import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pypaya_python_tools import CondaPackageManager, PackageManagerError


@pytest.fixture
def conda_manager():
    return CondaPackageManager()


class TestCondaPackageManager:
    @patch("subprocess.run")
    def test_install(self, mock_run, conda_manager):
        mock_run.return_value = MagicMock(stdout="Package installed successfully")

        conda_manager.install("package_name", "1.0.0")
        mock_run.assert_called_once_with(
            ["conda", "install", "-y", "package_name=1.0.0"],
            check=True, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_install_error(self, mock_run, conda_manager):
        mock_run.side_effect = subprocess.CalledProcessError(1, "conda install", stderr="Installation failed")

        with pytest.raises(PackageManagerError, match="Conda command failed: Installation failed"):
            conda_manager.install("package_name")

    @patch("subprocess.run")
    def test_uninstall(self, mock_run, conda_manager):
        mock_run.return_value = MagicMock(stdout="Package uninstalled successfully")

        conda_manager.uninstall("package_name")
        mock_run.assert_called_once_with(
            ["conda", "remove", "-y", "package_name"],
            check=True, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_update(self, mock_run, conda_manager):
        mock_run.return_value = MagicMock(stdout="Package updated successfully")

        conda_manager.update("package_name")
        mock_run.assert_called_once_with(
            ["conda", "update", "-y", "package_name"],
            check=True, capture_output=True, text=True
        )

    @patch("subprocess.run")
    def test_list_installed(self, mock_run, conda_manager):
        mock_run.return_value = MagicMock(stdout="\n".join([
            "# packages in environment at /path/to/env:",
            "#",
            "# Name                    Version                   Build  Channel",
            "package1                   1.0.0                    py38_0    conda-forge",
            "package2                   2.0.0                    py38_0    conda-forge",
        ]))

        result = conda_manager.list_installed()
        assert result == ["package1", "package2"]
        mock_run.assert_called_once_with(
            ["conda", "list"],
            check=True, capture_output=True, text=True
        )
