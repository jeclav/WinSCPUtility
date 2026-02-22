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
from config_manager import config_manager

# Ensure environment variables are loaded
load_dotenv()

# Set up the root logger
log_path = config_manager.get('paths.log_path')
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
    custom_name: str,
    on_complete: Callable = None,
    root: tk.Tk = None,
) -> None:
    """
    Runs selected operations based on the user's choice in a separate thread.
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
        nvram_path = config_manager.get('paths.nvram_path')

        # Sort operations based on their defined order
        selected_ops = [op for op, selected in selected_operations.items() if selected]
        ordered_ops = sorted(selected_ops, key=lambda op: OPERATION_RULES[op]['order'])

        try:
            for op in ordered_ops:
                # Before starting each operation, prompt the user
                operation_name = op.replace('_', ' ').title()

                # Use an event to wait for the user's decision
                proceed_event = threading.Event()

                def prompt_user():
                    result = messagebox.askyesno(
                        "Next Operation",
                        f"The next operation is '{operation_name}'.\nDo you want to continue?"
                    )
                    if result:
                        proceed_event.set()
                    else:
                        # User chose to abort
                        if on_complete:
                            on_complete()
                        proceed_event.set()
                        return

                # Show the prompt in the main thread
                root.after(0, prompt_user)

                # Wait until the user makes a decision
                proceed_event.wait()

                if not proceed_event.is_set():
                    # User aborted
                    logger.info(f"Operation '{operation_name}' was aborted by the user.")
                    return

                logger.info(f"Starting operation '{operation_name}'")

                # Execute the operation on all selected devices
                if op == 'compare_file_versions':
                    compare_file_versions(selected_devices, master_payload_folder)
                elif op == 'download_logs':
                    download_logs(selected_devices, download_path, custom_name)
                elif op == 'update_file_versions':
                    update_file_versions(selected_devices, master_payload_folder)
                elif op == 'nvram_reset':
                    nvram_reset(nvram_path, selected_devices)
                elif op == 'nvram_demo_reset':
                    nvram_demo_reset(nvram_path, selected_devices)

            # All operations completed
            if on_complete and root:
                root.after(0, on_complete)

        except Exception as e:
            logger.error(f"Error during operations: {e}", exc_info=True)
            if on_complete and root:
                def show_error(e=e):
                    messagebox.showerror("Error", f"An error occurred during operations:\n{e}")
                    on_complete()
                root.after(0, show_error)
            return

    operation_thread = threading.Thread(target=execute_operations)
    operation_thread.start()


@log_function_call
def main() -> None:
    """
    Main function to initialize the GUI and run the application.
    """
    root = tk.Tk()
    window_title = config_manager.get('ui.window_title')
    window_size = config_manager.get('ui.window_size')
    
    root.title(window_title)
    root.geometry(window_size)
    
    app = WinSCPAutomationApp(root, run_operations)
    root.mainloop()


if __name__ == "__main__":
    logger.info("Starting the WinSCP Automation Tool")
    main()