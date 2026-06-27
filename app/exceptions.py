class AppError(Exception):
    """Base application error shown cleanly in the Streamlit frontend."""


class ValidationError(AppError):
    """Raised when user input violates a business rule."""


class NotFoundError(AppError):
    """Raised when a requested record does not exist."""


class PermissionDeniedError(AppError):
    """Raised when a user tries to access another role/user's data."""


class AuthenticationError(AppError):
    """Raised for invalid login credentials or inactive accounts."""
