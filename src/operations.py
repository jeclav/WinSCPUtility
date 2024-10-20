# src/operations.py
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
    remote_folder: str,
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
    remote_folder = remote_folder.replace('\\', '/')
    script_dir = os.path.normpath(os.getenv('WINSCP_SCRIPT_DIR', './scripts'))

    # Construct different scripts based on the operation type
    if operation_type == "download":
        # Ensure download path is provided for the download operation
        if not download_path:
            logger.error("download_path is required for the download operation")
            raise ValueError("download_path is required for the download operation")
        
        # download_path = os.path.normpath(download_path)
        download_path = os.path.join(os.path.normpath(download_path),f"{device['name']}.txt")
        logger.debug(f"Downloading logs from: {device['name']} to: {download_path}")
        
        script_content = f"""
            open sftp://{device['username']}:{device['password']}@{device['ip']}
            lcd "{download_path}"
            cd /tmp
            get logs
            cd /mnt
            get log
            exit
            """
    elif operation_type == "nvram_reset":
        script_content = f"""
open sftp://{device['username']}:{device['password']}@{device['ip']}
rm "{remote_folder}/*"
exit
"""
    elif operation_type == "nvram_demo_reset":
        script_content = f"""
open sftp://{device['username']}:{device['password']}@{device['ip']}
# Delete all files except 'Demo.dat' in the remote folder
call find "{remote_folder}" -type f ! -name "Demo.dat" -exec rm {{}} \\;
exit
"""
    elif operation_type == "get_file_versions":
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

    winscp_path = os.path.normpath(os.getenv('WINSCP_PATH', 'C:\Program Files (x86)\WinSCP\winscp.com'))
    winscp_log_path = os.path.normpath(os.getenv('WINSCP_LOG_PATH', "./logs/winscp_.log"))
   
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
    Downloads logs from both MNT and TMP paths for selected devices.

    :param selected_devices: List of selected devices.
    :param download_path: Path to the local folder where logs will be downloaded.
    """
    # mnt_log_path = os.path.normpath(os.getenv('MNT_LOG_PATH', '/mnt/logs'))
    tmp_log_path = os.path.normpath(os.getenv('TMP_LOG_PATH', '/tmp/logs'))

    devices_to_process = get_devices_to_process(selected_devices)

    for device in devices_to_process:
        logger.info(f"Downloading logs for device: {device['name']}")

        # Download from both mnt & tmp
        script_path = create_script(device,tmp_log_path,download_path, operation_type="download") # clean up positional arguements: tmp and mnt path not required

        stdout, stderr = run_winscp_command(script_path)

        if stderr:
            logger.error(f"Error downloading logs for {device['name']} from MNT path: {stderr}")
        else:
            logger.info(f"Successfully downloaded logs for device {device['name']} from MNT path")

        os.remove(script_path)
        logger.debug(f"Removed script file: {script_path}")


@log_function_call
@handle_operation_errors
def get_file_versions(selected_devices: List[str]) -> Dict[str, List[str]]:
    """
    Collects a list of all the .iso files contained within the /mnt/flash path for each selected device.

    :param selected_devices: List of selected devices.
    :return: Dictionary of devices and their .iso files.
    """
    flash_path = os.path.normpath('/mnt/flash')

    devices_to_process = get_devices_to_process(selected_devices)

    file_versions: Dict[str, List[str]] = {}

    for device in devices_to_process:
        logger.info(f"Collecting file versions for device: {device['name']}")
        script_path = create_script(device, flash_path, operation_type="get_file_versions")
        stdout, stderr = run_winscp_command(script_path)

        if stderr:
            logger.error(f"Error collecting file versions for {device['name']}: {stderr}")
            file_versions[device['name']] = []
        else:
            # iso_files = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
            # file_versions[device['name']] = iso_files
            # logger.info(f"Found .iso files for device {device['name']}: {iso_files}")
            iso_files = re.findall(r'\S+\.iso',stdout)
            file_versions[device['name']] = iso_files
            logger.info(f"Found .iso files for device {device['name']}: {iso_files}")

        os.remove(script_path)
        logger.debug(f"Removed script file: {script_path}")

    return file_versions

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
        script_path = create_script(device, nvram_path, operation_type="nvram_reset")
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
        script_path = create_script(device, nvram_path, operation_type="nvram_demo_reset")
        stdout, stderr = run_winscp_command(script_path)

        if stderr:
            logger.error(f"Error during demo reset for {device['name']}: {stderr}")
        else:
            logger.info(f"Successfully demo-reset NVRAM for {device['name']}")
        os.remove(script_path)
        logger.debug(f"Removed script file: {script_path}")
