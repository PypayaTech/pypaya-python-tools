from typing import List, Optional
import subprocess
import sys
import re


class PackageManagerError(Exception):
    pass


class PackageManager:
    @staticmethod
    def _run_pip_command(*args: str) -> str:
        """Run a pip command and return its output."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", *args],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise PackageManagerError(f"Pip command failed: {e.stderr}")

    @staticmethod
    def _run_conda_command(*args: str) -> str:
        """Run a conda command and return its output."""
        try:
            result = subprocess.run(
                ["conda", *args],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise PackageManagerError(f"Conda command failed: {e.stderr}")

    @staticmethod
    def _validate_version(version: str) -> bool:
        """Validate version string format."""
        pattern = r'^\d+(\.\d+)*([a-zA-Z]+\d*)?$'
        return bool(re.match(pattern, version))

    @staticmethod
    def install(package_name: str, version: Optional[str] = None, manager: str = "pip") -> None:
        """
        Install a package using specified package manager.

        Args:
            package_name: Name of the package to install
            version: Optional version specification
            manager: Package manager to use ('pip' or 'conda')

        Raises:
            PackageManagerError: If installation fails
            ValueError: If manager type is invalid or version format is invalid
        """
        if version and not PackageManager._validate_version(version):
            raise ValueError(f"Invalid version format: {version}")

        package_spec = f"{package_name}=={version}" if version else package_name

        if manager == "pip":
            PackageManager._run_pip_command("install", package_spec)
        elif manager == "conda":
            PackageManager._run_conda_command("install", "-y", package_spec)
        else:
            raise ValueError(f"Unsupported package manager: {manager}")

    @staticmethod
    def install_multiple(packages: List[str], manager: str = "pip") -> None:
        """
        Install multiple packages in a single command.

        Args:
            packages: List of package names to install
            manager: Package manager to use ('pip' or 'conda')

        Raises:
            PackageManagerError: If installation fails
            ValueError: If manager type is invalid
        """
        if not packages:
            return

        if manager == "pip":
            PackageManager._run_pip_command("install", *packages)
        elif manager == "conda":
            PackageManager._run_conda_command("install", "-y", *packages)
        else:
            raise ValueError(f"Unsupported package manager: {manager}")

    @staticmethod
    def update(package_name: Optional[str] = None, manager: str = "pip") -> None:
        """
        Update a specific package or all packages.

        Args:
            package_name: Name of the package to update, if None - updates all packages
            manager: Package manager to use ('pip' or 'conda')

        Raises:
            PackageManagerError: If update fails
            ValueError: If manager type is invalid
        """
        if manager == "pip":
            if package_name:
                PackageManager._run_pip_command("install", "--upgrade", package_name)
            else:
                # Get list of outdated packages
                output = PackageManager._run_pip_command("list", "--outdated", "--format=json")
                import json
                outdated = json.loads(output)
                if outdated:
                    packages = [pkg["name"] for pkg in outdated]
                    PackageManager._run_pip_command("install", "--upgrade", *packages)
        elif manager == "conda":
            if package_name:
                PackageManager._run_conda_command("update", "-y", package_name)
            else:
                PackageManager._run_conda_command("update", "-y", "--all")
        else:
            raise ValueError(f"Unsupported package manager: {manager}")

    @staticmethod
    def uninstall(package_name: str, manager: str = "pip") -> None:
        """
        Uninstall a package.

        Args:
            package_name: Name of the package to uninstall
            manager: Package manager to use ('pip' or 'conda')

        Raises:
            PackageManagerError: If uninstallation fails
            ValueError: If manager type is invalid
        """
        if manager == "pip":
            PackageManager._run_pip_command("uninstall", "-y", package_name)
        elif manager == "conda":
            PackageManager._run_conda_command("remove", "-y", package_name)
        else:
            raise ValueError(f"Unsupported package manager: {manager}")

    @staticmethod
    def list_installed(manager: str = "pip") -> List[str]:
        """
        List all installed packages.

        Args:
            manager: Package manager to use ('pip' or 'conda')

        Returns:
            List of installed package names

        Raises:
            PackageManagerError: If listing fails
            ValueError: If manager type is invalid
        """
        if manager == "pip":
            output = PackageManager._run_pip_command("list", "--format=json")
            import json
            packages = json.loads(output)
            return [pkg["name"] for pkg in packages]
        elif manager == "conda":
            output = PackageManager._run_conda_command("list", "--json")
            import json
            packages = json.loads(output)
            return [pkg["name"] for pkg in packages]
        else:
            raise ValueError(f"Unsupported package manager: {manager}")
