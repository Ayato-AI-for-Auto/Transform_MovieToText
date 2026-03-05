import logging
import os
import threading
import time
import traceback

from src.recorder import AudioRecorder
from src.transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)

class LiveTranscriptionManager:
    """
    Orchestrates live loopback recording and background transcription.
    Handles the lifecycle of audio chunks.
    """
    def __init__(self, transcriber: WhisperTranscriber, model_name="base", force_gpu=False, on_text_added=None, source="system"):
        self.transcriber = transcriber
        self.model_name = model_name
        self.force_gpu = force_gpu
        self.on_text_added = on_text_added # Callback function(text)
        self.recorder = AudioRecorder(segment_time=30, source=source)
        
        self.processed_files = set()
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.full_transcript = ""
        
        # Statistics
        self.chunks_processed = 0
        self.total_errors = 0
        self.start_time = 0

    def start(self):
        """Starts both recording and the background processing thread."""
        self.full_transcript = ""
        self.processed_files.clear()
        self.stop_event.clear()
        self.chunks_processed = 0
        self.total_errors = 0
        self.start_time = time.time()
        
        self.recorder.clear_chunks()
        self.recorder.start()
        
        self.worker_thread = threading.Thread(target=self._process_chunks_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Live transcription manager started.")

    def stop(self):
        """Stops recording and waits for processing to finish."""
        self.recorder.stop()
        self.stop_event.set()
        
        if self.worker_thread:
            self.worker_thread.join(timeout=10)
        
        # Process any remaining chunks
        self._process_once()
        
        duration = time.time() - self.start_time
        logger.info(
            f"Live transcription stopped. "
            f"Summary: {self.chunks_processed} chunks processed, "
            f"{self.total_errors} errors, "
            f"Duration: {duration:.1f}s, "
            f"Total text length: {len(self.full_transcript)} chars"
        )
        return self.full_transcript

    def _process_chunks_loop(self):
        """Background thread loop that checks for new chunks."""
        while not self.stop_event.is_set():
            # Monitoring: Check if the recorder process is still alive
            if not self.recorder.is_process_alive() and self.recorder.is_recording:
                logger.error("Recording process (FFmpeg) died unexpectedly!")
                # We could trigger a stop or restart here, but for now we just log
            
            self._process_once()
            time.sleep(2) # Polling interval

    def _process_once(self):
        """Checks for new finished chunks and transcribes them."""
        chunks = self.recorder.get_recorded_chunks()
        if not chunks:
            return

        # AudioRecorder now writes chunks atomically (with .tmp rename)
        # We can safely process all available chunks immediately.
        for chunk_path in chunks:
            if chunk_path not in self.processed_files:
                self._handle_chunk(chunk_path)

    def _handle_chunk(self, path):
        """Transcribes a single chunk and deletes it."""
        try:
            logger.info(f"Processing chunk: {path.name}")
            text = self.transcriber.transcribe(str(path), model_name=self.model_name, force_gpu=self.force_gpu)
            
            if text:
                logger.info(f"Transcribed chunk {path.name}: {text[:50]}...")
                self.full_transcript += text + " "
                if self.on_text_added:
                    self.on_text_added(text)
            
            self.processed_files.add(path)
            self.chunks_processed += 1
            
            # Auto-cleanup with retries for Windows file locking
            self._safe_remove(path)
            
        except Exception:
            self.total_errors += 1
            logger.error(f"Error processing chunk {path}:\n{traceback.format_exc()}")

    def _safe_remove(self, path, retries=5, delay=1):
        """Attempts to remove a file with retries to handle Windows locking."""
        for i in range(retries):
            try:
                if path.exists():
                    os.remove(path)
                logger.debug(f"Deleted processed chunk: {path.name}")
                return
            except PermissionError:
                if i < retries - 1:
                    logger.debug(f"File locked, retrying deletion ({i+1}/{retries}): {path.name}")
                    time.sleep(delay)
                else:
                    logger.warning(f"Failed to delete {path.name} after {retries} retries (file locked).")
            except Exception as e:
                logger.warning(f"Unexpected error deleting {path.name}: {e}")
                break

