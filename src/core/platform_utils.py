import logging
import os
import sys

logger = logging.getLogger(__name__)


def is_android():
    """Returns True if running on Android."""
    # Specialization: Force False on Windows unless explicitly forced via env
    if sys.platform == "win32":
        return os.environ.get("FORCE_ANDROID_MODE") == "1"
    return sys.platform == "android"


def get_platform_name():
    if is_android():
        return "Android"
    return sys.platform


def get_app_data_path(app_name="MovieToText"):
    """Returns a safe path for storing app data depending on the platform."""
    if is_android():
        # Fallback for Android if still needed for some reason
        path = os.environ.get("FILESDIR") or os.path.expanduser("~")
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
