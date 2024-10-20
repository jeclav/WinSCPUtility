import sys
import os
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import unittest
from unittest.mock import patch, mock_open, MagicMock
import operations
from logger_setup import setup_logger

# Initialize the logger for the test file
logger = setup_logger('TestOperations')

class TestOperations(unittest.TestCase):

    @patch('operations.load_devices')
    @patch('operations.run_winscp_command')
    @patch('operations.create_script')
    @patch('os.remove')
    def test_download_logs_success(self, mock_os_remove, mock_create_script, mock_run_winscp_command, mock_load_devices):
        logger.debug("Starting test: test_download_logs_success")

        # Mock environment variables
        with patch.dict(os.environ, {
            'MNT_LOG_PATH': '/mnt/logs',
            'TMP_LOG_PATH': '/tmp/logs',
            'CONFIG_FILE': './config/devices.ini'
        }):
            logger.debug("Environment variables patched")

            # Mock devices
            mock_load_devices.return_value = [
                {'name': 'device1', 'ip': '192.168.1.1', 'username': 'user', 'password': 'pass'}
            ]
            mock_create_script.return_value = '/fake/path/script.txt'
            mock_run_winscp_command.return_value = ('Success', '')

            # Call download_logs
            selected_devices = ['device1']
            download_path = '/downloads'
            operations.download_logs(selected_devices, download_path)

            # Assertions with normalized paths for both /mnt/logs and /tmp/logs
            expected_calls = [
                unittest.mock.call(mock_load_devices.return_value[0], os.path.normpath('/mnt/logs'), download_path, operation_type='download'),
                unittest.mock.call(mock_load_devices.return_value[0], os.path.normpath('/tmp/logs'), download_path, operation_type='download')
            ]
            mock_create_script.assert_has_calls(expected_calls, any_order=True)
            mock_run_winscp_command.assert_called_with('/fake/path/script.txt')
            mock_os_remove.assert_called_with('/fake/path/script.txt')

    @patch('operations.load_devices')
    @patch('operations.run_winscp_command')
    @patch('operations.create_script')
    @patch('os.remove')
    def test_download_logs_failure(self, mock_os_remove, mock_create_script, mock_run_winscp_command, mock_load_devices):
        logger.debug("Starting test: test_download_logs_failure")

        # Mock environment variables
        with patch.dict(os.environ, {
            'MNT_LOG_PATH': '/mnt/logs',
            'TMP_LOG_PATH': '/tmp/logs',
            'CONFIG_FILE': './config/devices.ini'
        }):
            logger.debug("Environment variables patched")

            # Mock devices
            mock_load_devices.return_value = [
                {'name': 'device1', 'ip': '192.168.1.1', 'username': 'user', 'password': 'pass'}
            ]
            mock_create_script.return_value = '/fake/path/script.txt'
            mock_run_winscp_command.return_value = ('', 'Error')

            # Call download_logs
            selected_devices = ['device1']
            download_path = '/downloads'
            operations.download_logs(selected_devices, download_path)

            # Assertions with normalized paths for both /mnt/logs and /tmp/logs
            expected_calls = [
                unittest.mock.call(mock_load_devices.return_value[0], os.path.normpath('/mnt/logs'), download_path, operation_type='download'),
                unittest.mock.call(mock_load_devices.return_value[0], os.path.normpath('/tmp/logs'), download_path, operation_type='download')
            ]
            mock_create_script.assert_has_calls(expected_calls, any_order=True)
            mock_run_winscp_command.assert_called_with('/fake/path/script.txt')
            mock_os_remove.assert_called_with('/fake/path/script.txt')

    @patch('os.path.exists', return_value=False)
    def test_load_devices_missing_config(self, mock_exists):
        logger.debug("Starting test: test_load_devices_missing_config")
        with self.assertRaises(FileNotFoundError):
            operations.load_devices('fake_config.ini')

    @patch('os.path.exists', return_value=True)
    @patch('configparser.ConfigParser.read', return_value=None)
    def test_load_devices_missing_fields(self, mock_exists, mock_config_read):
        logger.debug("Starting test: test_load_devices_missing_fields")

        mock_config_parser = MagicMock()
        mock_config_parser.sections.return_value = ['device1']
        mock_config_parser.__getitem__.side_effect = KeyError  # Simulate missing fields

        with patch('configparser.ConfigParser', return_value=mock_config_parser):
            devices = operations.load_devices('fake_config.ini')
            self.assertEqual(devices, [])  # Expect no devices to be loaded due to missing fields

