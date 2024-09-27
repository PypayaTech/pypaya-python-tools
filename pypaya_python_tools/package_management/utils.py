from typing import Union, Optional
from pypaya_python_tools.package_management.base import PackageManager
from pypaya_python_tools.package_management.factory import PackageManagerFactory


def install_package(package_name: str, manager: Union[str, PackageManager] = "pip",
                    version: Optional[str] = None) -> None:
    """
    Install a package using the specified package manager.

    This function provides a high-level interface for package installation,
    abstracting away the details of different package managers.

    Args:
        package_name (str): The name of the package to install.
        manager (Union[str, PackageManager]): The package manager to use.
            Can be 'pip', 'conda', or an instance of PackageManager. Defaults to 'pip'.
        version (Optional[str]): The version of the package to install. Defaults to None.

    Raises:
        PackageManagerError: If the installation fails.
        ValueError: If an unsupported package manager is specified.

    Examples:
        >>> install_package('numpy')
        >>> install_package('pandas', 'conda', '1.2.3')
        >>> pip_manager = PackageManagerFactory.create('pip')
        >>> install_package('requests', pip_manager)
    """
    if isinstance(manager, str):
        package_manager = PackageManagerFactory.create(manager)
    elif isinstance(manager, PackageManager):
        package_manager = manager
    else:
        raise ValueError("Invalid package manager specified")

    package_manager.install(package_name, version)
