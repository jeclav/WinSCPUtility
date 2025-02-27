# src/config_manager.py

import os
import logging
import json
import configparser
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "paths": {
        "download_path": "C:\\DownloadedLogs",
        "master_payload_folder": "C:\\MasterPayload",
        "log_path": "logs/debug.log",
        "config_file": "./config/app_config.json",
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
        "confirm_before_reboot": True,
        "backup_before_update": True,
        "verify_after_update": True,
        "max_transfer_threads": 1
    }
}

class ConfigManager:
    """
    Centralized configuration manager for the WinSCP Automation Tool.
    Handles loading, saving, and accessing configuration values.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one config manager exists."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration manager if not already initialized."""
        if self._initialized:
            return
            
        self.config_path = os.getenv('APP_CONFIG', 'config/app_config.json')
        self.config = DEFAULT_CONFIG.copy()
        self.user_settings = {}
        
        # Load configuration
        self._load_config()
        self._load_user_settings()
        
        # Override with environment variables if present
        self._apply_env_overrides()
        
        self._initialized = True
        logger.info(f"Configuration manager initialized with config path: {self.config_path}")
    
    def _load_config(self) -> None:
        """Load configuration from the JSON config file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Update the default config with loaded values
                    self._deep_update(self.config, loaded_config)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.info(f"Configuration file {self.config_path} not found. Using defaults.")
                # Create default config file
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def _load_user_settings(self) -> None:
        """Load user settings from the settings file."""
        settings_file = self.get('paths.settings_file')
        try:
            if os.path.exists(settings_file):
                user_config = configparser.ConfigParser()
                user_config.read(settings_file)
                if user_config.has_section("Settings"):
                    self.user_settings = dict(user_config["Settings"])
                logger.info(f"User settings loaded from {settings_file}")
            else:
                logger.info(f"User settings file {settings_file} not found.")
        except Exception as e:
            logger.error(f"Error loading user settings: {e}")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to the configuration."""
        # Map of config keys to environment variable names
        env_mappings = {
            'paths.download_path': 'DOWNLOAD_PATH',
            'paths.master_payload_folder': 'MASTER_PAYLOAD_FOLDER',
            'paths.log_path': 'LOG_PATH',
            'paths.config_file': 'CONFIG_FILE',
            'paths.nvram_path': 'NVRAM_PATH',
            'paths.flash_path': 'FLASH_PATH',
            'paths.local_demo_path': 'LOCAL_DEMO_PATH',
            'winscp.dll_path': 'WINSCP_DLL_PATH'
        }
        
        for config_key, env_var in env_mappings.items():
            if env_var in os.environ:
                self.set(config_key, os.environ[env_var])
                logger.debug(f"Override {config_key} with environment variable {env_var}")
    
    def _deep_update(self, target_dict: Dict, source_dict: Dict) -> None:
        """
        Recursively update a nested dictionary with values from another dictionary.
        
        Args:
            target_dict: The dictionary to update
            source_dict: The dictionary with new values
        """
        for key, value in source_dict.items():
            if key in target_dict and isinstance(target_dict[key], dict) and isinstance(value, dict):
                self._deep_update(target_dict[key], value)
            else:
                target_dict[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value by its dot-notated path.
        
        Args:
            key_path: Dot-notated path to the configuration value (e.g., 'paths.download_path')
            default: Default value to return if the key is not found
            
        Returns:
            The configuration value or the default value if not found
        """
        keys = key_path.split('.')
        value = self.config
        
        # Try to traverse the config dictionary
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value by its dot-notated path.
        
        Args:
            key_path: Dot-notated path to the configuration value
            value: The value to set
        """
        keys = key_path.split('.')
        config_ref = self.config
        
        # Traverse to the right level in the config dictionary
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # Set the value
        config_ref[keys[-1]] = value
    
    def save_config(self) -> None:
        """Save the current configuration to the config file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get_user_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a user setting by key.
        
        Args:
            key: The setting key
            default: Default value to return if the key is not found
            
        Returns:
            The setting value or the default value if not found
        """
        return self.user_settings.get(key, default)
    
    def save_user_setting(self, key: str, value: str) -> None:
        """
        Save a user setting.
        
        Args:
            key: The setting key
            value: The value to save
        """
        self.user_settings[key] = value
        settings_file = self.get('paths.settings_file')
        
        try:
            config = configparser.ConfigParser()
            if os.path.exists(settings_file):
                config.read(settings_file)
            
            if not config.has_section("Settings"):
                config.add_section("Settings")
            
            config.set("Settings", key, value)
            
            with open(settings_file, "w") as configfile:
                config.write(configfile)
            
            logger.info(f"User setting {key} saved to {settings_file}")
        except Exception as e:
            logger.error(f"Error saving user setting: {e}")
    
    def get_devices(self) -> List[Dict[str, str]]:
        """
        Load device configurations from the devices.ini file.
        
        Returns:
            A list of dictionaries, each containing connection information for a device
        """
        config_file = os.path.normpath(self.get('paths.config_file'))
        logger.debug(f"Loading device configurations from {config_file}")
        
        if not os.path.exists(config_file):
            logger.error(f"Configuration file '{config_file}' not found.")
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
        
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
                logger.debug(f"Loaded device: {device}")
            except KeyError as e:
                logger.error(f"Missing required field {e} in device section [{device}]")
                raise ValueError(f"Missing required field {e} in device section [{device}]")
        
        return devices

# Create a global instance
config_manager = ConfigManager()