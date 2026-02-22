# src/operations.py
import clr
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from config_manager import config_manager

# Initialize .NET Interop with pythonnet
winscp_dll_path = os.path.abspath(config_manager.get('winscp.dll_path'))
clr.AddReference(winscp_dll_path)
from WinSCP import Session, SessionOptions, Protocol, TransferOptions, TransferOperationResult, TransferMode

logger = logging.getLogger(__name__)

def create_session(device: Dict[str, str]) -> Optional[Session]:
    """
    Creates and opens a WinSCP session using the provided device credentials.

    :param device: A dictionary containing device connection information with keys:
        - 'name': Name of the device.
        - 'ip': IP address of the device.
        - 'username': Username for authentication.
        - 'password': Password for authentication.
    :return: An active WinSCP session if successful, or None if the session creation fails.
    """
    try:
        session = Session()
        session_options = SessionOptions()
        session_options.Protocol = Protocol.Sftp
        session_options.HostName = device['ip']
        session_options.UserName = device['username']
        session_options.Password = device['password']
        session_options.GiveUpSecurityAndAcceptAnySshHostKey = True
       
        logger.info(f"Opening WinSCP session for {device['name']}...")
        session.Open(session_options)
        return session
    except Exception as e:
        logger.error(f"Failed to create session for {device['name']} - {e}")
        return None

def get_transfer_options() -> TransferOptions:
    """
    Creates and returns a TransferOptions object with predefined settings.
    """
    transfer_options = TransferOptions()
    transfer_options.TransferMode = TransferMode.Binary
    transfer_options.PreserveDirectories = True
    transfer_options.SpeedLimit = 0
    return transfer_options

def get_devices_to_process(selected_devices: List[str]) -> List[Dict[str, str]]:
    """
    Filters the devices based on the selected device names.

    :param selected_devices: List of device names chosen for processing.
    :return: A list of device dictionaries containing connection information for each selected device.
    """
    devices = config_manager.get_devices()
    return [device for device in devices if device['name'] in selected_devices]

def sanitize_folder_name(name: str) -> str:
    """
    Sanitizes a folder name by removing or replacing invalid characters.

    :param name: The original folder name.
    :return: A sanitized folder name safe for use in file systems.
    """
    import re
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized_name = re.sub(invalid_chars, '_', name)
    return sanitized_name

def download_logs(selected_devices: List[str], base_download_path: str, custom_name: Optional[str] = None) -> bool:
    """
    Downloads logs from selected devices to a specified local folder, preserving the subfolder structure.
    Creates a parent folder named after the current date and time, optionally including a custom name provided by the user.

    :param selected_devices: List of device names chosen for log download.
    :param base_download_path: Base path to the local directory where logs should be downloaded.
    :param custom_name: Optional custom name to include in the parent folder name.
    :return: True if logs are successfully downloaded from all devices, False if errors occur for any device.
    """
    # Get the current date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Construct the parent folder name
    if custom_name:
        parent_folder_name = f"{current_datetime}-{custom_name}"
    else:
        parent_folder_name = current_datetime

    # Ensure the parent folder name is valid
    parent_folder_name = sanitize_folder_name(parent_folder_name)

    # Create the parent folder
    parent_folder_path = os.path.join(base_download_path, parent_folder_name)
    os.makedirs(parent_folder_path, exist_ok=True)
    logger.info(f"Created parent folder: {parent_folder_path}")

    devices_to_process = get_devices_to_process(selected_devices)
    success = True

    for device in devices_to_process:
        session = create_session(device)
        if not session:
            continue

        try:
            # Create a dedicated download folder for each device inside the parent folder
            device_download_folder = os.path.join(parent_folder_path, device['name'])
            os.makedirs(device_download_folder, exist_ok=True)

            logger.info(f"Downloading logs for device: {device['name']} into {device_download_folder}")

            # Get the predefined transfer options
            transfer_options = get_transfer_options()

            # Download logs from /tmp/logs/ with subfolder structure preserved
            result: TransferOperationResult = session.GetFiles("/tmp/logs/*", device_download_folder + "\\*", False, transfer_options)
            result.Check()

            # Download logs from /mnt/log/ with subfolder structure preserved        
            result: TransferOperationResult = session.GetFiles("/mnt/log/*", device_download_folder + "\\*", False, transfer_options)
            result.Check()
                
            logger.info(f"Successfully downloaded logs for {device['name']}")

            # Call log_file_versions to get the list of .iso files and write to "PAYLOAD.txt" in device_download_folder
            log_file_versions(session, device_download_folder)

        except Exception as e:
            success = False
            logger.error(f"Error downloading logs for {device['name']}: {e}")
        finally:
            session.Dispose()

    return success

