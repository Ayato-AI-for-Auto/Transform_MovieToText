import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.live_processor import LiveTranscriptionManager


class TestLiveProcessor(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.mock_transcriber = MagicMock()
        self.manager = LiveTranscriptionManager(
            transcriber=self.mock_transcriber,
            on_text_added=MagicMock()
        )
        # Use the temp dir for the recorder output
        self.manager.recorder.output_dir = self.test_dir

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_process_once_detects_chunks(self):
        # Create a mock chunk file
        chunk_file = self.test_dir / "chunk_000.wav"
        chunk_file.write_bytes(b"dummy audio")
        
        self.mock_transcriber.transcribe.return_value = "Hello world"
        
        self.manager._process_once()
        
        # Verify transcription was called
        self.mock_transcriber.transcribe.assert_called_with(
            str(chunk_file), model_name="base", force_gpu=False
        )
        # Verify text was added to transcript
        self.assertIn("Hello world", self.manager.full_transcript)
        # Verify callback was called
        self.manager.on_text_added.assert_called_with("Hello world")
        # Verify chunk was added to processed files
        self.assertIn(chunk_file, self.manager.processed_files)
        # Verify chunk was deleted
        self.assertFalse(chunk_file.exists())

    @patch('os.remove')
    @patch('time.sleep', return_value=None)
    def test_safe_remove_retries(self, mock_sleep, mock_remove):
        # Simulate PermissionError then success
        mock_remove.side_effect = [PermissionError(), None]
        
        path = MagicMock()
        path.exists.return_value = True
        path.name = "chunk_000.wav"
        
        self.manager._safe_remove(path, retries=2, delay=0)
        
        # Should have called remove twice
        self.assertEqual(mock_remove.call_count, 2)
        # Should have called sleep once
        mock_sleep.assert_called_once()

if __name__ == '__main__':
    unittest.main()
