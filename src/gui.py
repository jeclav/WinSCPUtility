# src/gui.py

import configparser
import os
import tkinter as tk
from tkinter import filedialog, messagebox, BooleanVar
import logging
from tkinter import ttk  # For the progress bar
from typing import List
from decorators import log_function_call
from validation import validate_operations  # Import the validation function

logger = logging.getLogger(__name__)

logger.info('Initializing GUI')
logger.debug('Setting up buttons and event handlers')


class WinSCPAutomationApp:
    def __init__(self, root: tk.Tk, operations_callback: callable) -> None:
        logger.debug("Initializing WinSCPAutomationApp")
        self.root = root
        self.root.title("WinSCP Automation Tool")
        self.root.geometry("500x700")

        self.operations_callback = operations_callback

        self.config_file = os.path.normpath(os.getenv('CONFIG_FILE', 'devices.ini'))
        logger.info(f"Config file path: {self.config_file}")

        self.download_path = self.load_saved_setting("download_path", 'C:\\DownloadedLogs')
        self.master_payload_folder = self.load_saved_setting("master_payload_folder", 'C:\\MasterPayload')
        logger.info(f"Initial download path: {self.download_path}")
        logger.info(f"Initial master payload folder: {self.master_payload_folder}")

        # Initialize BooleanVars for operations
        self.download_logs = BooleanVar()
        self.nvram_demo_reset = BooleanVar()
        self.nvram_reset = BooleanVar()
        self.compare_file_versions = BooleanVar()
        self.update_file_versions = BooleanVar()

        # Add traces to enforce operation rules
        self.download_logs.trace_add('write', self.on_operation_select)
        self.nvram_demo_reset.trace_add('write', self.on_operation_select)
        self.nvram_reset.trace_add('write', self.on_operation_select)
        self.compare_file_versions.trace_add('write', self.on_operation_select)
        self.update_file_versions.trace_add('write', self.on_operation_select)

        # Custom name variable
        self.custom_name_var = tk.StringVar()

        # Create the layout for better user experience
        self.create_layout()

        # Progress bar for operations (initially hidden)
        self.progress_bar = None

        logger.debug("WinSCPAutomationApp initialized successfully")

    @log_function_call
    def create_layout(self):
        """
        Organize the layout into sections using frames.
        """
        # Device selection section
        device_frame = tk.Frame(self.root)
        device_frame.pack(pady=10)

        self.create_device_listbox(device_frame)
        self.create_device_selection_buttons(device_frame)

        # Operations section
        operations_frame = tk.Frame(self.root)
        operations_frame.pack(pady=10)

        self.create_checkbox("Compare File Versions", self.compare_file_versions, operations_frame)
        self.create_checkbox("Download Logs", self.download_logs, operations_frame)
        self.create_checkbox("Update File Versions", self.update_file_versions, operations_frame)
        self.create_checkbox("NVRAM Reset", self.nvram_reset, operations_frame)
        self.create_checkbox("NVRAM Demo Reset", self.nvram_demo_reset, operations_frame)

        # Folder selection section
        folder_frame = tk.Frame(self.root)
        folder_frame.pack(pady=10)

        # Download folder selection and label
        download_folder_frame = tk.Frame(folder_frame)
        download_folder_frame.pack(pady=10)
        self.create_button("Select Download Folder", self.select_download_folder, download_folder_frame)
        self.download_folder_label = tk.Label(download_folder_frame, text=f"Download Folder: {self.download_path}")
        self.download_folder_label.pack(pady=5)  # Placed below the button

        # Master payload folder selection and label
        master_payload_folder_frame = tk.Frame(folder_frame)
        master_payload_folder_frame.pack(pady=10)
        self.create_button("Select Master Payload Folder", self.select_master_payload_folder, master_payload_folder_frame)
        self.master_payload_folder_label = tk.Label(master_payload_folder_frame, text=f"Master Payload Folder: {self.master_payload_folder}")
        self.master_payload_folder_label.pack(pady=5)  # Placed below the button

        # Custom name entry for download_logs operation
        custom_name_frame = tk.Frame(self.root)
        custom_name_frame.pack(pady=10)

        custom_name_label = tk.Label(custom_name_frame, text="Custom Name for Logs (optional):")
        custom_name_label.pack(side=tk.LEFT)

        custom_name_entry = tk.Entry(custom_name_frame, textvariable=self.custom_name_var)
        custom_name_entry.pack(side=tk.LEFT)

        # Run operations button
        self.run_operations_button = self.create_button("Run Operations", self.run_operations_clicked)

    @log_function_call
    def show_progress_bar(self):
        """
        Show the progress bar and start it.
        """
        if not self.progress_bar:
            self.progress_bar = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=200, mode='indeterminate')
            self.progress_bar.pack(pady=10)
        self.progress_bar.start()

    @log_function_call
    def hide_progress_bar(self):
        """
        Hide the progress bar and stop it.
        """
        if self.progress_bar:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()  # Hide the progress bar

    @log_function_call
    def create_device_selection_buttons(self, parent_frame):
        """
        Create buttons for selecting and deselecting all devices.
        """
        select_all_button = tk.Button(parent_frame, text="Select All", command=self.select_all_devices)
        deselect_all_button = tk.Button(parent_frame, text="Deselect All", command=self.deselect_all_devices)
        select_all_button.pack(pady=5, side=tk.LEFT)
        deselect_all_button.pack(pady=5, side=tk.RIGHT)

    @log_function_call
    def select_all_devices(self):
        """
        Select all devices in the listbox.
        """
        self.device_listbox.select_set(0, tk.END)

    @log_function_call
    def deselect_all_devices(self):
        """
        Deselect all devices in the listbox.
        """
        self.device_listbox.select_clear(0, tk.END)

    @log_function_call
    def create_checkbox(self, label: str, var: BooleanVar, parent_frame=None) -> None:
        chk = tk.Checkbutton(parent_frame or self.root, text=label, variable=var)
        chk.pack(anchor=tk.W)
        logger.debug(f"Checkbox '{label}' created")

    @log_function_call
    def create_button(self, label: str, command: callable, parent_frame=None) -> tk.Button:
        btn = tk.Button(parent_frame or self.root, text=label, command=command)
        btn.pack(pady=5)
        logger.debug(f"Button '{label}' created")
        return btn

    @log_function_call
    def create_device_listbox(self, parent_frame=None) -> tk.Listbox:
        frame = tk.Frame(parent_frame or self.root)
        frame.pack(pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.device_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=50, height=10, yscrollcommand=scrollbar.set)
        self.device_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        scrollbar.config(command=self.device_listbox.yview)

        self.populate_device_list(self.device_listbox)
        return self.device_listbox

    @log_function_call
    def populate_device_list(self, listbox: tk.Listbox) -> None:
        listbox.delete(0, tk.END)
        if not os.path.exists(self.config_file):
            logger.error(f"Configuration file '{self.config_file}' not found.")
            messagebox.showerror("Error", f"Configuration file '{self.config_file}' not found.")
            return

        config = configparser.ConfigParser()
        config.read(self.config_file)
        devices = config.sections()
        for device_name in devices:
            listbox.insert(tk.END, device_name)

    @log_function_call
    def get_selected_devices(self) -> List[str]:
        selected_indices = self.device_listbox.curselection()
        selected_devices = [self.device_listbox.get(i) for i in selected_indices]
        return selected_devices

    @log_function_call
    def open_config_file(self) -> None:
        if os.path.exists(self.config_file):
            os.startfile(self.config_file)
        else:
            messagebox.showerror("Error", f"Configuration file '{self.config_file}' not found.")

    @log_function_call
    def select_download_folder(self) -> None:
        folder_selected = filedialog.askdirectory(initialdir=self.download_path, title="Select Download Folder")
        if folder_selected:
            self.download_path = os.path.normpath(folder_selected)
            self.save_setting("download_path", self.download_path)
            self.download_folder_label.config(text=f"Download Folder: {self.download_path}")

    @log_function_call
    def select_master_payload_folder(self) -> None:
        folder_selected = filedialog.askdirectory(initialdir=self.master_payload_folder, title="Select Master Payload Folder")
        if folder_selected:
            self.master_payload_folder = os.path.normpath(folder_selected)
            self.save_setting("master_payload_folder", self.master_payload_folder)
            self.master_payload_folder_label.config(text=f"Master Payload Folder: {self.master_payload_folder}")

    @log_function_call
    def load_saved_setting(self, key: str, default_value: str) -> str:
        settings_file = "user_settings.ini"
        config = configparser.ConfigParser()
        if os.path.exists(settings_file):
            config.read(settings_file)
            if config.has_section("Settings") and config.has_option("Settings", key):
                return config.get("Settings", key)
        return default_value

    @log_function_call
    def save_setting(self, key: str, value: str) -> None:
        settings_file = "user_settings.ini"
        config = configparser.ConfigParser()
        if os.path.exists(settings_file):
            config.read(settings_file)
        if not config.has_section("Settings"):
            config.add_section("Settings")
        config.set("Settings", key, value)
        with open(settings_file, "w") as configfile:
            config.write(configfile)

    @log_function_call
    def on_operation_select(self, *args):
        """
        Enforce operation rules when checkboxes are toggled.
        """
        selected_operations = {
            "download_logs": self.download_logs.get(),
            "nvram_demo_reset": self.nvram_demo_reset.get(),
            "nvram_reset": self.nvram_reset.get(),
            "compare_file_versions": self.compare_file_versions.get(),
            "update_file_versions": self.update_file_versions.get()
        }
        try:
            # Validate operations to enforce rules
            validate_operations(selected_operations)
        except ValueError as e:
            # Handle mutual exclusivity
            if 'nvram_reset' in str(e) or 'nvram_demo_reset' in str(e):
                # Undo the last change that caused the validation to fail
                if self.nvram_reset.get() and self.nvram_demo_reset.get():
                    # Determine which one to uncheck based on the error message
                    if 'NVRAM Reset' in str(e):
                        self.nvram_reset.set(False)
                    else:
                        self.nvram_demo_reset.set(False)
            # Enforce dependencies
            if 'requires' in str(e):
                # If operation requires another, uncheck it
                if self.download_logs.get() and not self.compare_file_versions.get():
                    self.download_logs.set(False)
                if self.update_file_versions.get() and not self.compare_file_versions.get():
                    self.update_file_versions.set(False)
            # Show error message
            messagebox.showwarning("Invalid Selection", str(e))

    @log_function_call
    def run_operations_clicked(self):
        # Run operations
        selected_devices = self.get_selected_devices()
        if not selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device.")
            return

        selected_operations = {
            "download_logs": self.download_logs.get(),
            "nvram_demo_reset": self.nvram_demo_reset.get(),
            "nvram_reset": self.nvram_reset.get(),
            "compare_file_versions": self.compare_file_versions.get(),
            "update_file_versions": self.update_file_versions.get()
        }

        if not any(selected_operations.values()):
            messagebox.showwarning("No Operations Selected", "Please select at least one operation.")
            return

        # Validate operations
        try:
            validate_operations(selected_operations)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        # Get the custom name for logs if download_logs is selected
        custom_name = None
        if self.download_logs.get():
            custom_name = self.custom_name_var.get().strip()
            # Optionally, you can sanitize or validate the custom name here

        # Disable buttons during execution
        self.run_operations_button.config(state=tk.DISABLED, text="Running...")
        self.show_progress_bar()

        # Call the callback function
        self.operations_callback(
            selected_operations,
            self.download_path,
            self.master_payload_folder,
            selected_devices,
            custom_name,
            self.on_operations_complete,
            self.root
        )

    @log_function_call
    def on_operations_complete(self):
        # Re-enable the button when the operation is done
        self.run_operations_button.config(state=tk.NORMAL, text="Run Operations")
        self.hide_progress_bar()
        messagebox.showinfo("Operations Complete", "Selected operations have completed.")