def log_file_versions(session: Session, device_download_folder: str) -> None:
    """
    Retrieves a sorted list of all .iso and .sig files in the device and writes it to a .txt file named "PAYLOAD.txt" in the device_download_folder.

    :param session: Active WinSCP session for the device.
    :param device_download_folder: Path to the local directory where the "PAYLOAD.txt" file should be saved.
    :return: None
    """
    flash_path = config_manager.get('paths.flash_path')

    try:
        remote_files = session.ListDirectory(flash_path).Files
        # Include both .iso and .sig files
        iso_sig_files = [file.Name for file in remote_files if file.Name.endswith('.iso') or file.Name.endswith('.sig')]
        # Sort the file names alphabetically
        iso_sig_files.sort()

        # Write the sorted list to a file named "PAYLOAD.txt" in device_download_folder
        payload_file_path = os.path.join(device_download_folder, "PAYLOAD.txt")
        with open(payload_file_path, 'w') as payload_file:
            for file_name in iso_sig_files:
                payload_file.write(file_name + '\n')

        logger.info(f"PAYLOAD.txt file written to {payload_file_path}")
    except Exception as e:
        logger.error(f"Error getting files for device: {e}")

def compare_file_versions(selected_devices: List[str], master_payload_folder: str) -> None:
    """
    Compares .iso files on selected devices with the master payload folder and reports outdated files.

    :param selected_devices: List of device names chosen for comparison.
    :param master_payload_folder: Path to the local folder containing the latest .iso files.
    :return: None
    """
    flash_path = config_manager.get('paths.flash_path')
    devices_to_process = get_devices_to_process(selected_devices)
    outdated_files_info = {}

    master_files = {
        file: os.path.join(master_payload_folder, file)
        for file in os.listdir(master_payload_folder) if file.endswith('.iso')
    }

    for device in devices_to_process:
        session = create_session(device)
        if not session:
            continue

        try:
            remote_files = session.ListDirectory(flash_path).Files
            device_files = [file.Name for file in remote_files if file.Name.endswith('.iso')]

            outdated_files = [file for file in device_files if file not in master_files]
            if outdated_files:
                outdated_files_info[device['name']] = outdated_files
        except Exception as e:
            logger.error(f"Error comparing files for {device['name']}: {e}")
        finally:
            session.Dispose()

    display_outdated_files_to_user(outdated_files_info, master_files)

def remount_flash_as_rw(session: Session) -> None:
    """
    Remounts the flash directory with read-write permissions using the specified session.

    :param session: Active WinSCP session to execute the remount command.
    """
    flash_path = config_manager.get('paths.flash_path')
    try:
        logger.info(f"Remounting {flash_path} as read-write")
        session.ExecuteCommand(f"mount {flash_path} -o remount,rw")
        logger.info(f"Successfully remounted {flash_path} as read-write")
    except Exception as e:
        logger.error(f"Failed to remount {flash_path} as read-write: {e}")
        raise
    
