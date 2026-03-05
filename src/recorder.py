import logging
import os
import re
import subprocess
import threading
import time
import wave
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_stereo_mix_device():
    """Auto-detect the Stereo Mix device ID from FFmpeg's DirectShow listing.
    
    Searches for devices matching common Stereo Mix names across locales:
    - English: "Stereo Mix"
    - Japanese: "ステレオ ミキサー"
    
    Returns the device ID string (e.g. "@device_cm_...") or None if not found.
    """
    cmd = ["ffmpeg", "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        _, stderr = proc.communicate(timeout=10)
    except Exception as e:
        logger.warning(f"Failed to probe DirectShow devices: {e}")
        return None

    # Parse stderr line by line.
    # Device entries look like:
    #   [dshow @ ...] "Device Name" (audio)
    #   [dshow @ ...]   Alternative name "@device_cm_..."
    stereo_mix_keywords = ["stereo mix", "ステレオ ミキサー"]
    lines = stderr.splitlines()
    found_stereo_mix = False

    for line in lines:
        # Check if this line declares an audio device matching Stereo Mix
        if "(audio)" in line:
            name_lower = line.lower()
            if any(kw in name_lower for kw in stereo_mix_keywords):
                found_stereo_mix = True
                logger.info(f"Stereo Mix device found: {line.strip()}")
                continue

        # The very next "Alternative name" line after finding Stereo Mix has the ID
        if found_stereo_mix and "Alternative name" in line:
            match = re.search(r'"(@device_cm_[^"]+)"', line)
            if match:
                device_id = match.group(1)
                logger.info(f"Stereo Mix device ID: {device_id}")
                return device_id
            found_stereo_mix = False  # Reset if pattern didn't match

    logger.warning("Stereo Mix device not found. Please enable it in Windows Sound settings.")
    return None


def detect_microphone_device():
    """Auto-detect the default microphone device ID from FFmpeg's DirectShow listing.
    
    Returns the device ID string (e.g. "@device_cm_...") or None if not found.
    """
    cmd = ["ffmpeg", "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"]
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        _, stderr = proc.communicate(timeout=10)
    except Exception as e:
        logger.warning(f"Failed to probe DirectShow devices: {e}")
        return None

    # Parse stderr line by line.
    lines = stderr.splitlines()
    found_mic = False

    for line in lines:
        # Check for audio devices. We prioritize entries that look like "Microphone"
        # but will pick the first official audio input if no "Microphone" is found.
        if "(audio)" in line:
            name_lower = line.lower()
            # On Windows, microphones are usually named "Microphone" (English) or "マイク" (Japanese)
            if "microphone" in name_lower or "マイク" in name_lower:
                found_mic = True
                logger.info(f"Microphone device found: {line.strip()}")
                continue
            
            # Fallback: if we haven't found a "Microphone" yet, any audio device could be it
            # But FFmpeg's -list_devices lists ALL dshow audio devices, including Stereo Mix.
            # So we MUST be careful not to pick Stereo Mix as the "Microphone".
            if "stereo mix" not in name_lower and "ステレオ ミキサー" not in name_lower:
                if not found_mic: # Only if we haven't found a better match
                    found_mic = True
                    logger.info(f"Generic audio input found (fallback for mic): {line.strip()}")
                    continue

        if found_mic and "Alternative name" in line:
            match = re.search(r'"(@device_cm_[^"]+)"', line)
            if match:
                device_id = match.group(1)
                logger.info(f"Microphone device ID: {device_id}")
                return device_id
            found_mic = False

    logger.warning("Microphone device not found via DirectShow.")
    return None



class AudioRecorder:
    """
    Handles system audio loopback recording using FFmpeg.
    Reads continuous PCM stream and slices into overlapping chunks.
    """
    def __init__(self, output_dir="temp_chunks", segment_time=30, overlap=5, source="system"):
        self.output_dir = Path(output_dir)
        self.segment_time = segment_time
        self.overlap = max(0, overlap)
        self.source = source # "system" or "microphone"
        self.process = None
        self.is_recording = False
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stderr_thread = None
        self.stdout_thread = None
        
        # Audio stream settings (Whisper native)
        self.sample_rate = 16000
        self.channels = 1
        self.bytes_per_sample = 2
        self.bytes_per_sec = self.sample_rate * self.channels * self.bytes_per_sample
        
        # Buffer to hold the recent audio
        self.chunk_duration = self.segment_time + self.overlap
        self.max_buffer_bytes = self.chunk_duration * self.bytes_per_sec
        self.audio_chunks = deque()
        self.current_buffer_size = 0
        self.buffer_lock = threading.Lock()
        
        self.chunk_index = 0
        self.last_save_time = 0
        
        logger.debug(f"AudioRecorder initialized: output_dir={self.output_dir}, segment_time={self.segment_time}, overlap={self.overlap}")

    def start(self):
        """Starts the FFmpeg loopback recording process."""
        if self.is_recording:
            return

        if self.source == "microphone":
            device_id = detect_microphone_device()
            source_name = "Microphone"
        else:
            device_id = detect_stereo_mix_device()
            source_name = "Stereo Mix"

        if not device_id:
            if self.source == "microphone":
                msg = "マイクが見つかりません。デバイスの接続を確認してください。"
            else:
                msg = ("Stereo Mix デバイスが見つかりません。\n"
                       "Windowsのサウンド設定で「ステレオ ミキサー」を有効にしてください。")
            raise RuntimeError(msg)

        # Stream raw 16-bit PCM to stdout
        cmd = [
            "ffmpeg",
            "-hide_banner", "-loglevel", "error",
            "-y",
            "-f", "dshow",
            "-i", f"audio={device_id}", 
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ar", str(self.sample_rate),
            "-ac", str(self.channels),
            "pipe:1"
        ]

        self.audio_chunks.clear()
        self.current_buffer_size = 0
        self.chunk_index = 0
        self.last_save_time = time.time()

        try:
            logger.info(f"Starting {source_name} recording on device: {device_id}")
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.is_recording = True
            
            # Start threads to read pipes
            self.stderr_thread = threading.Thread(
                target=self._read_stderr, 
                args=(self.process.stderr,), 
                name="FFmpegStderrReader",
                daemon=True
            )
            self.stderr_thread.start()
            
            self.stdout_thread = threading.Thread(
                target=self._read_stdout,
                name="FFmpegStdoutReader",
                daemon=True
            )
            self.stdout_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start FFmpeg recording: {e}", exc_info=True)
            self.is_recording = False
            raise

    def _read_stderr(self, pipe):
        """Reads FFmpeg stderr and logs it."""
        try:
            for line_bytes in pipe:
                line = line_bytes.decode('utf-8', errors='replace').strip()
                if line:
                    if "Error" in line or "fail" in line.lower():
                        logger.error(f"[FFmpeg] {line}")
                    else:
                        logger.debug(f"[FFmpeg] {line}")
        except Exception as e:
            logger.debug(f"Stderr reader thread closed: {e}")

    def _read_stdout(self):
        """Reads PCM audio stream and saves chunks periodically."""
        read_size = 8192
        try:
            while self.is_recording and self.process and self.process.stdout:
                data = self.process.stdout.read(read_size)
                if not data:
                    break
                
                with self.buffer_lock:
                    self.audio_chunks.append(data)
                    self.current_buffer_size += len(data)
                    
                    # Evict old data to maintain max window size
                    while self.current_buffer_size > self.max_buffer_bytes and self.audio_chunks:
                        removed = self.audio_chunks.popleft()
                        self.current_buffer_size -= len(removed)
                
                # Check if it's time to save a standard segment
                current_time = time.time()
                if current_time - self.last_save_time >= self.segment_time:
                    self._save_chunk()
                    self.last_save_time = current_time
                    
        except Exception as e:
            logger.error(f"Error reading FFmpeg stdout: {e}", exc_info=True)
        finally:
            # Save any remaining audio when stopping
            if self.current_buffer_size > 0:
                self._save_chunk()

    def _save_chunk(self):
        """Saves the current audio buffer atomically to a WAV file."""
        with self.buffer_lock:
            # We don't pop, we just read (so the data remains for overlap in the next chunk)
            audio_data = b"".join(self.audio_chunks)
            
        if len(audio_data) == 0:
            return
            
        chunk_name = f"chunk_{self.chunk_index:03d}.wav"
        chunk_path = self.output_dir / chunk_name
        tmp_path = chunk_path.with_suffix(".tmp")
        
        try:
            with wave.open(str(tmp_path), "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.bytes_per_sample)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            
            # Atomic rename ensures processor script only sees complete files
            tmp_path.rename(chunk_path)
            self.chunk_index += 1
            logger.debug(f"Saved {chunk_name} ({len(audio_data)/1024:.1f} KB)")
        except Exception as e:
            logger.error(f"Failed to save {chunk_name}: {e}")
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    def is_process_alive(self):
        """Checks if the FFmpeg process is still running."""
        if self.process and self.process.poll() is None:
            return True
        return False

    def stop(self):
        """Stops the recording process and cleans up."""
        if not self.is_recording:
            return

        logger.info("Stopping loopback recording...")
        self.is_recording = False
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            
        if self.stdout_thread:
            self.stdout_thread.join(timeout=2)
            
    def get_recorded_chunks(self):
        """Returns a list of wav files in the output directory, sorted by name."""
        return sorted(list(self.output_dir.glob("chunk_*.wav")))

    def clear_chunks(self):
        """Deletes all temporary chunks and files in the output directory."""
        for f in self.output_dir.glob("chunk_*.*"):
            try:
                f.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete chunk {f}: {e}")
