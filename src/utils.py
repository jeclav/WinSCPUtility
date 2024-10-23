# src/utils.py

import os
import re
from datetime import datetime
from typing import Optional

def sanitize_folder_name(name: str) -> str:
    """
    Sanitizes a folder name by removing or replacing invalid characters.

    :param name: The original folder name.
    :return: A sanitized folder name safe for use in file systems.
    """
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized_name = re.sub(invalid_chars, '_', name)
    return sanitized_name

def create_parent_archive_folder(base_download_path: str, custom_name: Optional[str] = None) -> str:
    """
    Creates a parent archive folder named after the current date and time,
    optionally including a custom name.

    :param base_download_path: Base path where the archive folder will be created.
    :param custom_name: Optional custom name to include in the folder name.
    :return: The path to the created parent archive folder.
    """
    # Get the current date and time
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    # Create the folder name: "YYYY-MM-DD_HH-MM-SS-CustomName"
    if custom_name:
        folder_name = f"{formatted_time}-{custom_name}"
    else:
        folder_name = formatted_time

    # Sanitize the folder name
    folder_name = sanitize_folder_name(folder_name)

    # Full path for the archive folder
    archive_path = os.path.join(base_download_path, folder_name)

    # Create the folder if it doesn't exist
    os.makedirs(archive_path, exist_ok=True)

    return archive_path

def create_device_archive_folder(parent_archive_path: str, device_name: str) -> str:
    """
    Creates a device-specific archive folder within the parent archive folder.

    :param parent_archive_path: Path to the parent archive folder.
    :param device_name: Name of the device.
    :return: The path to the created device archive folder.
    """
    # Sanitize the device name
    device_folder_name = sanitize_folder_name(device_name)

    # Full path for the device archive folder
    device_archive_path = os.path.join(parent_archive_path, device_folder_name)

    # Create the folder if it doesn't exist
    os.makedirs(device_archive_path, exist_ok=True)

    return device_archive_path
