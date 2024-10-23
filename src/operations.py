# src/operations.py

import clr
import os
import logging
from typing import List, Dict, Optional
from contextlib import contextmanager

# Initialize .NET Interop with pythonnet
winscp_dll_path = os.path.abspath("lib/WinSCP/WinSCPnet.dll")
clr.AddReference(winscp_dll_path)
from WinSCP import (
    Session,
    SessionOptions,
    Protocol,
    TransferOptions,
    TransferOperationResult,
    TransferMode,
    SessionRemoteException,
)

from utils import (
    get_transfer_options,
    sanitize_folder_name,
    create_parent_archive_folder,
    create_device_archive_folder,
)

logger = logging.getLogger(__name__)

def load_devices(config_file: str) -> List[Dict[str, str]]:
    """
    Loads device configurations from a specified configuration file.

    :param config_file: Path to the INI configuration file containing device sections.
    :return: A list of dictionaries, each containing connection information for a device.
    :raises FileNotFoundError: If the configuration file is not found.
    :raises ValueError: If required device information is missing in the configuration file.
    """
    logger.debug(f"Loading device configurations from {config_file}")

    if not os.path.exists(config_file):
        logger.error(f"Configuration file '{config_file}' not found.")
        raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

    import configparser
    config = configparser.ConfigParser()
    config.read(config_file)
    devices = []

    for device in config.sections():
        try:
            device_info = {
                'name': device,
                'ip': config[device]['ip'],
                'username': config[device]['username'],
                'password': config[device]['password']
            }
            devices.append(device_info)
            logger.debug(f"Loaded device: {device_info}")
        except KeyError as e:
            logger.error(f"Missing required field {e} in device section [{device}]")
            raise ValueError(f"Missing required field {e} in device section [{device}]") from e

    return devices

def get_devices_to_process(selected_devices: List[str]) -> List[Dict[str, str]]:
    """
    Filters the devices based on the selected device names.

    :param selected_devices: List of device names chosen for processing.
    :return: A list of device dictionaries containing connection information for each selected device.
    """
    config_file = os.path.normpath(os.getenv('CONFIG_FILE', 'devices.ini'))
    devices = load_devices(config_file)
    return [device for device in devices if device['name'] in selected_devices]

@contextmanager
def device_session(device: Dict[str, str]) -> Optional[Session]:
    """
    Context manager for creating and disposing of a WinSCP session.

    :param device: Device information dictionary.
    :yield: An active WinSCP session if successful, or None if the session creation fails.
    """
    device_logger = logging.LoggerAdapter(logger, {'device': device['name']})
    session = None
    try:
        session = Session()
        session_options = SessionOptions()
        session_options.Protocol = Protocol.Sftp
        session_options.HostName = device['ip']
        session_options.UserName = device['username']
        session_options.Password = device['password']
        session_options.GiveUpSecurityAndAcceptAnySshHostKey = True

        device_logger.info("Opening WinSCP session")
        session.Open(session_options)
        device_logger.debug("Session opened successfully")
        yield session
    except Exception as e:
        device_logger.error(f"Failed to create session: {e}", exc_info=True)
        yield None
    finally:
        if session:
            session.Dispose()
            device_logger.debug("Session disposed")

def download_logs(selected_devices: List[str], base_download_path: str, custom_name: Optional[str] = None) -> bool:
    """
    Downloads logs from selected devices to a specified local folder, preserving the subfolder structure.
    Creates a parent folder named after the current date and time, optionally including a custom name provided by the user.

    :param selected_devices: List of device names chosen for log download.
    :param base_download_path: Base path to the local directory where logs should be downloaded.
    :param custom_name: Optional custom name to include in the parent folder name.
    :return: True if logs are successfully downloaded from all devices, False if errors occur for any device.
    """
    logger.info("Starting log download operation")

    # Create the parent archive folder using utils.py utility
    parent_folder_path = create_parent_archive_folder(base_download_path, custom_name)
    logger.debug(f"Created parent folder: {parent_folder_path}")

    devices_to_process = get_devices_to_process(selected_devices)
    success = True

    for device in devices_to_process:
        device_logger = logging.LoggerAdapter(logger, {'device': device['name']})
        with device_session(device) as session:
            if not session:
                device_logger.error("Session could not be established. Skipping device.")
                success = False
                continue

            try:
                # Create the device-specific archive folder
                device_download_folder = create_device_archive_folder(parent_folder_path, device['name'])

                device_logger.info(f"Downloading logs into {device_download_folder}")

                # Get the predefined transfer options
                transfer_options = get_transfer_options()

                # Download logs from /tmp/logs/ with subfolder structure preserved
                result: TransferOperationResult = session.GetFiles(
                    "/tmp/logs/*", device_download_folder + "\\*", False, transfer_options)
                result.Check()

                # Download logs from /mnt/log/ with subfolder structure preserved
                result = session.GetFiles(
                    "/mnt/log/*", device_download_folder + "\\*", False, transfer_options)
                result.Check()

                device_logger.info("Logs downloaded successfully")

                # Call log_file_versions to get the list of .iso and .sig files and write to "PAYLOAD.txt"
                log_file_versions(session, device_download_folder, device['name'])

            except SessionRemoteException as e:
                success = False
                device_logger.error(f"Error during log download: {e}", exc_info=True)
            except Exception as e:
                success = False
                device_logger.error(f"Unexpected error: {e}", exc_info=True)

    logger.info("Completed log download operation")
    return success

