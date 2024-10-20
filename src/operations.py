import os
import configparser
import subprocess
import re
import logging
from typing import List, Dict, Tuple, Optional
from decorators import log_function_call, handle_operation_errors

# Define a module-level logger
logger = logging.getLogger(__name__)


@log_function_call
def load_devices(config_file: str) -> List[Dict[str, str]]:
    """
    Loads device configurations from the specified config file.

    :param config_file: Path to the configuration file.
    :return: A list of device dictionaries containing name, ip, username, and password.
    """
    logger.debug(f"Loading device configurations from {config_file}")

    # Normalize the config file path
    config_file = os.path.normpath(config_file)

    if not os.path.exists(config_file):
        logger.error(f"Configuration file '{config_file}' not found.")
        raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

    config = configparser.ConfigParser()
    config.read(config_file)
    devices: List[Dict[str, str]] = []
    
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


@log_function_call
def get_devices_to_process(selected_devices: List[str]) -> List[Dict[str, str]]:
    """
    Retrieves the list of devices to process based on selected device names.

    :param selected_devices: List of selected device names.
    :return: List of device dictionaries to process.
    """
    config_file = os.path.normpath(os.getenv('CONFIG_FILE', 'devices.ini'))
    devices = load_devices(config_file)
    devices_to_process = [device for device in devices if device['name'] in selected_devices]
    logger.debug(f"Devices to process: {devices_to_process}")
    return devices_to_process


@log_function_call
def create_script(
    device: Dict[str, str],
    remote_folder: Optional[str] = None,
    download_path: Optional[str] = None,
    operation_type: str = "download"
) -> str:
    """
    Creates a WinSCP script for various operations like downloading logs, resetting NVRAM, etc.

    :param device: Device information dictionary.
    :param remote_folder: Remote folder path or NVRAM path for NVRAM operations.
    :param download_path: Local folder path for storing downloaded logs (optional for operations like reset).
    :param operation_type: Type of operation ('download', 'nvram_reset', 'nvram_demo_reset', 'get_file_versions').
    :return: The path to the created WinSCP script.
    """
    logger.debug(f"Creating WinSCP script for device '{device['name']}', operation '{operation_type}'")

    # Normalize paths for the script
    if remote_folder:
        remote_folder = remote_folder.replace('\\', '/')
    script_dir = os.path.normpath(os.getenv('WINSCP_SCRIPT_DIR', './scripts'))

    # Construct different scripts based on the operation type
    if operation_type == "download":
        # Ensure download path is provided for the download operation
        if not download_path:
            logger.error("download_path is required for the download operation")
            raise ValueError("download_path is required for the download operation")
        
        download_folder = os.path.join(os.path.normpath(download_path), f"{device['name']}")
        os.makedirs(download_folder, exist_ok=True)
        logger.debug(f"Downloading logs from: {device['name']} to: {download_folder}")
        
        script_content = f"""
            open sftp://{device['username']}:{device['password']}@{device['ip']}
            lcd "{download_folder}"
            cd /tmp
            get logs
            cd /mnt
            get log
            exit
            """
    elif operation_type == "nvram_reset":
        if not remote_folder:
            logger.error("remote_folder is required for NVRAM operations")
            raise ValueError("remote_folder is required for NVRAM operations")
        script_content = f"""
            open sftp://{device['username']}:{device['password']}@{device['ip']}
            rm "{remote_folder}/*"
            exit
            """
    elif operation_type == "nvram_demo_reset":
        if not remote_folder:
            logger.error("remote_folder is required for NVRAM operations")
            raise ValueError("remote_folder is required for NVRAM operations")
        script_content = f"""
            open sftp://{device['username']}:{device['password']}@{device['ip']}
            # Delete all files except 'Demo.dat' in the remote folder
            call find "{remote_folder}" -type f ! -name "Demo.dat" -exec rm {{}} \\;
            exit
            """
    elif operation_type == "get_file_versions":
        if not remote_folder:
            logger.error("remote_folder is required for get_file_versions operation")
            raise ValueError("remote_folder is required for get_file_versions operation")
        script_content = f"""
            open sftp://{device['username']}:{device['password']}@{device['ip']}
            ls "{remote_folder}/*.iso"
            exit
            """
    else:
        logger.error(f"Unsupported operation_type: {operation_type}")
        raise ValueError(f"Unsupported operation_type: {operation_type}")

    # Create script file
    script_path = os.path.join(script_dir, f"{operation_type}_{device['name']}.txt")
    os.makedirs(os.path.dirname(script_path), exist_ok=True)

    with open(script_path, 'w') as script_file:
        script_file.write(script_content.strip())

    logger.debug(f"Script created at path: {script_path}")
    return script_path


