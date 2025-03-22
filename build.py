import os
import subprocess
import shutil
import sys
import venv
from pathlib import Path

def create_and_use_venv():
    """Create a dedicated virtual environment for building"""
    venv_dir = "build_venv"
    print(f"Creating virtual environment in {venv_dir}...")
    
    # Create the virtual environment
    venv.create(venv_dir, with_pip=True)
    
    # Determine the path to the Python executable in the virtual environment
    if os.name == 'nt':  # Windows
        python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
    else:  # Unix/Linux/MacOS
        python_executable = os.path.join(venv_dir, "bin", "python")
    
    # Install dependencies in the virtual environment
    print("Installing dependencies in virtual environment...")
    subprocess.check_call([python_executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([python_executable, "-m", "pip", "install", "pyinstaller"])
    
    print(f"Virtual environment created and dependencies installed in {venv_dir}")
    return python_executable

def clean_build_dirs():
    """Remove previous build artifacts"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    print("Cleaned previous build directories")

def copy_resources():
    """Copy necessary resource files to the dist directory"""
    # Create required directories
    os.makedirs("dist/WinSCPAutomation/config", exist_ok=True)
    os.makedirs("dist/WinSCPAutomation/lib/WinSCP", exist_ok=True)
    os.makedirs("dist/WinSCPAutomation/logs", exist_ok=True)
    
    # Copy config files
    print("Copying configuration files...")
    if os.path.exists("config/app_config.json"):
        shutil.copy("config/app_config.json", "dist/WinSCPAutomation/config/")
    else:
        print("WARNING: app_config.json not found!")
        
    if os.path.exists("config/devices.ini"):
        shutil.copy("config/devices.ini", "dist/WinSCPAutomation/config/")
    else:
        print("WARNING: devices.ini not found!")
        
    if os.path.exists("config/Demo.dat"):
        shutil.copy("config/Demo.dat", "dist/WinSCPAutomation/config/")
    else:
        print("WARNING: Demo.dat not found!")
    
    # Copy WinSCP DLL
    print("Copying WinSCP DLL...")
    winscp_dll = "lib/WinSCP/WinSCPnet.dll"
    if os.path.exists(winscp_dll):
        shutil.copy(winscp_dll, "dist/WinSCPAutomation/lib/WinSCP/")
    else:
        print(f"WARNING: {winscp_dll} not found! You need to add it manually.")
    
    # Create placeholder for logs
    with open("dist/WinSCPAutomation/logs/.gitkeep", "w") as f:
        f.write("# Placeholder for log files")
    
    # Copy README and licenses
    if os.path.exists("README.md"):
        shutil.copy("README.md", "dist/WinSCPAutomation/")
    
    # Copy requirements.txt for reference
    if os.path.exists("requirements.txt"):
        shutil.copy("requirements.txt", "dist/WinSCPAutomation/")
    
    # Copy icon if it exists
    if os.path.exists("resources/icon.ico"):
        os.makedirs("dist/WinSCPAutomation/resources", exist_ok=True)
        shutil.copy("resources/icon.ico", "dist/WinSCPAutomation/resources/")
    
    print("Resource files copied successfully")

def create_resources_dir():
    """Create resources directory if it doesn't exist"""
    if not os.path.exists("resources"):
        os.makedirs("resources", exist_ok=True)
        print("Created resources directory")

def check_for_icon():
    """Check if icon exists, if not create a placeholder message"""
    icon_path = "resources/icon.ico"
    if not os.path.exists(icon_path):
        print(f"WARNING: Icon file {icon_path} not found!")
        print("If you haven't created an icon yet, please create one and place it at resources/icon.ico")
        print("The build will continue with a default icon.")
        
        # Create resources directory if it doesn't exist
        create_resources_dir()
        
        # Create a text file with instructions
        with open("resources/ICON_MISSING.txt", "w") as f:
            f.write("Please create an icon.ico file and place it in this directory.\n")
            f.write("The icon will be used for the application executable.\n")

def build_executable(python_executable):
    """Build the executable using PyInstaller in the virtual environment"""
    # Clean previous builds
    clean_build_dirs()
    
    # Check for icon
    check_for_icon()
    
    # Determine icon path - use it if it exists, otherwise let PyInstaller use default
    icon_param = []
    if os.path.exists("resources/icon.ico"):
        icon_param = ["--icon=resources/icon.ico"]
    
    # Build the command
    cmd = [
        python_executable,
        "-m",
        "PyInstaller",
        "--name=WinSCPAutomation",
        "--windowed",
        "--noconfirm",
        "--add-data=config;config" if os.name == 'nt' else "--add-data=config:config",
        "--add-data=lib;lib" if os.name == 'nt' else "--add-data=lib:lib",
    ]
    
    # Add icon parameter if available
    if icon_param:
        cmd.extend(icon_param)
    
    # Add the main script
    cmd.append("src/main.py")
    
    print("Running PyInstaller to create executable...")
    print(f"Command: {' '.join(cmd)}")
    subprocess.call(cmd)
    
    # Copy additional resources
    copy_resources()
    
    print("Build completed. Executable is in the dist/WinSCPAutomation directory.")

def create_distribution_zip():
    """Create a zip file of the distribution"""
    import zipfile
    
    dist_dir = "dist/WinSCPAutomation"
    output_zip = "dist/WinSCPAutomation.zip"
    
    if os.path.exists(dist_dir):
        print(f"Creating distribution zip file: {output_zip}")
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "dist")
                    zipf.write(file_path, arcname)
        
        print(f"Distribution zip file created: {output_zip}")
    else:
        print(f"ERROR: Distribution directory {dist_dir} not found. Zip file not created.")

def main():
    """Main build function"""
    print("Starting build process for WinSCP Automation Tool...")
    
    # Ensure requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("ERROR: requirements.txt not found. Please create it before building.")
        sys.exit(1)
    
    try:
        # Create virtual environment and get its Python executable
        python_executable = create_and_use_venv()
        
        # Build the executable
        build_executable(python_executable)
        
        # Create distribution zip
        create_distribution_zip()
        
        print("\nBuild process completed successfully!")
        print("You can find the executable in the dist/WinSCPAutomation directory")
        print("A zip distribution is available at dist/WinSCPAutomation.zip")
        
    except Exception as e:
        print(f"ERROR: Build process failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()