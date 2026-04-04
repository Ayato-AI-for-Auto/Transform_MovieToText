# Compatibility shim for src.recorder
from src.pc.recorder.audio_recorder import AudioRecorder
from src.pc.recorder.base import _BaseRecorder
from src.pc.recorder.factory import create_recorder
from src.pc.recorder.ffmpeg import FFmpegRecorder

__all__ = ["_BaseRecorder", "FFmpegRecorder", "AudioRecorder", "create_recorder"]
