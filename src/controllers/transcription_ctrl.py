import logging
import threading

from src.config_manager import ConfigManager
from src.core.state import state
from src.live_processor import LiveTranscriptionManager
from src.transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)

class TranscriptionController:
    def __init__(self, config_mgr: ConfigManager, transcriber: WhisperTranscriber):
        self.config_mgr = config_mgr
        self.transcriber = transcriber
        self.live_mgr = None

    def start_file_transcription(self, file_path: str, model_name: str):
        if not file_path:
            return
        
        state.set("is_processing", True)
        state.set("status_text", "文字起こし中... (初回モデルDL時は時間がかかります)")
        state.set("progress_visible", True)

        def _worker():
            try:
                force_gpu = self.config_mgr.get_force_gpu()
                self.transcriber.load_model(model_name, force_gpu=force_gpu)
                
                if self.transcriber.last_warning:
                    state.set("gpu_warning", f"⚠️ {self.transcriber.last_warning}")
                else:
                    state.set("gpu_warning", "")
                
                result = self.transcriber.transcribe(file_path, model_name=model_name, force_gpu=force_gpu)
                state.set("transcript_text", result)
                state.set("status_text", "文字起こし完了")
            except Exception as e:
                logger.error(f"Transcription error: {e}", exc_info=True)
                state.set("status_text", f"エラー: {e}")
            finally:
                state.set("is_processing", False)
                state.set("progress_visible", False)

        threading.Thread(target=_worker, daemon=True).start()

    def toggle_live_recording(self, model_name: str, source: str):
        if state.get("is_recording"):
            self.stop_live_recording()
        else:
            self.start_live_recording(model_name, source)

    def start_live_recording(self, model_name: str, source: str):
        state.set("is_recording", True)
        source_label = "システム音" if source == "system" else "マイク"
        state.set("status_text", f"{source_label}をリアルタイム録音・文字起こし中...")
        state.set("transcript_text", "")

        force_gpu = self.config_mgr.get_force_gpu()
        
        try:
            self.transcriber.load_model(model_name, force_gpu=force_gpu)
            if self.transcriber.last_warning:
                state.set("gpu_warning", f"⚠️ {self.transcriber.last_warning}")
            else:
                state.set("gpu_warning", "")
            
            self.live_mgr = LiveTranscriptionManager(
                transcriber=self.transcriber,
                model_name=model_name,
                force_gpu=force_gpu,
                on_text_added=self._on_live_text_added,
                source=source
            )
            self.live_mgr.start()
        except Exception as e:
            logger.error(f"Live recording start error: {e}")
            state.set("status_text", f"エラー: {e}")
            state.set("is_recording", False)

    def stop_live_recording(self):
        if not self.live_mgr:
            return

        state.set("status_text", "録音を終了し、最後のチャンクを処理中...")
        state.set("is_recording", False) # UI should reflect stopping phase

        def _stop_worker():
            full_text = self.live_mgr.stop()
            state.set("transcript_text", full_text)
            state.set("status_text", "ライブ文字起こし完了")
            self.live_mgr = None

        threading.Thread(target=_stop_worker, daemon=True).start()

    def _on_live_text_added(self, text):
        current_text = state.get("transcript_text", "")
        # Very simple append logic
        state.set("transcript_text", current_text + text + " ")