@log_function_call
def run_winscp_command(script_path: str) -> Tuple[str, str]:
    """
    Runs the WinSCP script and returns the stdout and stderr.

    :param script_path: The path to the WinSCP script.
    :return: stdout and stderr of the command.
    """
    logger.debug(f"Running WinSCP command with script: {script_path}")

    # Normalize the script path
    script_path = os.path.normpath(script_path)

    if not os.path.exists(script_path):
        logger.error(f"Script file '{script_path}' not found.")
        raise FileNotFoundError(f"Script file '{script_path}' not found.")

    winscp_path = os.path.normpath(os.getenv('WINSCP_PATH', 'C:\\Program Files (x86)\\WinSCP\\winscp.com'))
    winscp_log_path = os.path.normpath(os.getenv('WINSCP_LOG_PATH', './logs/winscp.log'))
   
    command = f'"{winscp_path}" /script="{script_path}" /log="{winscp_log_path}"'
    logging.debug(f"Running command: {command}")
    
    result = subprocess.run(command, capture_output=True, text=True, shell=True)

    logger.debug(f"WinSCP command output: {result.stdout}")
    if result.stderr:
        logger.error(f"WinSCP command error: {result.stderr}")
    return result.stdout, result.stderr


@log_function_call
@handle_operation_errors
def download_logs(selected_devices: List[str], download_path: str) -> None:
    """
    Downloads logs from selected devices.

    :param selected_devices: List of selected devices.
    :param download_path: Path to the local folder where logs will be downloaded.
    """
    devices_to_process = get_devices_to_process(selected_devices)

    for device in devices_to_process:
        logger.info(f"Downloading logs for device: {device['name']}")
        script_path = create_script(device, download_path=download_path, operation_type="download")

        stdout, stderr = run_winscp_command(script_path)

        if stderr:
            logger.error(f"Error downloading logs for {device['name']}: {stderr}")
        else:
            logger.info(f"Successfully downloaded logs for device {device['name']}")

        os.remove(script_path)
        logger.debug(f"Removed script file: {script_path}")


@log_function_call
@handle_operation_errors
def compare_file_versions(selected_devices: List[str], master_payload_folder: str) -> None:
    """
    Compares .iso files on devices with the master payload folder and reports outdated files.

    :param selected_devices: List of selected devices.
    :param master_payload_folder: Path to the folder containing the latest versions of .iso files.
    """
    flash_path = os.path.normpath('/mnt/flash')
    devices_to_process = get_devices_to_process(selected_devices)
    outdated_files_info = {}

    # List of master payload .iso files
    master_files = {
        file: os.path.join(master_payload_folder, file)
        for file in os.listdir(master_payload_folder)
        if file.endswith('.iso')
    }

    for device in devices_to_process:
        logger.info(f"Comparing .iso files for device: {device['name']}")
        script_path = create_script(device, remote_folder=flash_path, operation_type="get_file_versions")
        stdout, stderr = run_winscp_command(script_path)

        if stderr:
            logger.error(f"Error collecting file versions for {device['name']}: {stderr}")
            continue

        # Parse the .iso files on the device
        device_files = re.findall(r'\S+\.iso', stdout)
        logger.debug(f"Found .iso files for device {device['name']}: {device_files}")

        outdated_files = []

        # Compare device files with master payload
        for file in device_files:
            if file not in master_files:
                logger.info(f"File {file} on device {device['name']} is outdated or missing from the master payload.")
                outdated_files.append(file)

        if outdated_files:
            outdated_files_info[device['name']] = outdated_files

        os.remove(script_path)
        logger.debug(f"Removed script file: {script_path}")

    # Display outdated files to the user
    if outdated_files_info:
        display_outdated_files_to_user(outdated_files_info)
    else:
        logger.info("All files are up-to-date.")


@log_function_call
@handle_operation_errors
def update_file_versions(selected_devices: List[str], master_payload_folder: str) -> None:
    """
    Updates the .iso files on devices by deleting outdated files and uploading the latest versions.

    :param selected_devices: List of selected devices.
    :param master_payload_folder: Path to the folder containing the latest versions of .iso files.
    """
    flash_path = os.path.normpath('/mnt/flash')
    devices_to_process = get_devices_to_process(selected_devices)

    # List of master payload .iso files
    master_files = {
        file: os.path.join(master_payload_folder, file)
        for file in os.listdir(master_payload_folder)
        if file.endswith('.iso')
    }

    for device in devices_to_process:
        logger.info(f"Updating .iso files for device: {device['name']}")
        script_path = create_script(device, remote_folder=flash_path, operation_type="get_file_versions")
        stdout, stderr = run_winscp_command(script_path)

        if stderr:
            logger.error(f"Error collecting file versions for {device['name']}: {stderr}")
            continue

        # Parse the .iso files on the device
        device_files = re.findall(r'\S+\.iso', stdout)
        logger.debug(f"Found .iso files for device {device['name']}: {device_files}")

        outdated_files = []

        # Identify outdated files
        for file in device_files:
            if file not in master_files:
                logger.info(f"File {file} on device {device['name']} is outdated or missing from the master payload.")
                outdated_files.append(file)

        if outdated_files:
            # Delete outdated files
            logger.info(f"Deleting outdated files from device {device['name']}: {outdated_files}")
            delete_outdated_files(device, outdated_files)

            # Upload latest versions
            logger.info(f"Uploading latest versions to device {device['name']}")
            upload_latest_files(device, master_files)

        os.remove(script_path)
        logger.debug(f"Removed script file: {script_path}")


