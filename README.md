# Transform Movie to Text

A simple Python application to transcribe video files into text using OpenAI's Whisper model.

## Features
- Select video files via a GUI.
- High-performance transcription using GPU (CUDA) support.
- Live text display and editing.
- Save transcripts to any arbitrary path.

## Requirements
- Python 3.10+
- FFmpeg (must be installed on the system and in PATH)

## Installation
```bash
uv venv .venv
# Activate venv
uv pip install -e .
uv pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121
```

## Usage
```bash
uv run src/main.py
```
