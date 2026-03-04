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
### Using Source Code
```bash
uv run main.py
# Or use the batch file (Windows)
run.bat
```

### Using Executable (.exe)
You can download the pre-built executables from the GitHub Releases/Actions page:
- **GPU version**: For PCs with NVIDIA GPUs (Fast transcription).
- **CPU version**: For any PC (Small size, works everywhere).

## Building from Source
To create your own standalone executable:
```bash
python scripts/build_exe.py
```
This script will automatically detect your GPU and ask which version of Torch to install before building.
