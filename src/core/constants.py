import os
from enum import Enum

from .platform_utils import get_app_data_path

# Root App Data
APP_DATA_DIR = get_app_data_path()

# Paths
DEFAULT_DB_PATH = os.path.join(APP_DATA_DIR, "history.db")
DEFAULT_CONFIG_PATH = os.path.join(APP_DATA_DIR, "config.json")
DEFAULT_RECORDS_DIR = os.path.join(APP_DATA_DIR, "history")
TEMP_DIR = os.path.join(APP_DATA_DIR, "temp")
TEMP_CHUNKS_DIR = os.path.join(APP_DATA_DIR, "temp", "chunks")
TEMP_VIDEO_DIR = os.path.join(APP_DATA_DIR, "temp", "frames")

# Recording Defaults
DEFAULT_SEGMENT_TIME = 30
DEFAULT_OVERLAP = 5
DEFAULT_SAMPLE_RATE = 16000

# Provider Defaults (Restricted to Local Privacy-First execution)
DEFAULT_PROVIDERS = {
    "ollama_local": {"api_key": "", "base_url": "http://localhost:11434"},
}
DEFAULT_ACTIVE_PROVIDER = "ollama_local"
DEFAULT_LLM_MODELS = {
    "ollama_local": ["gemma3:1b", "gemma3:4b", "gemma3:12b", "llama3.2", "mistral-nemo", "phi4"],
}

DEFAULT_WHISPER_MODEL = "base"
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]

# Embedding Defaults (Privacy-First: FastEmbed is the non-negotiable default)
DEFAULT_EMBEDDING_PROVIDER = "local"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
