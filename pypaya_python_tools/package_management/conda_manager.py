import subprocess
import sys
from typing import List, Optional
from .base import PackageManager
from .exceptions import PackageManagerError


class CondaPackageManager(PackageManager):
    def _run_conda_command(self, *args: str) -> str:
        """
        Run a conda command and return its output.

        Args:
            *args: Command arguments to pass to conda.

        Returns:
            str: The command output.

        Raises:
            PackageManagerError: If the command execution fails.
        """
        try:
            result = subprocess.run(
                ["conda"] + list(args),
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise PackageManagerError(f"Conda command failed: {e.stderr}")

    def install(self, package_name: str, version: Optional[str] = None) -> None:
        package_spec = f"{package_name}={version}" if version else package_name
        self._run_conda_command("install", "-y", package_spec)

    def uninstall(self, package_name: str) -> None:
        self._run_conda_command("remove", "-y", package_name)

    def update(self, package_name: str) -> None:
        self._run_conda_command("update", "-y", package_name)

    def list_installed(self) -> List[str]:
        output = self._run_conda_command("list")
        return [line.split()[0] for line in output.split("\n")[3:] if line.strip()]
