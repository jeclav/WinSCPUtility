# src/main.py

import os
import logging
import tkinter as tk
import threading
from typing import List, Dict, Callable
from dotenv import load_dotenv
from gui import WinSCPAutomationApp
from operations import (
    download_logs,
    compare_file_versions,
    update_file_versions,
    nvram_demo_reset,
    nvram_reset,
)
from logger_setup import setup_logger
from decorators import log_function_call
from tkinter import messagebox
from validation import validate_operations, OPERATION_RULES

# Ensure environment variables are loaded
load_dotenv()

# Set up the root logger
log_path = os.getenv('LOG_PATH', 'logs/debug.log')
setup_logger(log_file=log_path)

logger = logging.getLogger(__name__)

logger.debug('Application started')
logger.info('Loading GUI components')


@log_function_call
def run_operations(
    selected_operations: Dict[str, bool],
    download_path: str,
    master_payload_folder: str,
    selected_devices: List[str],
    on_complete: Callable = None,
    root: tk.Tk = None,
) -> None:
    """
    Runs selected operations based on the user's choice in a separate thread.

    :param selected_operations: Dictionary containing the operations to run (True/False).
    :param download_path: The path where logs should be downloaded.
    :param master_payload_folder: The path to the master payload folder for .iso file comparison.
    :param selected_devices: List of devices selected for the operation.
    :param on_complete: Callback function to be called when operations are complete.
    :param root: The Tk root object, required to schedule on_complete in the main thread.
    :return: None
    """
    logger.info("Preparing to run selected operations")

    # Validate the selected operations
    try:
        validate_operations(selected_operations)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        if on_complete and root:
            def show_error(e=e):
                messagebox.showerror("Validation Error", str(e))
                on_complete()
            root.after(0, show_error)
        return

    def execute_operations():
        logger.info("Running selected operations")
        nvram_path = os.getenv('NVRAM_PATH', '/mnt/nvram')

        # Sort operations based on their defined order
        selected_ops = [op for op, selected in selected_operations.items() if selected]
        ordered_ops = sorted(selected_ops, key=lambda op: OPERATION_RULES[op]['order'])

        try:
            for op in ordered_ops:
                if op == 'compare_file_versions':
                    logger.info("Running compare file versions operation")
                    compare_file_versions(selected_devices, master_payload_folder)
                elif op == 'download_logs':
                    logger.info("Running download logs operation")
                    download_logs(selected_devices, download_path)
                elif op == 'update_file_versions':
                    logger.info("Running update file versions operation")
                    update_file_versions(selected_devices, master_payload_folder)
                elif op == 'nvram_reset':
                    logger.info("Running NVRAM reset operation")
                    nvram_reset(nvram_path, selected_devices)
                elif op == 'nvram_demo_reset':
                    logger.info("Running NVRAM demo reset operation")
                    nvram_demo_reset(nvram_path, selected_devices)
        except Exception as e:
            logger.error(f"Error during operations: {e}", exc_info=True)
            if on_complete and root:
                def show_error(e=e):
                    messagebox.showerror("Error", f"An error occurred during operations:\n{e}")
                    on_complete()
                root.after(0, show_error)
            return

        if on_complete and root:
            root.after(0, on_complete)

    operation_thread = threading.Thread(target=execute_operations)
    operation_thread.start()


@log_function_call
def main() -> None:
    """
    Main function to initialize the GUI and run the application.

    :return: None
    """
    root = tk.Tk()
    app = WinSCPAutomationApp(root, run_operations)
    root.mainloop()


if __name__ == "__main__":
    logger.info("Starting the WinSCP Automation Tool")
    main()
