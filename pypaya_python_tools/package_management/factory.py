from pypaya_python_tools.package_management.base import PackageManager
from pypaya_python_tools.package_management.pip_manager import PipPackageManager
from pypaya_python_tools.package_management.conda_manager import CondaPackageManager


class PackageManagerFactory:
    @staticmethod
    def create(manager_type: str) -> PackageManager:
        """
        Create and return a package manager instance based on the specified type.

        Args:
            manager_type (str): The type of package manager to create ('pip' or 'conda').

        Returns:
            PackageManager: An instance of the specified package manager.

        Raises:
            ValueError: If an unsupported package manager type is specified.
        """
        if manager_type.lower() == "pip":
            return PipPackageManager()
        elif manager_type.lower() == "conda":
            return CondaPackageManager()
        else:
            raise ValueError(f"Unsupported package manager type: {manager_type}")
