# src/main.py
import os
import logging
import tkinter as tk
import threading
from typing import List, Dict
from dotenv import load_dotenv
from gui import WinSCPAutomationApp
from operations import download_logs, get_file_versions, nvram_demo_reset, nvram_reset
from logger_setup import setup_logger
from decorators import log_function_call
from tkinter import messagebox

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
    selected_devices: List[str],
    on_complete: callable = None,
    root: tk.Tk = None
) -> None:
    """
    Runs selected operations based on the user's choice in a separate thread.

    :param selected_operations: Dictionary containing the operations to run (True/False).
    :param download_path: The path where logs should be downloaded.
    :param selected_devices: List of devices selected for the operation.
    :param on_complete: Callback function to be called when operations are complete.
    :param root: The Tk root object, required to schedule on_complete in the main thread.
    :return: None
    """
    logger.info("Preparing to run selected operations")

    def execute_operations():
        logger.info("Running selected operations")
        mnt_log_path = os.getenv('MNT_LOG_PATH', '/mnt/log')
        tmp_log_path = os.getenv('TMP_LOG_PATH', '/tmp/logs')
        nvram_path = os.getenv('NVRAM_PATH', '/mnt/nvram')

        try:
            if selected_operations.get('download_logs', False):
                logger.info("Running download logs operation")
                download_logs(selected_devices, download_path)

            if selected_operations.get('nvram_demo_reset', False):
                logger.info("Running NVRAM demo reset operation")
                nvram_demo_reset(nvram_path, selected_devices)

            if selected_operations.get('nvram_reset', False):
                logger.info("Running NVRAM reset operation")
                nvram_reset(nvram_path, selected_devices)

            if selected_operations.get('get_file_versions', False):
                logger.info("Running get device file versions operation")
                file_versions = get_file_versions(selected_devices)
                # Optionally, display file versions to the user
                if root:
                    def show_versions():
                        version_info = ""
                        for device, versions in file_versions.items():
                            version_info += f"{device}:\n" + "\n".join(versions) + "\n\n"
                        messagebox.showinfo("File Versions", version_info)
                    root.after(0, show_versions)
        except Exception as e:
            logger.error(f"Error during operations: {e}", exc_info=True)
            # Schedule a function to show an error message to the user
            if on_complete and root:
                def show_error():
                    messagebox.showerror("Error", f"An error occurred during operations:\n{e}")
                    on_complete()
                root.after(0, show_error)
            return

        # When done, call on_complete in the main thread
        if on_complete and root:
            root.after(0, on_complete)

    operation_thread = threading.Thread(
        target=execute_operations
    )
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
