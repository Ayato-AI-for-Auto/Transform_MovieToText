import logging
import os
import sys

logger = logging.getLogger(__name__)


def is_android():
    """Returns True if running on Android."""
    return sys.platform == "android" or "ANDROID_ARGUMENT" in os.environ


def get_platform_name():
    if is_android():
        return "Android"
    return sys.platform


def get_app_data_path(app_name="MovieToText"):
    """Returns a safe path for storing app data depending on the platform."""
    if is_android():
        # On Android, we try to use the most stable app-specific directory.
        # Flet sometimes sets ANDROID_DATA or similar.
        path = os.environ.get("FILESDIR") or "/data/data/com.example.movietotext/files"
        if not os.path.exists(path):
            try:
                # Fallback to home if filesdir is not set/exists
                path = os.path.expanduser("~")
            except Exception:
                pass
        
        final_path = os.path.join(path, app_name)
        os.makedirs(final_path, exist_ok=True)
        return final_path

    # Windows/others
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, app_name)
    os.makedirs(path, exist_ok=True)
    return path


def get_log_path():
    """Returns the absolute path to the app's debug log file."""
    base_path = get_app_data_path()
    log_dir = os.path.join(base_path, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "app_debug.log")
