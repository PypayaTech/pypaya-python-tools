import abc
from typing import List, Optional


class PackageManager(abc.ABC):
    @abc.abstractmethod
    def install(self, package_name: str, version: Optional[str] = None) -> None:
        """
        Install a package.

        Args:
            package_name (str): The name of the package to install.
            version (Optional[str]): The version of the package to install. Defaults to None.

        Raises:
            PackageManagerError: If the installation fails.
        """
        pass

    @abc.abstractmethod
    def uninstall(self, package_name: str) -> None:
        """
        Uninstall a package.

        Args:
            package_name (str): The name of the package to uninstall.

        Raises:
            PackageManagerError: If the uninstallation fails.
        """
        pass

    @abc.abstractmethod
    def update(self, package_name: str) -> None:
        """
        Update a package to its latest version.

        Args:
            package_name (str): The name of the package to update.

        Raises:
            PackageManagerError: If the update fails.
        """
        pass

    @abc.abstractmethod
    def list_installed(self) -> List[str]:
        """
        List all installed packages.

        Returns:
            List[str]: A list of installed package names.

        Raises:
            PackageManagerError: If listing the packages fails.
        """
        pass
