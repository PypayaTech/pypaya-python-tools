from dataclasses import dataclass, field
from typing import Set
from pypaya_python_tools.object_operations.exceptions import (
    SecurityError,
    AccessSecurityError,
    ModificationSecurityError
)


@dataclass
class OperationSecurity:
    """Security controls for object operations.

    Attributes:
        enabled: Whether security checks are enabled
        allow_private_access: Allow access to private members (__name)
        allow_protected_access: Allow access to protected members (_name)
        allow_modification: Allow modification operations (set/del)
        allow_dynamic_access: Allow dynamic operations (call/instantiate)
        allow_container_modification: Allow container modifications
        allowed_methods: Set of explicitly allowed methods
        blocked_methods: Set of explicitly blocked methods
        allowed_attributes: Set of explicitly allowed attributes
        blocked_attributes: Set of explicitly blocked attributes
    """

    # Basic controls
    enabled: bool = True

    # Access control
    allow_private_access: bool = False
    allow_protected_access: bool = False
    allow_modification: bool = False
    allow_dynamic_access: bool = False
    allow_container_modification: bool = False

    # Method/attribute restrictions
    allowed_methods: Set[str] = field(default_factory=set)
    blocked_methods: Set[str] = field(default_factory=set)
    allowed_attributes: Set[str] = field(default_factory=set)
    blocked_attributes: Set[str] = field(default_factory=set)

    def validate_access(self, name: str, is_method: bool = False) -> None:
        """Validate member access.

        Args:
            name: Name of the member to access
            is_method: Whether the member is a method

        Raises:
            AccessSecurityError: If access is not allowed
            SecurityError: If validation fails
        """
        if not self.enabled:
            return

        # Check private/protected access
        if name.startswith('__') and not name.endswith('__'):
            if not self.allow_private_access:
                raise AccessSecurityError(
                    f"Private member access denied: {name}",
                    access_type="private"
                )
        elif name.startswith('_'):
            if not self.allow_protected_access:
                raise AccessSecurityError(
                    f"Protected member access denied: {name}",
                    access_type="protected"
                )

        # Check allowed/blocked members
        target_allowed = self.allowed_methods if is_method else self.allowed_attributes
        if target_allowed and name not in target_allowed:
            raise AccessSecurityError(
                f"Member {name} is not in allowed list",
                access_type="allowlist"
            )

        target_blocked = self.blocked_methods if is_method else self.blocked_attributes
        if name in target_blocked:
            raise AccessSecurityError(
                f"Member {name} is blocked",
                access_type="blocklist"
            )

    def validate_modification(self, operation_type: str) -> None:
        """Validate modification operations.

        Args:
            operation_type: Type of modification operation

        Raises:
            ModificationSecurityError: If modification is not allowed
        """
        if not self.enabled:
            return

        if not self.allow_modification:
            raise ModificationSecurityError(
                "Modification operations are not allowed",
                modification_type=operation_type
            )

        if operation_type.startswith("container_") and not self.allow_container_modification:
            raise ModificationSecurityError(
                "Container modification is not allowed",
                modification_type=operation_type
            )
