import logging
import os
import subprocess
import time

import psutil
import torch
import whisper

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Backend class for Whisper transcription logic.
    Handles hardware detection, model loading, and transcription.
    """

    # Relaxed Model requirements in GB (approximate VRAM/RAM for FP16)
    # Lowered slightly to be more inclusive for cards like RTX 3050 (4GB)
    MODEL_REQUIREMENTS = {
        "tiny": 0.5,
        "base": 0.5,
        "small": 1.2,
        "medium": 3.5,
        "large-v3": 8.0,
        "turbo": 5.0,
    }

    def __init__(self):
        self.model = None
        self.current_model_name = None
        self._hardware_info = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.last_warning = ""
        logger.info(f"Initialized WhisperTranscriber on device: {self.device}")

    @staticmethod
    def _detect_vram_nvidia_smi():
        """Detects VRAM using nvidia-smi (driver-level, independent of PyTorch)."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                vram_mb = float(result.stdout.strip().split("\n")[0])
                return round(vram_mb / 1024, 1)
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        return 0.0

    def get_hardware_info(self):
        """Returns detected VRAM (via nvidia-smi) and total RAM in GB. Cached."""
        if self._hardware_info is not None:
            return self._hardware_info

        info = {"vram": 0.0, "ram": 0.0}

        # RAM detection
        ram_bytes = psutil.virtual_memory().total
        info["ram"] = round(ram_bytes / (1024**3), 1)

        # VRAM detection (nvidia-smi first, torch.cuda as fallback)
        info["vram"] = self._detect_vram_nvidia_smi()
        if info["vram"] == 0.0 and torch.cuda.is_available():
            vram_bytes = torch.cuda.get_device_properties(0).total_memory
            info["vram"] = round(vram_bytes / (1024**3), 1)

        logger.info(f"Hardware detected - RAM: {info['ram']}GB, VRAM: {info['vram']}GB")
        self._hardware_info = info
        return info

    def get_model_device(self, model_name, force_gpu=False):
        """Determines the best device (cuda or cpu) for a specific model."""
        self.last_warning = ""
        
        if not torch.cuda.is_available():
            return "cpu"

        if force_gpu:
            logger.info(f"GPU usage FORCED for model {model_name}.")
            return "cuda"

        req = self.MODEL_REQUIREMENTS.get(model_name, 1.0)
        vram = self.get_hardware_info()["vram"]
        
        if vram >= req:
            return "cuda"
        else:
            reason = f"VRAM不足 (必要: {req}GB / 使用可能: {vram}GB)。安全のためCPUに切り替えました。"
            self.last_warning = reason
            logger.warning(f"GPU safety triggered: {reason}")
            return "cpu"

    def can_run_on_gpu(self, model_name):
        """Checks if the GPU has enough VRAM for this model (independent of PyTorch CUDA)."""
        req = self.MODEL_REQUIREMENTS.get(model_name, 1.0)
        vram = self.get_hardware_info()["vram"]
        return vram >= req

    def load_model(self, model_name="base", force_gpu=False):
        """Loads or reloads the Whisper model on the appropriate device."""
        device = self.get_model_device(model_name, force_gpu=force_gpu)

        if self.model is None or self.current_model_name != model_name or self.model.device.type != device:
            logger.info(f"Loading Whisper model: {model_name} on {device}...")
            self.model = whisper.load_model(model_name, device=device)
            self.current_model_name = model_name
            # Verify actual device of the loaded model
            actual_device = next(self.model.parameters()).device
            logger.info(f"Model {model_name} loaded successfully on {actual_device}.")
        return self.model

    def transcribe(self, path, model_name="base", force_gpu=False):
        """
        Transcribes the file at the given path.
        Ensures the correct model is loaded.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Transcription file not found: {path}")
        
        file_size = os.path.getsize(path)
        if file_size == 0:
            raise ValueError(f"Transcription file is empty (0 bytes): {path}")

        self.load_model(model_name, force_gpu=force_gpu)

        logger.info(f"Starting transcription for: {path} (Size: {file_size/1024:.1f} KB, Device: {next(self.model.parameters()).device})")
        start_time = time.time()
        
        try:
            result = self.model.transcribe(path)
            duration = time.time() - start_time
            logger.info(f"Transcription completed in {duration:.2f}s for {path}")
            return result.get("text", "").strip()
        except Exception as e:
            logger.error(f"Error during whisper transcription: {e}", exc_info=True)
            raise
