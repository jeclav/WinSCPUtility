# WinSCP Automation Tool

## Overview
The **WinSCP Automation Tool** is a Python-based application for **SGF platform** that automates file transfers and other operations on network devices using WinSCP. It features a graphical user interface (GUI) built with Tkinter, allowing users to select devices and perform operations such as downloading logs, comparing file versions, updating firmware, and managing NVRAM.

## Features
- **Device Management**: Load device configurations from an INI file and interact with any configuration of selected devices.
- **File Operations**: Compare file versions, download logs, update file versions, on selected devices sequentially using WinSCP.
- **NVRAM Operations**: Perform regular or demo reset operations on NVRAM for selected devices.
- **Chain Operations**: Operations are que'd to run sequentially (with validation) for greater automation. 


## Project Structure
### `main.py`
The main entry point of the application, responsible for:
- Setting up the logger and environment variables.
- Initializing the GUI.
- Handling the execution of operations based on user input.

### `gui.py`
This file defines the Tkinter-based GUI:
- **Device Selection**: Allows users to select devices to operate on.
- **Operation Selection**: Users choose which operations (e.g., download logs, reset NVRAM) to perform.
- **Folder Selection**: Users can specify folders for downloads and master payloads.

### `operations.py`
Implements the core operations on devices, including:
- **Session Management**: Managing WinSCP sessions for communication with devices.
- **File Transfers**: Using WinSCP to download and update files on devices.
- **NVRAM Operations**: Reset or demo reset NVRAM.

### `validation.py`
Implements rules for operation selection validation:
- Ensures mutually exclusive operations are not selected together.
- Validates that dependent operations are selected if required.

## Installation

### Prerequisites
- Python 3.8+
- Tkinter (`pip install tk`)
- pythonnet (`pip install pythonnet`)
- python-dotenv (`pip install python-dotenv`)
- WinSCP .NET assembly (`WinSCPnet.dll`)

## Configuration
Device Configuration

Device connection details are loaded from an INI file (CONFIG_FILE). 

Each device should have a section in the following format:

```
[Device1]
ip=192.168.1.10
username=root
password=admin
```




Activate your virtual environment (if you're using one) to ensure the correct environment is being used. For example, if using venv, run:

bash
Copy code
source venv/bin/activate  # On Linux/macOS
venv\Scripts\activate     # On Windows
Install all the required libraries for your project, if you haven’t already. For example:

bash
Copy code
pip install pythonnet python-dotenv tk
Generate requirements.txt using pip by running:

bash
Copy code
pip freeze > requirements.txt