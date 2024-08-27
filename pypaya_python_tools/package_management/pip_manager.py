import subprocess
import sys
from typing import List, Optional
from .base import PackageManager
from .exceptions import PackageManagerError


class PipPackageManager(PackageManager):
    def _run_pip_command(self, *args: str) -> str:
        """
        Run a pip command and return its output.

        Args:
            *args: Command arguments to pass to pip.

        Returns:
            str: The command output.

        Raises:
            PackageManagerError: If the command execution fails.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip"] + list(args),
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise PackageManagerError(f"Pip command failed: {e.stderr}")

    def install(self, package_name: str, version: Optional[str] = None) -> None:
        package_spec = f"{package_name}=={version}" if version else package_name
        self._run_pip_command("install", package_spec)

    def uninstall(self, package_name: str) -> None:
        self._run_pip_command("uninstall", "-y", package_name)

    def update(self, package_name: str) -> None:
        self._run_pip_command("install", "--upgrade", package_name)

    def list_installed(self) -> List[str]:
        output = self._run_pip_command("list", "--format=freeze")
        return [line.split("==")[0] for line in output.split("\n") if line]
