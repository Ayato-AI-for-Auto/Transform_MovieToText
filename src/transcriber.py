import os
import torch
import whisper


class WhisperTranscriber:
    """
    Backend class for Whisper transcription logic.
    Handles device selection, model loading, and transcription.
    """

    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self, model_name="base"):
        """Loads the Whisper model if not already loaded."""
        if self.model is None:
            self.model = whisper.load_model(model_name, device=self.device)
        return self.model

    def transcribe(self, path):
        """
        Transcribes the file at the given path.
        Assumes the model is already loaded.
        """
        if self.model is None:
            self.load_model()

        result = self.model.transcribe(path)
        return result.get("text", "").strip()
