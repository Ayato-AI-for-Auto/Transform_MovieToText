import datetime
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger():
    """
    Sets up a robust rotating file logger.
    This should be called as early as possible.
    """
    log_file = "app.log"
    max_size = 5 * 1024 * 1024  # 5MB
    backup_count = 5

    # Check if DEBUG mode is enabled via environment variable
    debug_mode = os.environ.get("APP_DEBUG", "0") == "1"
    log_level = logging.DEBUG if debug_mode else logging.INFO

    # Check if we can write to the directory
    try:
        # Create formatter
        # Added [%(threadName)s] for better debugging in multi-threaded environment
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(threadName)s] %(name)s: %(message)s"
        )

        # File Handler (Rotating)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_size, 
            backupCount=backup_count, 
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)

        # Stream Handler (Console)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # Root Logger setup
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Avoid duplicate handlers
        if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            root_logger.addHandler(file_handler)
        if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            root_logger.addHandler(stream_handler)
            
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"--- APP START at {now} ---")
        logging.info(f"Logger Initialized (Level: {logging.getLevelName(log_level)}, Handler: RotatingFileHandler)")
        
    except Exception as e:
        # Fallback for lock contention or permission issues
        logging.basicConfig(level=logging.INFO)
        logging.warning(f"Could not initialize RotatingFileHandler: {e}. Falling back to console logging.")

if __name__ == "__main__":
    setup_logger()
    logging.info("Logger test run.")
