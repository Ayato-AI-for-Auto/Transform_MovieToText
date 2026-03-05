import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.recorder import AudioRecorder, detect_microphone_device, detect_stereo_mix_device


class TestRecorder(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.recorder = AudioRecorder(output_dir=self.test_dir, segment_time=1, overlap=1)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('subprocess.Popen')
    def test_detect_stereo_mix_device(self, mock_popen):
        # Mock FFmpeg output for device list
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", (
            '[dshow @ 0000] "Stereo Mix (Realtek Audio)" (audio)\n'
            '[dshow @ 0000]   Alternative name "@device_cm_12345"\n'
        ))
        mock_popen.return_value = mock_process
        
        device_id = detect_stereo_mix_device()
        self.assertEqual(device_id, "@device_cm_12345")

    @patch('subprocess.Popen')
    def test_detect_microphone_device(self, mock_popen):
        # Mock FFmpeg output for device list
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", (
            '[dshow @ 0000] "Microphone (Realtek Audio)" (audio)\n'
            '[dshow @ 0000]   Alternative name "@device_cm_mic123"\n'
        ))
        mock_popen.return_value = mock_process
        
        device_id = detect_microphone_device()
        self.assertEqual(device_id, "@device_cm_mic123")

    @patch('src.recorder.detect_stereo_mix_device')
    @patch('subprocess.Popen')
    def test_recorder_start_stop(self, mock_popen, mock_detect):
        mock_detect.return_value = "@device_cm_12345"
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        self.recorder.start()
        self.assertTrue(self.recorder.is_recording)
        self.assertTrue(self.recorder.is_process_alive())
        
        self.recorder.stop()
        self.assertFalse(self.recorder.is_recording)

    def test_save_chunk_logic(self):
        # Manually fill chunks to simulate overlap
        # 16000 samples/sec * 1 channel * 2 bytes/sample = 32000 bytes/sec
        # segment=1, overlap=1 -> chunk_duration=2 -> max_buffer=64000
        
        data_1s = b'\x00' * 32000
        
        with self.recorder.buffer_lock:
            self.recorder.audio_chunks.append(data_1s)
            self.recorder.current_buffer_size = 32000
            
        self.recorder._save_chunk()
        
        # Should have saved chunk_000.wav (1s)
        chunks = self.recorder.get_recorded_chunks()
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].name, "chunk_000.wav")
        
        # Add another 1s
        with self.recorder.buffer_lock:
            self.recorder.audio_chunks.append(data_1s)
            self.recorder.current_buffer_size = 64000
            
        self.recorder._save_chunk()
        
        # Should have saved chunk_001.wav (2s total because of no eviction yet)
        chunks = self.recorder.get_recorded_chunks()
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[1].name, "chunk_001.wav")
        # Check size? 2s = 64000 bytes + wav header (~44 bytes)
        self.assertGreater(chunks[1].stat().st_size, 64000)

if __name__ == '__main__':
    unittest.main()
