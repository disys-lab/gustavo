import logging
import colorlog

def setup_logging(level=logging.INFO):
    """
    Configures colored logging for the application using `colorlog`.

    Purpose:
    - Set up a standardized, color-coded logging format for better readability in the terminal
    - Ensure only one active handler is attached to the root logger to prevent duplicate logs

    Args:
        level (int, optional): Logging level (default is `logging.INFO`). 
            Common values include:
            - `logging.DEBUG`: Detailed debug output
            - `logging.INFO`: General info messages
            - `logging.WARNING`: Warning conditions
            - `logging.ERROR`: Error messages
            - `logging.CRITICAL`: Critical failure messages

    Logic:
    - Uses `colorlog.ColoredFormatter` to define colored log output based on severity level
    - Clears any existing handlers from the root logger to prevent duplicate outputs
    - Attaches a new `StreamHandler` with the colored formatter to the logger

    Log Color Mapping:
        - DEBUG → Cyan
        - INFO → Green
        - WARNING → Yellow
        - ERROR → Red
        - CRITICAL → Bold Red

    Returns:
        None
    """
    # Create a colored formatter
    log_format = "%(log_color)s%(asctime)s - %(levelname)s - %(message)s"
    formatter = colorlog.ColoredFormatter(
        log_format,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }
    )

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove any existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a console handler and set the formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)
setup_logging()