# WinSCP Automation Tool

The **WinSCP Automation Tool** is a Python-based application designed to automate file transfer tasks with WinSCP using a simple graphical user interface (GUI). The tool allows users to manage device operations such as downloading logs and performing specific tasks like DemoNvramReset and NvramReset. It supports multiple devices through a configuration file (`devices.ini`) and allows the user to define download paths that persist between sessions.

## Features
- **Device Management**: Define devices in `devices.ini` for quick access.
- **File Operations**: Automate downloading logs and performing custom operations like `DemoNvramReset` and `NvramReset`.
- **GUI Controls**: Checkboxes allow you to select operations to execute.
- **Folder Selection**: Choose a folder for downloading files, with the path saved for future sessions.
- **Logging**: Detailed logs of actions and errors for troubleshooting.

## Project Structure
WinSCPAutomation/
├── config/
│   └── devices.ini           # Configuration file for device information
├── logs/
│   └── activity.log          # Log file generated during execution
├── scripts/                  # (Optional) Directory for generated WinSCP script files
├── src/
│   ├── main.py               # Main entry point of the application
│   ├── gui.py                # GUI logic with Tkinter
│   └── utils.py              # (Optional) Helper functions for file and operation handling
├── user_settings.ini         # User settings, stores persistent values like download paths
└── README.md                 # Documentation for the project

## Installation and Setup

### Prerequisites
- Python 3.6+
- WinSCP installed and added to the system PATH
- Required Python packages: `tkinter`, `configparser`, `logging`, and `PyInstaller` (for creating an executable)

### Step 1: Install Dependencies
Install the necessary Python packages:
pip install pyinstaller
Note: tkinter is a built-in Python library and doesn't need separate installation.

### Step 2: Configuration
Configure your devices: Create the devices.ini file inside the config/ directory with the following format:


#### devices.ini
[G920-1]
ip = 192.168.0.10
username = admin
password = pass123

[G920-2]
ip = 192.168.0.11
username = user1
password = pass456
Initial Setup: Ensure the user_settings.ini file exists in the project root to store your download path.

## Usage
Running the Application
Start the application by running main.py:
python src/main.py


Creating an Executable
To create a standalone executable, use PyInstaller:


pyinstaller --onefile --noconsole --add-data "src/config/devices.ini;config" --add-data "src/user_settings.ini;." src/main.py
The executable will be generated in the dist/ folder.

Log Files
All application logs are saved in logs/activity.log.
Logs provide detailed information about the application's actions, errors, and user interactions.
Troubleshooting
Cannot find devices.ini: Ensure that the devices.ini file is located in the config/ directory.
WinSCP not recognized: Make sure winscp.com is installed and added to the system PATH.
Contributing
If you'd like to contribute, feel free to submit pull requests or report issues.

## License
This project is licensed under the MIT License.


## Notes:
- **Commands**: Use the PyInstaller command exactly as shown to ensure the necessary files are included when creating an executable.
- **Device Configuration**: Ensure `devices.ini` follows the expected format for smooth operation.
- **Logging**: Logs are crucial for understanding the application’s execution flow, especially when troubleshooting.




