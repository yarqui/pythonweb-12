import enum

__all__ = ["Role"]


class Role(enum.Enum):
    """
    An enumeration for user roles.
    """

    ADMIN = "admin"
    USER = "user"
