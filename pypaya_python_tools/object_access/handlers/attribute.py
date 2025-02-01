from typing import Any
from pypaya_python_tools.object_access.exceptions import ObjectAccessSecurityError
from pypaya_python_tools.object_access.definitions import AccessType, ObjectAccess
from pypaya_python_tools.object_access.handlers.base import AccessHandler, AccessResult


class AttributeHandler(AccessHandler):
    """Handles attribute access and modification."""

    def can_handle(self, obj: Any, access: ObjectAccess) -> bool:
        return access.type in (AccessType.GET, AccessType.SET)

    def _validate_access(self, obj: Any, access: ObjectAccess) -> None:
        if access.type == AccessType.SET and not self.security.allow_modification:
            raise ObjectAccessSecurityError("Attribute modification is not allowed")

    def handle(self, obj: Any, access: ObjectAccess) -> AccessResult:
        self._validate_access(obj, access)

        try:
            if access.type == AccessType.GET:
                if not access.args:
                    raise AttributeError("Attribute name must be specified")
                attr_name = access.args[0]
                if not hasattr(obj, attr_name):
                    raise AttributeError(f"Object has no attribute '{attr_name}'")

                value = getattr(obj, attr_name)
                return AccessResult(value, metadata={"attribute": attr_name})

            else:  # SET
                if len(access.args) < 2:
                    raise AttributeError("Attribute name and value must be specified")
                attr_name, value = access.args[:2]
                setattr(obj, attr_name, value)
                return AccessResult(None, metadata={
                    "attribute": attr_name,
                    "value": value
                })

        except Exception as e:
            if isinstance(e, AttributeError):
                raise
            raise AttributeError(f"Attribute access failed: {str(e)}")
