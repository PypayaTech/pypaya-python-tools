import pytest
import sys
import subprocess
from unittest.mock import patch, MagicMock
from pypaya_python_tools.package_management import PipPackageManager, PackageManagerError


@pytest.fixture
def pip_manager():
    return PipPackageManager()


class TestPipPackageManager:
    @patch("subprocess.run")
    def test_install(self, mock_run, pip_manager):
        mock_run.return_value = MagicMock(stdout="Package installed successfully")

        pip_manager.install("package_name", "1.0.0")
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "pip", "install", "package_name==1.0.0"],
            check=True, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_install_error(self, mock_run, pip_manager):
        mock_run.side_effect = subprocess.CalledProcessError(1, "pip install", stderr="Installation failed")

        with pytest.raises(PackageManagerError, match="Pip command failed: Installation failed"):
            pip_manager.install("package_name")

    @patch("subprocess.run")
    def test_uninstall(self, mock_run, pip_manager):
        mock_run.return_value = MagicMock(stdout="Package uninstalled successfully")

        pip_manager.uninstall("package_name")
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "pip", "uninstall", "-y", "package_name"],
            check=True, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_update(self, mock_run, pip_manager):
        mock_run.return_value = MagicMock(stdout="Package updated successfully")

        pip_manager.update("package_name")
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "pip", "install", "--upgrade", "package_name"],
            check=True, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_list_installed(self, mock_run, pip_manager):
        mock_run.return_value = MagicMock(stdout="package1==1.0.0\npackage2==2.0.0\n")

        result = pip_manager.list_installed()
        assert result == ["package1", "package2"]
        mock_run.assert_called_once_with(
            [sys.executable, "-m", "pip", "list", "--format=freeze"],
            check=True, capture_output=True, text=True
        )
