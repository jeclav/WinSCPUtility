# src/operations.py
import clr
import os
import logging
from typing import List, Dict, Optional

# Initialize .NET Interop with pythonnet
winscp_dll_path = os.path.abspath("lib/WinSCP/WinSCPnet.dll")
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

def get_devices_to_process(selected_devices: List[str]) -> List[Dict[str, str]]:
    """
    Filters the devices based on the selected device names.

    :param selected_devices: List of device names chosen for processing.
    :return: A list of device dictionaries containing connection information for each selected device.
    """
    config_file = os.path.normpath(os.getenv('CONFIG_FILE', 'devices.ini'))
    devices = load_devices(config_file)
    return [device for device in devices if device['name'] in selected_devices]

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

def download_logs(selected_devices: List[str], download_path: str) -> bool:
    """
    Downloads logs from selected devices to a specified local folder, preserving the subfolder structure.

    :param selected_devices: List of device names chosen for log download.
    :param download_path: Path to the local directory where logs should be downloaded.
    :return: True if logs are successfully downloaded from all devices, False if errors occur for any device.
    """
    devices_to_process = get_devices_to_process(selected_devices)
    success = True

    for device in devices_to_process:
        session = create_session(device)
        if not session:
            continue

        try:
            # Create a dedicated download folder for each device
            device_download_folder = os.path.join(download_path, device['name'])
            os.makedirs(device_download_folder, exist_ok=True)

            logger.info(f"Downloading logs for device: {device['name']} into {device_download_folder}")

            # Configure transfer options to preserve subdirectory structure
            transfer_options = TransferOptions()
            transfer_options.TransferMode = TransferMode.Binary
            transfer_options.PreserveDirectories = True
            transfer_options.SpeedLimit = 0


            # Download logs from /tmp/logs/ with subfolder structure preserved
            result: TransferOperationResult = session.GetFiles("/tmp/logs/*", device_download_folder + "\\*", False, transfer_options)
            result.Check()

            # Download logs from /mnt/log/ with subfolder structure preserved        
            result: TransferOperationResult = session.GetFiles("/mnt/log/*", device_download_folder + "\\*", False, transfer_options)
            result.Check()
            


            logger.info(f"Successfully downloaded logs for {device['name']}")
        except Exception as e:
            success = False
            logger.error(f"Error downloading logs for {device['name']}: {e}")
        finally:
            session.Dispose()

    return success

def compare_file_versions(selected_devices: List[str], master_payload_folder: str) -> None:
    """
    Compares .iso files on selected devices with the master payload folder and reports outdated files.

    :param selected_devices: List of device names chosen for comparison.
    :param master_payload_folder: Path to the local folder containing the latest .iso files.
    :return: None
    """
    flash_path = '/mnt/flash'
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

    display_outdated_files_to_user(outdated_files_info)

def remount_flash_as_rw(session: Session) -> None:
    """
    Remounts the /mnt/flash directory with read-write permissions using the specified session.

    :param session: Active WinSCP session to execute the remount command.
    """
    try:
        logger.info("Remounting /mnt/flash as read-write")
        session.ExecuteCommand("mount /mnt/flash -o remount,rw")
        logger.info("Successfully remounted /mnt/flash as read-write")
    except Exception as e:
        logger.error(f"Failed to remount /mnt/flash as read-write: {e}")
        raise

