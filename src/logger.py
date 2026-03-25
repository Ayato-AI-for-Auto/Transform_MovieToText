import datetime
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import colorlog


def setup_logger():
    """
    Sets up a robust rotating file logger and professional colorized terminal output.
    This should be called as early as possible.
    """
    log_file = "app.log"
    max_size = 10 * 1024 * 1024  # 10MB
    backup_count = 5

    # Check if DEBUG mode is enabled via environment variable
    debug_mode = os.environ.get("APP_DEBUG", "0") == "1"
    log_level = logging.DEBUG if debug_mode else logging.INFO

    try:
        # Standard format for file logging (No colors)
        log_format = "%(asctime)s [%(levelname)s] [%(threadName)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
        file_formatter = logging.Formatter(log_format)

        # File Handler (Rotating)
        file_handler = RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backup_count, encoding="utf-8")
        file_handler.setFormatter(file_formatter)

        # Stream Handler (Console) - Using colorlog for professional output
        stream_handler = logging.StreamHandler(sys.stdout)

        if sys.stdout.isatty():
            # Color configuration for professional terminal output
            color_formatter = colorlog.ColoredFormatter(
                "%(log_color)s" + log_format,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
                secondary_log_colors={},
                style="%",
            )
            stream_handler.setFormatter(color_formatter)
        else:
            stream_handler.setFormatter(file_formatter)

        # Root Logger setup
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Clean existing handlers to avoid duplicates during re-init
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"--- 🚀 APP START at {now} ---")
        logging.info("Professional logging initialized: colorlog library is now managing terminal output.")

    except Exception as e:
        # Fallback for lock contention or permission issues
        logging.basicConfig(level=logging.INFO)
        logging.warning(f"Could not initialize RotatingFileHandler: {e}. Falling back to basic logging.")


if __name__ == "__main__":
    setup_logger()
    logging.debug("This is a debug message (Cyan)")
    logging.info("This is an info message (Green)")
    logging.warning("This is a warning message (Yellow)")
    logging.error("This is an error message (Red)")
    logging.critical("This is a critical message (Bold Red)")