def log_file_versions(session: Session, device_download_folder: str, device_name: str) -> None:
    """
    Retrieves a sorted list of all .iso and .sig files in the device and writes it to a .txt file named "PAYLOAD.txt" in the device_download_folder.

    :param session: Active WinSCP session for the device.
    :param device_download_folder: Path to the local directory where the "PAYLOAD.txt" file should be saved.
    :param device_name: Name of the device.
    :return: None
    """
    device_logger = logging.LoggerAdapter(logger, {'device': device_name})
    flash_path = '/mnt/flash'

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

        device_logger.debug(f"PAYLOAD.txt file written to {payload_file_path}")
    except Exception as e:
        device_logger.error(f"Error retrieving file versions: {e}", exc_info=True)

def compare_file_versions(selected_devices: List[str], master_payload_folder: str) -> None:
    """
    Compares .iso files on selected devices with the master payload folder and reports outdated files.

    :param selected_devices: List of device names chosen for comparison.
    :param master_payload_folder: Path to the local folder containing the latest .iso files.
    :return: None
    """
    logger.info("Starting file version comparison")
    flash_path = '/mnt/flash'
    devices_to_process = get_devices_to_process(selected_devices)
    outdated_files_info = {}

    master_files = {
        file: os.path.join(master_payload_folder, file)
        for file in os.listdir(master_payload_folder) if file.endswith('.iso')
    }

    for device in devices_to_process:
        device_logger = logging.LoggerAdapter(logger, {'device': device['name']})
        with device_session(device) as session:
            if not session:
                device_logger.error("Session could not be established. Skipping device.")
                continue

            try:
                remote_files = session.ListDirectory(flash_path).Files
                device_files = [file.Name for file in remote_files if file.Name.endswith('.iso')]

                outdated_files = [file for file in device_files if file not in master_files]
                if outdated_files:
                    outdated_files_info[device['name']] = outdated_files
                    device_logger.warning(f"Outdated files found: {outdated_files}")
                else:
                    device_logger.info("All files are up-to-date")
            except Exception as e:
                device_logger.error(f"Error comparing files: {e}", exc_info=True)

    display_outdated_files_to_user(outdated_files_info, master_files)
    logger.info("Completed file version comparison")

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
    message += "Master files:\n" + "\n".join(sorted(master_files.keys()))

    logger.info("Displaying outdated files to user")
    messagebox.showinfo("Outdated ISO Files", message)

def remount_flash_as_rw(session: Session, device_name: str) -> None:
    """
    Remounts the /mnt/flash directory with read-write permissions using the specified session.

    :param session: Active WinSCP session to execute the remount command.
    :param device_name: Name of the device.
    """
    device_logger = logging.LoggerAdapter(logger, {'device': device_name})
    try:
        device_logger.debug("Remounting /mnt/flash as read-write")
        session.ExecuteCommand("mount /mnt/flash -o remount,rw")
        device_logger.info("Successfully remounted /mnt/flash as read-write")
    except Exception as e:
        device_logger.error(f"Failed to remount /mnt/flash as read-write: {e}", exc_info=True)
        raise

def remount_nvram_as_rw(session: Session, device_name: str) -> None:
    """
    Remounts the /mnt/nvram directory with read-write permissions using the specified session.

    :param session: Active WinSCP session to execute the remount command.
    :param device_name: Name of the device.
    """
    device_logger = logging.LoggerAdapter(logger, {'device': device_name})
    try:
        device_logger.debug("Remounting /mnt/nvram as read-write")
        session.ExecuteCommand("mount /mnt/nvram -o remount,rw")
        device_logger.info("Successfully remounted /mnt/nvram as read-write")
    except Exception as e:
        device_logger.error(f"Failed to remount /mnt/nvram as read-write: {e}", exc_info=True)
        raise

