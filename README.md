# WinSCP Automation Tool

![WinSCP Automation Tool Logo](https://via.placeholder.com/800x200?text=WinSCP+Automation+Tool)

## Overview

The **WinSCP Automation Tool** is a Python-based application designed for the **SGF platform** that automates file transfers and operations on network devices using WinSCP. It features a graphical user interface (GUI) built with Tkinter, allowing users to select devices and perform operations such as downloading logs, comparing file versions, updating firmware, and managing NVRAM.


## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
  - [Component Diagram](#component-diagram)
  - [Operation Flow](#operation-flow)
  - [Class Diagram](#class-diagram)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Configuration](#configuration)
  - [Device Configuration](#device-configuration)
  - [Application Configuration](#application-configuration)
- [Usage](#usage)
  - [Starting the Application](#starting-the-application)
  - [Performing Operations](#performing-operations)
- [Project Structure](#project-structure)
- [Development](#development)
  - [Adding New Operations](#adding-new-operations)
  - [Extending Device Support](#extending-device-support)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **Device Management**: Load device configurations from an INI file and interact with any configuration of selected devices.
- **File Operations**: Compare file versions, download logs, update file versions on selected devices sequentially using WinSCP.
- **NVRAM Operations**: Perform regular or demo reset operations on NVRAM for selected devices.
- **Chain Operations**: Operations are queued to run sequentially (with validation) for greater automation.
- **Logging**: Comprehensive logging of all operations for troubleshooting.
- **Configurable**: Extensive configuration options via JSON and INI files.

## System Architecture

The WinSCP Automation Tool follows a modular architecture with clear separation of concerns:

### Component Diagram

```
┌────────────────────────────────┐     ┌─────────────────────────┐
│           User Interface       │     │     Configuration       │
│  ┌──────────────────────────┐  │     │  ┌───────────────────┐  │
│  │     WinSCPAutomationApp  │  │     │  │  ConfigManager    │  │
│  │     (Tkinter GUI)        │◄─┼─────┼──┤  (Settings)       │  │
│  └──────────────────────────┘  │     │  └───────────────────┘  │
└────────────┬───────────────────┘     └─────────────────────────┘
             │
             │ User Actions
             ▼
┌────────────────────────────────┐     ┌──────────────────────────┐
│     Operation Controller       │     │       Validation         │
│  ┌──────────────────────────┐  │     │  ┌────────────────────┐  │
│  │     run_operations()     │◄─┼─────┼──┤ validate_operations│  │
│  │     (main.py)            │  │     │  │ (Rules Checking)   │  │
│  └──────────────────────────┘  │     │  └────────────────────┘  │
└────────────┬───────────────────┘     └──────────────────────────┘
             │
             │ Execute Operations
             ▼
┌────────────────────────────────┐     ┌─────────────────────────┐
│       Operation Modules        │     │       Device Access     │
│  ┌──────────────────────────┐  │     │  ┌───────────────────┐  │
│  │  - download_logs         │◄─┼─────┼──┤  WinSCP Session   │  │
│  │  - compare_file_versions │  │     │  │  Management       │  │
│  │  - update_file_versions  │  │     │  │                   │  │
│  │  - nvram_reset           │  │     │  │                   │  │
│  │  - nvram_demo_reset      │  │     │  │                   │  │
│  └──────────────────────────┘  │     │  └───────────────────┘  │
└────────────────────────────────┘     └─────────────────────────┘
```

### Operation Flow

```
┌─────────┐     ┌────────────┐     ┌────────────┐     ┌────────────────┐
│  Start  │────►│ Select     │────►│ Choose     │────►│ Select Folders │
│  App    │     │ Devices    │     │ Operations │     │ if needed      │
└─────────┘     └────────────┘     └────────────┘     └────────────────┘
                                                                │
┌─────────┐     ┌────────────┐     ┌────────────┐               │
│  Done   │◄────│ Reboot if  │◄────│ Execute    │◄──────────────┘
│         │     │ needed     │     │ Operations │
└─────────┘     └────────────┘     └────────────┘
```

### Class Diagram

```
┌───────────────────────┐      ┌───────────────────────┐
│   ConfigManager       │      │   WinSCPAutomationApp │
├───────────────────────┤      ├───────────────────────┤
│ - config: Dict        │      │ - root: tk.Tk         │
│ - user_settings: Dict │      │ - download_path: str  │
├───────────────────────┤      │ - master_payload_path │
│ + get()               │      ├───────────────────────┤
│ + set()               │      │ + create_layout()     │
│ + get_devices()       │◄─────│ + run_operations()    │
│ + save_user_setting() │      │ + create_checkbox()   │
└───────────────────────┘      └───────────────────────┘
          ▲                              │
          │                              │
          │                              ▼
┌───────────────────────┐      ┌───────────────────────┐
│   Operations Module   │      │   Validation Module   │
├───────────────────────┤      ├───────────────────────┤
│ + download_logs()     │      │ - OPERATION_RULES     │
│ + compare_files()     │◄─────│ + validate_operations │
│ + update_files()      │      └───────────────────────┘
│ + nvram_reset()       │
│ + nvram_demo_reset()  │
└───────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- WinSCP .NET assembly (`WinSCPnet.dll`)
- Windows operating system (for WinSCP support)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/winscp-automation-tool.git
   cd winscp-automation-tool
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate your virtual environment:
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On Linux/macOS
   source venv/bin/activate
   ```

4. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

5. Ensure that `WinSCPnet.dll` is in the correct location (default is `lib/WinSCP/WinSCPnet.dll`).

## Configuration

### Device Configuration

Device connection details are loaded from an INI file (specified in your config as `paths.config_file`). 

Create a device configuration file (e.g., `config/devices.ini`) with the following format:

```ini
[Device1]
ip=192.168.1.10
username=root
password=admin

[Device2]
ip=192.168.1.11
username=root
password=admin
```

### Application Configuration

The application's default configuration is defined in `config_manager.py`. You can override these defaults by creating a JSON configuration file (default: `config/app_config.json`):

```json
{
  "paths": {
    "download_path": "C:\\DownloadedLogs",
    "master_payload_folder": "C:\\MasterPayload",
    "log_path": "logs/debug.log",
    "config_file": "./config/devices.ini",
    "nvram_path": "/mnt/nvram",
    "flash_path": "/mnt/flash",
    "local_demo_path": "./config/Demo.dat",
    "settings_file": "user_settings.ini"
  },
  "winscp": {
    "dll_path": "lib/WinSCP/WinSCPnet.dll"
  },
  "ui": {
    "window_title": "WinSCP Automation Tool",
    "window_size": "500x700"
  },
  "operations": {
    "confirm_before_reboot": true,
    "backup_before_update": true,
    "verify_after_update": true,
    "max_transfer_threads": 1
  }
}
```

## Usage

### Starting the Application

Run the main Python script to start the application:

```bash
python src/main.py
```

### Performing Operations

1. **Select Devices**: Choose one or more devices from the device list.
2. **Select Operations**: Check the operations you want to perform:
   - Compare File Versions: Compare the device's files with the master payload.
   - Download Logs: Download log files from the device.
   - Update File Versions: Update the device's files with the master payload.
   - NVRAM Reset: Reset the device's NVRAM.
   - NVRAM Demo Reset: Reset the device's NVRAM but preserve Demo.dat.
3. **Configure Folders**: Select the download folder and master payload folder as needed.
4. **Run Operations**: Click "Run Operations" to execute the selected operations.
5. **Monitor Progress**: The application will show the progress and prompt for confirmation when needed.

## Project Structure

```
winscp-automation-tool/
├── src/
│   ├── main.py              # Main entry point
│   ├── gui.py               # Tkinter GUI implementation
│   ├── operations.py        # Core operations implementation
│   ├── validation.py        # Operation validation rules
│   ├── config_manager.py    # Configuration management
│   ├── logger_setup.py      # Logging configuration
│   ├── decorators.py        # Function decorators for logging
│   └── archive.py           # Archive creation utility
├── config/
│   ├── app_config.json      # Application configuration
│   ├── devices.ini          # Device configurations
│   └── Demo.dat             # Demo file for NVRAM reset
├── lib/
│   └── WinSCP/
│       └── WinSCPnet.dll    # WinSCP .NET assembly
├── logs/                    # Log files directory
│   └── debug.log            # Default log file
├── venv/                    # Virtual environment
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Development

### Adding New Operations

1. Define the operation function in `operations.py`.
2. Add validation rules in `validation.py` by updating the `OPERATION_RULES` dictionary.
3. Add a checkbox for the operation in `gui.py`.
4. Update the `run_operations` function in `main.py` to include the new operation.


## Troubleshooting

- **Connection Issues**: Verify device IP, username, and password in the devices.ini file.
- **WinSCP DLL Not Found**: Ensure WinSCPnet.dll is in the correct location specified in your config.
- **Operation Failures**: Check the log file (default: logs/debug.log) for detailed error information.
- **GUI Issues**: If the GUI fails to start, check for conflicting Tkinter packages.

