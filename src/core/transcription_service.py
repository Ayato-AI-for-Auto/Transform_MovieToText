import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import datetime

from src.config_manager import ConfigManager
from src.core.history_mgr import history_mgr
from src.live_processor import LiveTranscriptionManager
from src.llm.factory import LLMFactory
from src.recorder.visual_recorder import visual_recorder
from src.transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Handles business logic for transcription workflows.
    Decoupled from UI state.
    """

    def __init__(self, config_mgr: ConfigManager, transcriber: WhisperTranscriber):
        self.config_mgr = config_mgr
        self.transcriber = transcriber
        self.live_mgr: LiveTranscriptionManager | None = None
        self._live_start_time: float | None = None
        self._current_meeting_id: int | None = None
        self._current_mp3_path: str | None = None

    def transcribe_file_sync(
        self, file_path: str, model_name: str, language: str | None = None, progress_callback: Callable[[float], None] | None = None
    ) -> str:
        """Synchronously transcribes a file and saves it to history."""
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        force_gpu = self.config_mgr.get_force_gpu()
        self.transcriber.load_model(model_name, force_gpu=force_gpu)

        result = self.transcriber.transcribe(
            file_path, model_name=model_name, force_gpu=force_gpu, language=language, progress_callback=progress_callback
        )

        # Auto-save to history
        base_name = os.path.basename(file_path)

        # 1. Generate AI Title if possible
        ai_title = ""
        try:
            ai_title = self._generate_title_internal(result)
        except Exception as e:
            logger.warning(f"AI Title generation failed for file: {e}")

        final_title = f"{ai_title} ({base_name})" if ai_title else f"ファイル文字起こし: {base_name}"

        history_mgr.add_meeting(title=final_title, transcript=result, audio_path=file_path, model_info=model_name)
        return result

    def start_live_recording(
        self,
        model_name: str,
        source: str,
        language: str | None = None,
        project_name: str = "その他",
        category: str = "",
        on_text_added: Callable[[str], None] | None = None,
    ) -> int:
        """Starts a live recording session. Returns meeting_id."""
        force_gpu = self.config_mgr.get_force_gpu()
        self.transcriber.load_model(model_name, force_gpu=force_gpu)

        from src.core.utils import sanitize_filename

        safe_project = sanitize_filename(project_name or "その他")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_ui = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Create Placeholder
        meeting_id = history_mgr.add_meeting(
            title=f"会議録音 ({timestamp_ui})", transcript="", audio_path="", model_info=model_name, project_name=safe_project, category=category
        )
        self._current_meeting_id = meeting_id
        self._live_start_time = time.time()

        # 2. Setup audio path
        from src.core.constants import DEFAULT_RECORDS_DIR

        mp3_dir = os.path.join(os.getcwd(), DEFAULT_RECORDS_DIR, safe_project)
        os.makedirs(mp3_dir, exist_ok=True)
        mp3_path = os.path.join(mp3_dir, f"meeting_{timestamp}.mp3")
        self._current_mp3_path = mp3_path

        # 3. Start Recorders
        self.live_mgr = LiveTranscriptionManager(
            transcriber=self.transcriber,
            model_name=model_name,
            force_gpu=force_gpu,
            on_text_added=on_text_added,
            source=source,
            mp3_path=mp3_path,
            language=language,
        )
        self.live_mgr.start()

        # Visual Recorder
        if self.config_mgr.get_visual_capture_enabled():
            visual_recorder.start(meeting_id)

        return meeting_id

    def stop_live_recording(self, finalize_callback: Callable[[str, str], None] | None = None):
        """Stops live recording and finalizes results in background."""
        if not self.live_mgr:
            return

        visual_recorder.stop()

        def _finalize_worker():
            try:
                full_text = self.live_mgr.stop()
                meeting_id = self._current_meeting_id
                mp3_path = self._current_mp3_path
                duration = time.time() - (self._live_start_time or time.time())

                if duration >= 30 and full_text.strip():
                    # Auto-category and title extraction
                    category = ""
                    ai_title = ""
                    try:
                        category = self._extract_category_internal(full_text)
                    except Exception as e:
                        logger.warning(f"Category extraction failed: {e}")
                        category = "未分類"

                    try:
                        ai_title = self._generate_title_internal(full_text)
                    except Exception as e:
                        logger.warning(f"AI Title generation failed: {e}")

                    timestamp_ui = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    final_title = f"{ai_title} ({timestamp_ui})" if ai_title else f"会議録音 ({timestamp_ui})"

                    history_mgr.update_meeting(meeting_id, title=final_title, transcript=full_text, audio_path=mp3_path, category=category)
                else:
                    logger.info(f"Recording discarded (duration={duration:.1f}s)")
                    if meeting_id:
                        history_mgr.delete_meeting(meeting_id)

                if finalize_callback:
                    finalize_callback(full_text, category)

            except Exception as e:
                logger.error(f"Error finalizing live recording: {e}", exc_info=True)
            finally:
                self.live_mgr = None
                self._live_start_time = None
                self._current_meeting_id = None
                self._current_mp3_path = None

        threading.Thread(target=_finalize_worker, daemon=True).start()

    def _extract_category_internal(self, text: str) -> str:
        provider = self.config_mgr.get_active_provider()
        conf = self.config_mgr.get_provider_config(provider)
        llm_client = LLMFactory.create_client(provider, api_key=conf.get("api_key"), base_url=conf.get("base_url"))
        llm_model = self.config_mgr.get_last_model()
        return llm_client.extract_category(text, llm_model)

    def _generate_title_internal(self, text: str) -> str:
        if not text or len(text.strip()) < 50:
            return ""
        provider = self.config_mgr.get_active_provider()
        conf = self.config_mgr.get_provider_config(provider)
        llm_client = LLMFactory.create_client(provider, api_key=conf.get("api_key"), base_url=conf.get("base_url"))
        llm_model = self.config_mgr.get_last_model()
        return llm_client.generate_title(text, llm_model)
