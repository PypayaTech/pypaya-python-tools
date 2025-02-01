from typing import Any, Optional, Dict, Type, TypeVar, overload, Iterator
from pypaya_python_tools.object_operations.definitions import OperationType, Operation
from pypaya_python_tools.object_operations.manager import AccessManager
from pypaya_python_tools.object_operations.security import OperationSecurity


T = TypeVar('T')


_default_manager: Optional[AccessManager] = None


def get_access_manager(security: Optional[OperationSecurity] = None) -> AccessManager:
    """Get or create an AccessManager instance.

    Args:
        security: Optional security configuration. If None, uses permissive defaults.

    Returns:
        AccessManager instance (creates new or returns cached)
    """
    global _default_manager
    if _default_manager is None or security is not None:
        if security is None:
            security = OperationSecurity(
                allow_dynamic_access=True,
                allow_modification=True,
                allow_container_modification=True
            )
        _default_manager = AccessManager(security)
    return _default_manager


# Direct access
def direct(obj: Any) -> Any:
    """Get direct access to object.

    Args:
        obj: Target object

    Returns:
        Object itself with metadata
    """
    op = Operation(OperationType.DIRECT)
    return get_access_manager().access_object(obj, op)


# Attribute operations
@overload
def get_attribute(obj: Any, name: str) -> Any:
    ...


@overload
def get_attribute(obj: Any, name: str, default: T) -> T:
    ...


def get_attribute(obj: Any, name: str, default: Any = None) -> Any:
    """Get object attribute by name.

    Args:
        obj: Target object
        name: Attribute name
        default: Optional default value if attribute doesn't exist

    Returns:
        Attribute value or default
    """
    op = Operation(
        type=OperationType.GET_ATTRIBUTE,
        args=(name, default)
    )
    return get_access_manager().access_object(obj, op)


def set_attribute(obj: Any, name: str, value: Any) -> None:
    """Set object attribute value.

    Args:
        obj: Target object
        name: Attribute name
        value: Value to set
    """
    op = Operation(
        type=OperationType.SET_ATTRIBUTE,
        args=(name, value)
    )
    return get_access_manager().access_object(obj, op)


def del_attribute(obj: Any, name: str) -> None:
    """Delete object attribute.

    Args:
        obj: Target object
        name: Attribute name to delete
    """
    op = Operation(
        type=OperationType.DEL_ATTRIBUTE,
        args=(name,)
    )
    return get_access_manager().access_object(obj, op)


# Callable operations
def call(obj: Any, *args: Any, **kwargs: Any) -> Any:
    """Call an object directly.

    Args:
        obj: Callable object
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Call result
    """
    op = Operation(
        type=OperationType.CALL,
        args=args,
        kwargs=kwargs
    )
    return get_access_manager().access_object(obj, op)


def instantiate(cls: Type[T], *args: Any, **kwargs: Any) -> T:
    """Instantiate a class.

    Args:
        cls: Class to instantiate
        *args: Constructor positional arguments
        **kwargs: Constructor keyword arguments

    Returns:
        New instance
    """
    op = Operation(
        type=OperationType.INSTANTIATE,
        args=args,
        kwargs=kwargs
    )
    return get_access_manager().access_object(cls, op)


# Container operations
def get_item(obj: Any, key: Any) -> Any:
    """Get container item.

    Args:
        obj: Container object
        key: Item key

    Returns:
        Item value
    """
    op = Operation(
        type=OperationType.GET_ITEM,
        args=(key,)
    )
    return get_access_manager().access_object(obj, op)


def set_item(obj: Any, key: Any, value: Any) -> None:
    """Set container item.

    Args:
        obj: Container object
        key: Item key
        value: Value to set
    """
    op = Operation(
        type=OperationType.SET_ITEM,
        args=(key, value)
    )
    return get_access_manager().access_object(obj, op)


def del_item(obj: Any, key: Any) -> None:
    """Delete container item.

    Args:
        obj: Container object
        key: Key to delete
    """
    op = Operation(
        type=OperationType.DEL_ITEM,
        args=(key,)
    )
    return get_access_manager().access_object(obj, op)


def iterate(obj: Any) -> Iterator:
    """Get iterator for object.

    Args:
        obj: Iterable object

    Returns:
        Iterator for the object
    """
    op = Operation(OperationType.ITERATE)
    return get_access_manager().access_object(obj, op)
