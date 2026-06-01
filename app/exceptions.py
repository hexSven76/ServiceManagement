class AppError(Exception):
    pass


class ValidationError(AppError):
    pass


class NotFoundError(AppError):
    pass


class PermissionDeniedError(AppError):
    pass


class ConflictError(AppError):
    pass


class AuthenticationError(AppError):
    pass


class PaymentError(AppError):
    pass
