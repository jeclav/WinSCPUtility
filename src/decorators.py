# src/decorators.py
import logging
import subprocess
from functools import wraps

def log_function_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.info(f"Calling function: {func.__name__} with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in function {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper

# Custom exception for device-related errors
class DeviceOperationError(Exception):
    pass

# General error handling decorator for device operations
def handle_operation_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"File not found during operation: {e}")
            raise DeviceOperationError(f"File not found during operation: {e}")
        except ValueError as e:
            logger.error(f"Invalid value provided: {e}")
            raise DeviceOperationError(f"Invalid value provided: {e}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running external command: {e}")
            raise DeviceOperationError(f"Error running external command: {e}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}", exc_info=True)
            raise DeviceOperationError(f"Unexpected error occurred: {e}")
    return wrapper
