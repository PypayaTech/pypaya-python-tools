import subprocess
import pytest
from unittest.mock import patch, Mock
from pypaya_python_tools.package_management import PackageManager, PackageManagerError


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            stdout="Success",
            stderr="",
            returncode=0
        )
        yield mock_run


def test_install_package(mock_subprocess_run):
    PackageManager.install("numpy")
    mock_subprocess_run.assert_called_once()
    args = mock_subprocess_run.call_args[0][0]
    assert "pip" in args
    assert "install" in args
    assert "numpy" in args


def test_install_package_with_version(mock_subprocess_run):
    PackageManager.install("numpy", version="1.21.0")
    args = mock_subprocess_run.call_args[0][0]
    assert "numpy==1.21.0" in " ".join(args)


def test_install_package_with_invalid_version():
    with pytest.raises(ValueError):
        PackageManager.install("numpy", version="invalid.version")


def test_install_package_with_invalid_manager():
    with pytest.raises(ValueError):
        PackageManager.install("numpy", manager="invalid")


def test_install_multiple_packages(mock_subprocess_run):
    PackageManager.install_multiple(["numpy", "pandas"])
    args = mock_subprocess_run.call_args[0][0]
    assert "numpy" in args
    assert "pandas" in args


def test_update_specific_package(mock_subprocess_run):
    PackageManager.update("numpy")
    args = mock_subprocess_run.call_args[0][0]
    assert "pip" in args
    assert "--upgrade" in args
    assert "numpy" in args


def test_update_all_packages(mock_subprocess_run):
    outdated_json = '[{"name": "numpy"}, {"name": "pandas"}]'

    # Configure mock to return different responses for different commands
    def mock_run_side_effect(*args, **kwargs):
        if "--outdated" in args[0]:
            # Return list of outdated packages when checking
            return Mock(stdout=outdated_json, stderr="", returncode=0)
        # Return success for the update command
        return Mock(stdout="Success", stderr="", returncode=0)

    mock_subprocess_run.side_effect = mock_run_side_effect

    PackageManager.update()

    assert mock_subprocess_run.call_count == 2

    upgrade_call = mock_subprocess_run.call_args
    upgrade_args = upgrade_call[0][0]
    assert "--upgrade" in upgrade_args
    assert "numpy" in upgrade_args
    assert "pandas" in upgrade_args


def test_update_failure(mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, [], stderr="Update failed"
    )
    with pytest.raises(PackageManagerError):
        PackageManager.update("numpy")


def test_uninstall_package(mock_subprocess_run):
    PackageManager.uninstall("numpy")
    args = mock_subprocess_run.call_args[0][0]
    assert "uninstall" in args
    assert "numpy" in args


def test_command_failure(mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        1, [], stderr="Error message"
    )
    with pytest.raises(PackageManagerError):
        PackageManager.install("numpy")


@pytest.mark.parametrize("version,is_valid", [
    ("1.0.0", True),
    ("1.0.0rc1", True),
    ("1.0", True),
    ("invalid", False),
    ("1.0.?", False),
])
def test_version_validation(version, is_valid):
    assert PackageManager._validate_version(version) == is_valid


def test_list_installed(mock_subprocess_run):
    mock_subprocess_run.return_value.stdout = '[{"name": "numpy"}, {"name": "pandas"}]'
    packages = PackageManager.list_installed()
    assert "numpy" in packages
    assert "pandas" in packages