@patch('operations.run_winscp_command')
@patch('operations.create_script')
@patch('operations.load_devices')
@patch('os.remove')
def test_nvram_reset(self, mock_os_remove, mock_load_devices, mock_create_script, mock_run_winscp_command):
    logger.debug("Starting test: test_nvram_reset")

    # Mock devices returned by load_devices
    mock_load_devices.return_value = [
        {'name': 'device1', 'ip': '192.168.1.1', 'username': 'user', 'password': 'pass'},
        {'name': 'device2', 'ip': '192.168.1.2', 'username': 'user2', 'password': 'pass2'}
    ]

    # Mock successful script creation and command execution
    mock_create_script.return_value = '/fake/path/script.txt'
    mock_run_winscp_command.return_value = ('Success', '')

    nvram_path = '/mnt/nvram'
    selected_devices = ['device1', 'device2']

    # Call nvram_reset
    operations.nvram_reset(nvram_path, selected_devices)

    # Check if the correct scripts were created and run for both devices
    expected_calls = [
        unittest.mock.call({'name': 'device1', 'ip': '192.168.1.1', 'username': 'user', 'password': 'pass'}, nvram_path, operation_type='nvram_reset'),
        unittest.mock.call({'name': 'device2', 'ip': '192.168.1.2', 'username': 'user2', 'password': 'pass2'}, nvram_path, operation_type='nvram_reset')
    ]
    mock_create_script.assert_has_calls(expected_calls, any_order=True)
    mock_run_winscp_command.assert_called_with('/fake/path/script.txt')
    mock_os_remove.assert_called_with('/fake/path/script.txt')


    @patch('operations.run_winscp_command')
    @patch('operations.create_script')
    @patch('operations.load_devices')
    @patch('os.remove')
    def test_nvram_demo_reset(self, mock_os_remove, mock_load_devices, mock_create_script, mock_run_winscp_command):
        logger.debug("Starting test: test_nvram_demo_reset")

        # Mock devices returned by load_devices
        mock_load_devices.return_value = [
            {'name': 'device1', 'ip': '192.168.1.1', 'username': 'user', 'password': 'pass'},
            {'name': 'device2', 'ip': '192.168.1.2', 'username': 'user2', 'password': 'pass2'}
        ]

        # Mock successful script creation and command execution
        mock_create_script.return_value = '/fake/path/script.txt'
        mock_run_winscp_command.return_value = ('Success', '')

        nvram_path = '/mnt/nvram'
        selected_devices = ['device1', 'device2']

        # Call nvram_demo_reset
        operations.nvram_demo_reset(nvram_path, selected_devices)

        # Check if the correct scripts were created and run for both devices
        expected_calls = [
            unittest.mock.call({'name': 'device1', 'ip': '192.168.1.1', 'username': 'user', 'password': 'pass'}, nvram_path, operation_type='nvram_demo_reset'),
            unittest.mock.call({'name': 'device2', 'ip': '192.168.1.2', 'username': 'user2', 'password': 'pass2'}, nvram_path, operation_type='nvram_demo_reset')
        ]
        mock_create_script.assert_has_calls(expected_calls, any_order=True)
        mock_run_winscp_command.assert_called_with('/fake/path/script.txt')
        mock_os_remove.assert_called_with('/fake/path/script.txt')


    @patch('os.remove')
    @patch('operations.run_winscp_command')
    @patch('operations.create_script')
    @patch('operations.load_devices')
    def test_get_device_file_versions(self, mock_load_devices, mock_create_script, mock_run_winscp_command, mock_os_remove):
        logger.debug("Starting test: test_get_device_file_versions")

        # Mock environment variables
        with patch.dict(os.environ, {
            'CONFIG_FILE': './config/devices.ini'
        }):
            logger.debug("Environment variables patched")

            # Mock devices
            mock_load_devices.return_value = [
                {'name': 'device1', 'ip': '192.168.1.1', 'username': 'user', 'password': 'pass'}
            ]
            mock_create_script.return_value = '/fake/path/script.txt'
            mock_run_winscp_command.return_value = ('file1.iso\nfile2.iso\n', '')

            selected_devices = ['device1']
            file_versions = operations.get_device_file_versions(selected_devices)

            # Assertions for script creation and WinSCP command
            mock_create_script.assert_called_once_with(mock_load_devices.return_value[0], os.path.normpath('/mnt/flash'), operation_type='get_file_versions')
            mock_run_winscp_command.assert_called_once_with('/fake/path/script.txt')

            # Check the result
            self.assertEqual(file_versions, {'device1': ['file1.iso', 'file2.iso']})


if __name__ == '__main__':
    unittest.main()