def remount_nvram_as_rw(session: Session) -> None:
    """
    Remounts the NVRAM directory with read-write permissions using the specified session.

    :param session: Active WinSCP session to execute the remount command.
    """
    nvram_path = config_manager.get('paths.nvram_path')
    try:
        logger.info(f"Remounting {nvram_path} as read-write")
        session.ExecuteCommand(f"mount {nvram_path} -o remount,rw")
        logger.info(f"Successfully remounted {nvram_path} as read-write")
    except Exception as e:
        logger.error(f"Failed to remount {nvram_path} as read-write: {e}")
        raise

def update_file_versions(selected_devices: List[str], master_payload_folder: str) -> None:
    """
    Updates .iso and .sig files on selected devices by deleting outdated files and uploading the latest versions.

    :param selected_devices: List of device names chosen for the update.
    :param master_payload_folder: Path to the local folder containing the latest .iso and .sig files.
    """
    flash_path = config_manager.get('paths.flash_path')
    devices_to_process = get_devices_to_process(selected_devices)
    master_files = {
        file: os.path.join(master_payload_folder, file)
        for file in os.listdir(master_payload_folder) if file.endswith('.iso') or file.endswith('.sig')
    }

    # Get the predefined transfer options
    transfer_options = get_transfer_options()

    for device in devices_to_process:
        session = create_session(device)
        if not session:
            continue

        try:
            logger.info(f"Updating .iso and .sig files for device: {device['name']}")
            remote_files = session.ListDirectory(flash_path).Files
            device_files = [file.Name for file in remote_files if file.Name.endswith('.iso') or file.Name.endswith('.sig')]

            outdated_files = [file for file in device_files if file not in master_files]

            # Determine if there are files to upload (missing on device)
            missing_files = [file for file in master_files if file not in device_files]

            if outdated_files or missing_files:
                # Remount the flash path as read-write before making any changes
                remount_flash_as_rw(session)

                if outdated_files:
                    logger.info(f"Deleting outdated files: {outdated_files}")
                    for file in outdated_files:
                        session.RemoveFiles(f"{flash_path}/{file}").Check()

                logger.info(f"Uploading latest files for {device['name']}")
                for file, path in master_files.items():
                    session.PutFiles(path, f"{flash_path}/{file}", False, transfer_options).Check()
            else:
                logger.info(f"No outdated or missing files for device {device['name']}")

        except Exception as e:
            logger.error(f"Error updating files for {device['name']}: {e}")
        finally:
            session.Dispose()
            
def reboot(session: Session) -> None:
    """
    Reboots the device using the specified session.

    :param session: Active WinSCP session to execute the reboot command.
    """
    try:
        logger.info("Initiating reboot")
        session.ExecuteCommand("reboot")
        logger.info("Successfully initiated reboot")
    except Exception as e:
        logger.error(f"Failed to initiate reboot: {e}")
        raise

def nvram_reset(nvram_path: str, selected_devices: List[str]) -> None:
    """
    Resets the NVRAM by deleting all files in the specified path for selected devices.

    :param nvram_path: Path to the NVRAM directory on the devices.
    :param selected_devices: List of device names chosen for NVRAM reset.
    :return: None
    """
    devices_to_process = get_devices_to_process(selected_devices)
    confirm_reboot = config_manager.get('operations.confirm_before_reboot', True)
    
    for device in devices_to_process:
        session = create_session(device)
        if not session:
            continue

        try:
            logger.info(f"Resetting NVRAM for device: {device['name']} at {nvram_path}")
            remount_nvram_as_rw(session)
            session.RemoveFiles(f"{nvram_path}/*").Check()
            logger.info(f"Successfully reset NVRAM for {device['name']}")
            
            if confirm_reboot:
                from tkinter import messagebox
                reboot_confirm = messagebox.askyesno(
                    "Confirm Reboot", 
                    f"NVRAM reset completed for {device['name']}. Reboot device now?"
                )
                if reboot_confirm:
                    reboot(session)
            else:
                reboot(session)
                
        except Exception as e:
            logger.error(f"Error resetting NVRAM for {device['name']}: {e}")
        finally:
            session.Dispose()

