# src/archive.py
import os
from datetime import datetime

def create_archive_path(device_name, base_download_path):
    # Get the current date and time
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y_%m_%d %H-%M-%S")
    
    # Create the folder name: "YYYY_MM_DD HH-MM-SS device_name"
    folder_name = f"{formatted_time} {device_name}"
    
    # Full path for the archive folder
    archive_path = os.path.join(base_download_path, folder_name)

    # Create the folder if it doesn't exist
    os.makedirs(archive_path, exist_ok=True)
    
    return archive_path
