# src/logger_setup.py
import logging
import os

# ANSI escape codes for colored output
RESET = "\x1b[0m"
COLORS = {
    'DEBUG': "\x1b[1;34m",    # Blue
    'INFO': "\x1b[32m",     # Green
    'WARNING': "\x1b[33m",  # Yellow
    'ERROR': "\x1b[31m",    # Red
    'CRITICAL': "\x1b[41m", # Red background
}

class ColorFormatter(logging.Formatter):
    def format(self, record):
        log_color = COLORS.get(record.levelname, RESET)
        log_msg = super().format(record)
        return f"{log_color}{log_msg}{RESET}"

def setup_logger(log_file=None, log_level=logging.DEBUG):
    """Set up a logger with colorized output and optional file logging."""
    logger = logging.getLogger()
    if not logger.hasHandlers():
        logger.setLevel(log_level)

        # Console handler with color output
        console_handler = logging.StreamHandler()
        console_formatter = ColorFormatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Optional file handler (if log_file is provided)
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(os.path.normpath(log_file))
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  # No color in file
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            