def nvram_demo_reset(nvram_path: str, selected_devices: List[str]) -> None:
    """
    Performs a demo reset on the NVRAM by deleting all files except 'Demo.dat'.
    If 'Demo.dat' does not exist on the device, it is pushed from the local './config/Demo.dat'.

    :param nvram_path: Path to the NVRAM directory on the devices.
    :param selected_devices: List of device names chosen for the demo reset.
    :return: None
    """
    devices_to_process = get_devices_to_process(selected_devices)
    local_demo_path = os.path.abspath(config_manager.get('paths.local_demo_path'))
    confirm_reboot = config_manager.get('operations.confirm_before_reboot', True)

    for device in devices_to_process:
        session = create_session(device)
        if not session:
            continue

        try:
            logger.info(f"Running demo NVRAM reset for device: {device['name']}")
            
            # List all files in nvram_path and check if 'Demo.dat' is present
            remote_directory = session.ListDirectory(nvram_path)
            demo_file_found = any(file.Name == "Demo.dat" for file in remote_directory.Files)

            if demo_file_found:
                # Filter out 'Demo.dat' and delete the rest of the files in nvram_path
                logger.info(f"'Demo.dat' found in {nvram_path}")
                remount_nvram_as_rw(session)
                files_to_delete = [file for file in remote_directory.Files if file.Name != "Demo.dat" and file.Name != "." and file.Name != ".."]

                # Delete each file except for 'Demo.dat'
                for file in files_to_delete:
                    logger.debug(f"Removing: {nvram_path}/{file.Name}")
                    session.RemoveFiles(f"{nvram_path}/{file.Name}").Check()
                    
                logger.info(f"All files except 'Demo.dat' have been deleted from {nvram_path}")
                
                if confirm_reboot:
                    from tkinter import messagebox
                    reboot_confirm = messagebox.askyesno(
                        "Confirm Reboot", 
                        f"NVRAM demo reset completed for {device['name']}. Reboot device now?"
                    )
                    if reboot_confirm:
                        reboot(session)
                else:
                    reboot(session)
            
            else:
                logger.info(f"'Demo.dat' not found in {nvram_path}, uploading from {local_demo_path}...")
                
                if os.path.exists(local_demo_path):
                    remount_nvram_as_rw(session)
                    session.PutFiles(local_demo_path, f"{nvram_path}/Demo.dat").Check()
                    logger.info(f"'Demo.dat' successfully uploaded to {nvram_path}")
                    
                    if confirm_reboot:
                        from tkinter import messagebox
                        reboot_confirm = messagebox.askyesno(
                            "Confirm Reboot", 
                            f"NVRAM demo reset completed for {device['name']}. Reboot device now?"
                        )
                        if reboot_confirm:
                            reboot(session)
                    else:
                        reboot(session)
                else:
                    logger.error(f"Local 'Demo.dat' not found at {local_demo_path}")
                    return

            logger.info(f"Successfully demo-reset NVRAM for {device['name']}")
        except Exception as e:
            logger.error(f"Error during demo reset for {device['name']}: {e}")
        finally:
            session.Dispose()

def display_outdated_files_to_user(outdated_files_info: Dict[str, List[str]], master_files: Dict[str, str]) -> None:
    """
    Displays a message box showing devices with outdated .iso files,
    or a message when all files are up to date, and displays master files.

    :param outdated_files_info: A dictionary with device names as keys and a list of outdated .iso files as values.
    :param master_files: A dictionary of master .iso files.
    :return: None
    """
    from tkinter import messagebox

    if not outdated_files_info:
        message = "All files are up-to-date."
        logger.info(message)
        messagebox.showinfo("Up-to-Date Files", message)
        return

    message = "The following devices have outdated .iso files:\n\n"
    for device, files in outdated_files_info.items():
        message += f"{device}:\n" + "\n".join(files) + "\n\n"

    # Add master_files to the message
    message += "Master files:\n" + "\n".join(master_files.keys())

    messagebox.showinfo("Outdated ISO Files", message)