def update_file_versions(selected_devices: List[str], master_payload_folder: str) -> None:
    """
    Updates .iso files on selected devices by deleting outdated files and uploading the latest versions.

    :param selected_devices: List of device names chosen for the update.
    :param master_payload_folder: Path to the local folder containing the latest .iso files.
    """
    flash_path = '/mnt/flash'
    devices_to_process = get_devices_to_process(selected_devices)
    master_files = {
        file: os.path.join(master_payload_folder, file)
        for file in os.listdir(master_payload_folder) if file.endswith('.iso')
    }

    for device in devices_to_process:
        session = create_session(device)
        if not session:
            continue

        try:
            # Remount the flash path as read-write before making any changes
            remount_flash_as_rw(session)

            logger.info(f"Updating .iso files for device: {device['name']}")
            remote_files = session.ListDirectory(flash_path).Files
            device_files = [file.Name for file in remote_files if file.Name.endswith('.iso')]
            outdated_files = [file for file in device_files if file not in master_files]

            if outdated_files:
                logger.info(f"Deleting outdated files: {outdated_files}")
                for file in outdated_files:
                    session.RemoveFiles(f"{flash_path}/{file}").Check()

                logger.info(f"Uploading latest files for {device['name']}")
                for file, path in master_files.items():
                    session.PutFiles(path, f"{flash_path}/{file}").Check()
        except Exception as e:
            logger.error(f"Error updating files for {device['name']}: {e}")
        finally:
            session.Dispose()
            
def reboot(session: Session) -> None:
    """
    Reboots the device using the specified session.

    :param session: Active WinSCP session to execute the remount command.
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
    
    for device in devices_to_process:
        session = create_session(device)
        if not session:
            continue

        try:
            logger.info(f"Resetting NVRAM for device: {device['name']} at {nvram_path}")
            session.RemoveFiles(f"{nvram_path}/*").Check()
            logger.info(f"Successfully reset NVRAM for {device['name']}")
            reboot(session)
        except Exception as e:
            logger.error(f"Error resetting NVRAM for {device['name']}: {e}")
        finally:
            session.Dispose()

def nvram_demo_reset(nvram_path: str, selected_devices: List[str]) -> None:
    """
    Performs a demo reset on the NVRAM by deleting all files except 'Demo.dat'.
    If 'Demo.dat' does not exist on the device, it is pushed from the local './config/demo.dat'.

    :param nvram_path: Path to the NVRAM directory on the devices.
    :param selected_devices: List of device names chosen for the demo reset.
    :return: None
    """
    devices_to_process = get_devices_to_process(selected_devices)
    local_demo_path = os.path.normpath(os.getenv('LOCAL_DEMO_PATH', './config/Demo.dat'))

    if not os.path.exists(local_demo_path):
        logger.error("Local 'Demo.dat' file not found at './config/demo.dat'.")
        return

    for device in devices_to_process:
        session = create_session(device)
        if not session:
            continue

        try:
            logger.info(f"Running demo NVRAM reset for device: {device['name']}")
            remote_files = session.ListDirectory(nvram_path).Files

            # Delete all files except 'Demo.dat'
            for file in remote_files:
                if file.Name != "Demo.dat":
                    session.RemoveFiles(f"{nvram_path}/{file.Name}").Check()

            # Check if 'Demo.dat' exists on the device; if not, push it from the local path
            # if "Demo.dat" not in [file.Name for file in remote_files]:
            #     logger.info(f"Pushing 'Demo.dat' to device {device['name']} at {nvram_path}")
            #     session.PutFiles(local_demo_path, f"{nvram_path}/Demo.dat").Check()
            #     logger.info(f"'Demo.dat' successfully pushed to device {device['name']}")

            logger.info(f"Successfully demo-reset NVRAM for {device['name']}")
        except Exception as e:
            logger.error(f"Error during demo reset for {device['name']}: {e}")
        finally:
            session.Dispose()


def display_outdated_files_to_user(outdated_files_info: Dict[str, List[str]]) -> None:
    """
    Displays a message box showing devices with outdated .iso files,
    or a message when all files are up to date.

    :param outdated_files_info: A dictionary with device names as keys and a list of outdated .iso files as values.
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

    messagebox.showinfo("Outdated ISO Files", message)


def test_winscp_session():
    """
    Tests the creation and opening of a WinSCP session with example connection parameters.

    :return: None
    """
    session = Session()
    session_options = SessionOptions()
    session_options.Protocol = Protocol.Sftp
    session_options.HostName = '172.17.28.65'  # Use valid hostname
    session_options.UserName = 'root'
    session_options.Password = 'root1234'
    session_options.GiveUpSecurityAndAcceptAnySshHostKey = True

    try:
        session.Open(session_options)
        print("Session successfully created")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.Dispose()

