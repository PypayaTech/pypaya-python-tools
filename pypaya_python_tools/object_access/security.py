from dataclasses import dataclass


@dataclass
class ObjectAccessSecurityContext:
    """Security settings for object access operations."""
    allow_dynamic_creation: bool = True
    allow_modification: bool = True


# Common configurations
DEFAULT_OBJECT_ACCESS_SECURITY = ObjectAccessSecurityContext()
STRICT_OBJECT_ACCESS_SECURITY = ObjectAccessSecurityContext(
    allow_dynamic_creation=False,
    allow_modification=False
)
