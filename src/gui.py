# src/gui.py
import configparser
import os
import tkinter as tk
from tkinter import filedialog, messagebox, BooleanVar
import logging
from typing import List
from decorators import log_function_call

logger = logging.getLogger(__name__)

logger.info('Initializing GUI')
logger.debug('Setting up buttons and event handlers')


class WinSCPAutomationApp:
    def __init__(self, root: tk.Tk, operations_callback: callable) -> None:
        logger.debug("Initializing WinSCPAutomationApp")
        self.root = root
        self.root.title("WinSCP Automation Tool")
        self.root.geometry("500x600")

        self.operations_callback = operations_callback

        self.config_file = os.path.normpath(os.getenv('CONFIG_FILE', 'devices.ini'))
        logger.info(f"Config file path: {self.config_file}")

        self.download_path = self.load_saved_download_path()
        logger.info(f"Initial download path: {self.download_path}")

        self.download_logs = BooleanVar()
        self.nvram_demo_reset = BooleanVar()
        self.nvram_reset = BooleanVar()
        self.get_file_versions = BooleanVar()

        self.device_listbox = self.create_device_listbox()
        self.create_checkbox("Download Logs", self.download_logs)
        self.create_checkbox("NVRAM Demo Reset", self.nvram_demo_reset)
        self.create_checkbox("NVRAM Reset", self.nvram_reset)
        self.create_checkbox("Get File Versions", self.get_file_versions)

        self.create_button("Open Configuration File", self.open_config_file)
        self.create_button("Select Download Folder", self.select_download_folder)
        self.run_operations_button = self.create_button("Run Operations", self.run_operations_clicked)

        self.download_folder_label = tk.Label(root, text=f"Download Folder: {self.download_path}")
        self.download_folder_label.pack(pady=10)

        logger.debug("WinSCPAutomationApp initialized successfully")

    @log_function_call
    def create_checkbox(self, label: str, var: BooleanVar) -> None:
        chk = tk.Checkbutton(self.root, text=label, variable=var)
        chk.pack(anchor=tk.W)
        logger.debug(f"Checkbox '{label}' created")

    @log_function_call
    def create_button(self, label: str, command: callable) -> tk.Button:
        btn = tk.Button(self.root, text=label, command=command)
        btn.pack(pady=5)
        logger.debug(f"Button '{label}' created")
        return btn

    @log_function_call
    def create_device_listbox(self) -> tk.Listbox:
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        device_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=50, height=10, yscrollcommand=scrollbar.set)
        device_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        scrollbar.config(command=device_listbox.yview)

        self.populate_device_list(device_listbox)
        return device_listbox

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
            self.download_folder_label.config(text=f"Download Folder: {self.download_path}")
            self.save_download_path()

    @log_function_call
    def load_saved_download_path(self) -> str:
        settings_file = "user_settings.ini"
        config = configparser.ConfigParser()
        if os.path.exists(settings_file):
            config.read(settings_file)
            if config.has_section("Settings") and config.has_option("Settings", "download_path"):
                return config.get("Settings", "download_path")

        return os.getenv('DEFAULT_DOWNLOAD_PATH', 'C:\\DownloadedLogs')

    @log_function_call
    def save_download_path(self) -> None:
        settings_file = "user_settings.ini"
        config = configparser.ConfigParser()
        if os.path.exists(settings_file):
            config.read(settings_file)
        if not config.has_section("Settings"):
            config.add_section("Settings")
        config.set("Settings", "download_path", self.download_path)
        with open(settings_file, "w") as configfile:
            config.write(configfile)

    @log_function_call
    def run_operations_clicked(self):
        # Disable the button
        self.run_operations_button.config(state=tk.DISABLED)
        # Start the operations
        selected_devices = self.get_selected_devices()

        if not selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device.")
            self.run_operations_button.config(state=tk.NORMAL)
            return

        if not any([self.download_logs.get(), self.nvram_demo_reset.get(), self.nvram_reset.get(), self.get_file_versions.get()]):
            messagebox.showwarning("No Operations Selected", "Please select at least one operation.")
            self.run_operations_button.config(state=tk.NORMAL)
            return

        self.operations_callback({
            "download_logs": self.download_logs.get(),
            "nvram_demo_reset": self.nvram_demo_reset.get(),
            "nvram_reset": self.nvram_reset.get(),
            "get_file_versions": self.get_file_versions.get()
        }, self.download_path, selected_devices, self.on_operations_complete, self.root)

    @log_function_call
    def on_operations_complete(self):
        # Re-enable the button
        self.run_operations_button.config(state=tk.NORMAL)
        # Optionally show a message to the user
        messagebox.showinfo("Operations Complete", "Selected operations have completed.")
