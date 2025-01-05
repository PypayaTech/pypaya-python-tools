from typing import Any, Type, Dict, List, Set, Optional, Union, get_type_hints
import inspect
from abc import ABC, abstractmethod
from dataclasses import is_dataclass
from enum import Enum


def is_abstract(cls: Type) -> bool:
    """
    Comprehensively check if a class is abstract.

    Checks for:
    1. ABC inheritance and abstractmethods
    2. Non-ABC abstract methods
    3. Unimplemented abstract methods in inheritance chain
    4. Abstract properties and other descriptors

    Args:
        cls: Class to check

    Returns:
        bool: True if class is abstract
    """
    # Check using inspect
    if inspect.isabstract(cls):
        return True

    # Check for abstractmethods
    for name, value in inspect.getmembers(cls):
        if getattr(value, "__isabstractmethod__", False):
            return True

    # Check __abstractmethods__ attribute
    abstract_methods = getattr(cls, "__abstractmethods__", set())
    if abstract_methods:
        return True

    return False


def get_signature(callable_obj: Any) -> Dict[str, Any]:
    """
    Get comprehensive signature information for a callable.

    Args:
        callable_obj: Function, method, or callable object

    Returns:
        Dict containing:
        - parameters: Parameter information including defaults, annotations
        - return_type: Return type annotation if available
        - is_method: Whether it's a method
        - is_class_method: Whether it's a class method
        - is_static_method: Whether it's a static method
        - is_property: Whether it's a property
        - has_varargs: Whether it accepts *args
        - has_varkw: Whether it accepts **kwargs
    """
    sig = inspect.signature(callable_obj)
    type_hints = get_type_hints(callable_obj)

    return {
        "parameters": {
            name: {
                "kind": param.kind.name,
                "default": param.default if param.default is not param.empty else None,
                "annotation": type_hints.get(name, None),
                "has_default": param.default is not param.empty
            }
            for name, param in sig.parameters.items()
        },
        "return_type": type_hints.get("return", None),
        "is_method": inspect.ismethod(callable_obj),
        "is_class_method": isinstance(callable_obj, classmethod),
        "is_static_method": isinstance(callable_obj, staticmethod),
        "is_property": isinstance(callable_obj, property),
        "has_varargs": any(p.kind == inspect.Parameter.VAR_POSITIONAL
                           for p in sig.parameters.values()),
        "has_varkw": any(p.kind == inspect.Parameter.VAR_KEYWORD
                         for p in sig.parameters.values())
    }


def analyze_class(cls: Type) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of a class.

    Args:
        cls: Class to analyze

    Returns:
        Dict containing:
        - methods: All methods with their signatures
        - properties: All properties
        - class_attrs: Class attributes
        - instance_attrs: Instance attributes
        - bases: Base classes
        - is_dataclass: Whether it's a dataclass
        - is_enum: Whether it's an enum
        - is_abstract: Whether it's abstract
        - special_methods: Special methods (__init__, __call__, etc.)
    """
    return {
        "methods": {
            name: get_signature(value)
            for name, value in inspect.getmembers(cls)
            if inspect.isfunction(value) or inspect.ismethod(value)
        },
        "properties": {
            name: {"doc": value.__doc__, "type": get_type_hints(value).get("return")}
            for name, value in inspect.getmembers(cls, lambda x: isinstance(x, property))
        },
        "class_attrs": {
            name: value for name, value in vars(cls).items()
            if not (inspect.isfunction(value) or isinstance(value, property))
        },
        "instance_attrs": {
            name: getattr(cls, name) for name in dir(cls)
            if not name.startswith('_') and not hasattr(type(cls), name)
        },
        "bases": cls.__bases__,
        "is_dataclass": is_dataclass(cls),
        "is_enum": issubclass(cls, Enum),
        "is_abstract": is_abstract(cls),
        "special_methods": {
            name: get_signature(value)
            for name, value in inspect.getmembers(cls)
            if name.startswith('__') and name.endswith('__') and callable(value)
        }
    }