@log_function_call
def delete_outdated_files(device: Dict[str, str], outdated_files: List[str]) -> None:
    """
    Deletes the outdated .iso files from the device.

    :param device: The device dictionary containing connection details.
    :param outdated_files: List of outdated .iso files to delete.
    """
    remote_folder = '/mnt/flash'

    # Create a script to delete the outdated files
    delete_commands = '\n'.join([f'rm "{remote_folder}/{file}"' for file in outdated_files])
    
    script_content = f"""
    open sftp://{device['username']}:{device['password']}@{device['ip']}
    {delete_commands}
    exit
    """

    # Save and run the script
    script_path = create_script(device, operation_type="delete_files", remote_folder=remote_folder)
    with open(script_path, 'w') as script_file:
        script_file.write(script_content)
    
    run_winscp_command(script_path)
    logger.info(f"Deleted outdated files from device {device['name']}")
    os.remove(script_path)


@log_function_call
def upload_latest_files(device: Dict[str, str], master_files: Dict[str, str]) -> None:
    """
    Uploads the latest .iso files from the master payload folder to the device.

    :param device: The device dictionary containing connection details.
    :param master_files: Dictionary of .iso file names and their paths in the master payload folder.
    """
    remote_folder = '/mnt/flash'
    
    # Create a script to upload the latest files
    upload_commands = '\n'.join([f'put "{local_file}" "{remote_folder}/{file}"' for file, local_file in master_files.items()])

    script_content = f"""
    open sftp://{device['username']}:{device['password']}@{device['ip']}
    {upload_commands}
    exit
    """

    # Save and run the script
    script_path = create_script(device, operation_type="upload_files", remote_folder=remote_folder)
    with open(script_path, 'w') as script_file:
        script_file.write(script_content)

    run_winscp_command(script_path)
    logger.info(f"Uploaded latest files to device {device['name']}")
    os.remove(script_path)


@log_function_call
def display_outdated_files_to_user(outdated_files_info: Dict[str, List[str]]) -> None:
    """
    Displays the outdated files to the user via a message box.

    :param outdated_files_info: Dictionary of devices and their outdated .iso files.
    """
    message = "The following devices have outdated .iso files:\n\n"
    for device, files in outdated_files_info.items():
        message += f"{device}:\n" + "\n".join(files) + "\n\n"
    
    messagebox.showinfo("Outdated ISO Files", message)


@log_function_call
@handle_operation_errors
def nvram_reset(nvram_path: str, selected_devices: List[str]) -> None:
    """
    Resets the NVRAM for selected devices by deleting all files in the NVRAM path.

    :param nvram_path: The path to the NVRAM folder.
    :param selected_devices: The list of selected devices to reset NVRAM for.
    """
    devices_to_process = get_devices_to_process(selected_devices)

    for device in devices_to_process:
        logger.info(f"Resetting NVRAM for device: {device['name']}")
        script_path = create_script(device, remote_folder=nvram_path, operation_type="nvram_reset")
        stdout, stderr = run_winscp_command(script_path)

        if stderr:
            logger.error(f"Error resetting NVRAM for {device['name']}: {stderr}")
        else:
            logger.info(f"Successfully reset NVRAM for {device['name']}")
        
        os.remove(script_path)
        logger.debug(f"Removed script file: {script_path}")


@log_function_call
@handle_operation_errors
def nvram_demo_reset(nvram_path: str, selected_devices: List[str]) -> None:
    """
    Performs a demo reset on the NVRAM for selected devices by deleting all files except for 'Demo.dat'.

    :param nvram_path: The path to the NVRAM folder.
    :param selected_devices: The list of selected devices to demo reset NVRAM for.
    """
    devices_to_process = get_devices_to_process(selected_devices)

    for device in devices_to_process:
        logger.info(f"Running demo NVRAM reset for device: {device['name']}")
        script_path = create_script(device, remote_folder=nvram_path, operation_type="nvram_demo_reset")
        stdout, stderr = run_winscp_command(script_path)

        if stderr:
            logger.error(f"Error during demo reset for {device['name']}: {stderr}")
        else:
            logger.info(f"Successfully demo-reset NVRAM for {device['name']}")
        
        os.remove(script_path)
        logger.debug(f"Removed script file: {script_path}")
