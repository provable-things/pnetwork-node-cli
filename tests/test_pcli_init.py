import responses
import unittest
from unittest.mock import patch
import sys
sys.path.append('../')
from utils import check_for_file_in_path, download_file
from client_config import CLI_CONFIG


class TestFileInPath(unittest.TestCase):

    @patch('os.path.isfile')
    def test_file_in_path_true(self, mock_os_is_file):
        mock_os_is_file.return_value = True
        assert check_for_file_in_path('terraform', f'{CLI_CONFIG["pcli_config_path"]}') == True

    @patch('os.path.isfile')
    def test_file_in_path_false(self, mock_os_is_file):
        mock_os_is_file.return_value = False
        assert check_for_file_in_path('terraform', f'{CLI_CONFIG["pcli_config_path"]}') == False

class TestDownloadFile(unittest.TestCase):

    def test_download_file_succeed(self):
        assert download_file(CLI_CONFIG['tf_binary_url_linux']) == 200


if __name__ == '__main__':
    unittest.main(verbosity=2)