def update_file_versions(selected_devices: List[str], master_payload_folder: str) -> None:
    """
    Updates .iso and .sig files on selected devices by deleting outdated files and uploading the latest versions.

    :param selected_devices: List of device names chosen for the update.
    :param master_payload_folder: Path to the local folder containing the latest .iso and .sig files.
    """
    logger.info("Starting file version update")
    flash_path = '/mnt/flash'
    devices_to_process = get_devices_to_process(selected_devices)
    master_files = {
        file: os.path.join(master_payload_folder, file)
        for file in os.listdir(master_payload_folder) if file.endswith('.iso') or file.endswith('.sig')
    }

    transfer_options = get_transfer_options()

    for device in devices_to_process:
        device_logger = logging.LoggerAdapter(logger, {'device': device['name']})
        with device_session(device) as session:
            if not session:
                device_logger.error("Session could not be established. Skipping device.")
                continue

            try:
                device_logger.info("Checking for outdated or missing files")
                remote_files = session.ListDirectory(flash_path).Files
                device_files = [file.Name for file in remote_files if file.Name.endswith('.iso') or file.Name.endswith('.sig')]

                outdated_files = [file for file in device_files if file not in master_files]
                missing_files = [file for file in master_files if file not in device_files]

                if outdated_files or missing_files:
                    remount_flash_as_rw(session, device['name'])

                    if outdated_files:
                        device_logger.info(f"Deleting outdated files: {outdated_files}")
                        for file in outdated_files:
                            session.RemoveFiles(f"{flash_path}/{file}").Check()

                    device_logger.info("Uploading latest files")
                    for file, path in master_files.items():
                        session.PutFiles(path, f"{flash_path}/{file}", False, transfer_options).Check()
                else:
                    device_logger.info("No outdated or missing files found")

            except Exception as e:
                device_logger.error(f"Error updating files: {e}", exc_info=True)

    logger.info("Completed file version update")

def reboot(session: Session, device_name: str) -> None:
    """
    Reboots the device using the specified session.

    :param session: Active WinSCP session to execute the reboot command.
    :param device_name: Name of the device.
    """
    device_logger = logging.LoggerAdapter(logger, {'device': device_name})
    try:
        device_logger.info("Initiating reboot")
        session.ExecuteCommand("reboot")
        device_logger.info("Reboot command sent successfully")
    except Exception as e:
        device_logger.error(f"Failed to initiate reboot: {e}", exc_info=True)
        raise

def nvram_reset(nvram_path: str, selected_devices: List[str]) -> None:
    """
    Resets the NVRAM by deleting all files in the specified path for selected devices.

    :param nvram_path: Path to the NVRAM directory on the devices.
    :param selected_devices: List of device names chosen for NVRAM reset.
    :return: None
    """
    logger.info("Starting NVRAM reset")
    devices_to_process = get_devices_to_process(selected_devices)

    for device in devices_to_process:
        device_logger = logging.LoggerAdapter(logger, {'device': device['name']})
        with device_session(device) as session:
            if not session:
                device_logger.error("Session could not be established. Skipping device.")
                continue

            try:
                device_logger.info(f"Resetting NVRAM at {nvram_path}")
                session.RemoveFiles(f"{nvram_path}/*").Check()
                device_logger.info("NVRAM reset successfully")
                reboot(session, device['name'])
            except Exception as e:
                device_logger.error(f"Error resetting NVRAM: {e}", exc_info=True)

    logger.info("Completed NVRAM reset")

def nvram_demo_reset(nvram_path: str, selected_devices: List[str]) -> None:
    """
    Performs a demo reset on the NVRAM by deleting all files except 'Demo.dat'.
    If 'Demo.dat' does not exist on the device, it is pushed from the local './config/Demo.dat'.

    :param nvram_path: Path to the NVRAM directory on the devices.
    :param selected_devices: List of device names chosen for the demo reset.
    :return: None
    """
    logger.info("Starting NVRAM demo reset")
    devices_to_process = get_devices_to_process(selected_devices)
    local_demo_path = os.path.abspath(os.getenv('LOCAL_DEMO_PATH', './config/Demo.dat'))

    for device in devices_to_process:
        device_logger = logging.LoggerAdapter(logger, {'device': device['name']})
        with device_session(device) as session:
            if not session:
                device_logger.error("Session could not be established. Skipping device.")
                continue

            try:
                device_logger.info("Checking for 'Demo.dat'")
                # List all files in nvram_path and check if 'Demo.dat' is present
                remote_directory = session.ListDirectory(nvram_path)
                demo_file_found = any(file.Name == "Demo.dat" for file in remote_directory.Files)

                if demo_file_found:
                    # Delete all files except 'Demo.dat'
                    device_logger.info("'Demo.dat' found. Deleting other files.")
                    files_to_delete = [file for file in remote_directory.Files if file.Name not in ["Demo.dat", ".", ".."]]

                    for file in files_to_delete:
                        session.RemoveFiles(f"{nvram_path}/{file.Name}").Check()

                    device_logger.info("NVRAM demo reset completed")
                    reboot(session, device['name'])

                else:
                    device_logger.info("'Demo.dat' not found. Uploading from local path.")
                    if os.path.exists(local_demo_path):
                        remount_nvram_as_rw(session, device['name'])
                        session.PutFiles(local_demo_path, f"{nvram_path}/Demo.dat").Check()
                        device_logger.info("'Demo.dat' uploaded successfully")
                        reboot(session, device['name'])
                    else:
                        device_logger.error(f"Local 'Demo.dat' not found at {local_demo_path}")
                        continue

            except Exception as e:
                device_logger.error(f"Error during NVRAM demo reset: {e}", exc_info=True)

    logger.info("Completed NVRAM demo reset")
