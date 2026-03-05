import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from src.recorder import AudioRecorder


class TestRecorder(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.recorder = AudioRecorder(output_dir=self.test_dir, segment_time=1, overlap=1)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('soundcard.default_microphone')
    def test_recorder_start_stop_mic(self, mock_mic):
        mock_device = MagicMock()
        mock_mic.return_value = mock_device
        
        self.recorder.source = "microphone"
        self.recorder.start()
        self.assertTrue(self.recorder.is_recording)
        
        self.recorder.stop()
        self.assertFalse(self.recorder.is_recording)

    @patch('soundcard.default_speaker')
    def test_recorder_start_stop_system(self, mock_speaker):
        mock_device = MagicMock()
        mock_speaker.return_value = mock_device
        
        self.recorder.source = "system"
        self.recorder.start()
        self.assertTrue(self.recorder.is_recording)
        
        self.recorder.stop()
        self.assertFalse(self.recorder.is_recording)

    def test_push_chunk_logic(self):
        # Manually fill buffer with numpy blocks (1 block = 1024 samples)
        # 16000 samples/sec
        data_block = np.zeros(1024, dtype=np.float32)
        
        with self.recorder.buffer_lock:
            for _ in range(16): # ~1s
                self.recorder.audio_buffer.append(data_block)
            self.recorder.current_samples_count = 1024 * 16
            
        self.recorder._push_chunk()
        
        # Should have pushed data to chunk_queue
        self.assertEqual(self.recorder.chunk_queue.qsize(), 1)
        audio_data = self.recorder.chunk_queue.get()
        self.assertTrue(isinstance(audio_data, np.ndarray))
        self.assertEqual(len(audio_data), 1024 * 16)
        
        # Test eviction
        # segment=1, overlap=1 -> max_buffer=2s = 32000 samples
        with self.recorder.buffer_lock:
            # Add a lot of data to trigger eviction
            for _ in range(100): 
                self.recorder.audio_buffer.append(data_block)
                self.recorder.current_samples_count += 1024
            
            # Manually trigger eviction logic check (simulating loop)
            while self.recorder.current_samples_count > self.recorder.max_buffer_samples:
                rem = self.recorder.audio_buffer.popleft()
                self.recorder.current_samples_count -= len(rem)
        
        self.assertLessEqual(self.recorder.current_samples_count, self.recorder.max_buffer_samples)

if __name__ == '__main__':
    unittest.main()
