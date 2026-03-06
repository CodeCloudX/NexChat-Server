from fastapi import HTTPException, status

class NexChatException(HTTPException):
    """Base exception for all NexChat errors."""
    def __init__(self, status_code: int, detail: str = None):
        super().__init__(status_code=status_code, detail=detail)

class UserNotFoundException(NexChatException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

class UserAlreadyExistsException(NexChatException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

class AuthenticationException(NexChatException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class InactiveUserException(NexChatException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

class ChatNotFoundException(NexChatException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Chat room not found")

class UnauthorizedException(NexChatException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class ForbiddenException(NexChatException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class InvalidFileException(NexChatException):
    def __init__(self, detail: str = "Invalid file type or content"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class StorageException(NexChatException):
    def __init__(self, detail: str = "Failed to process file in storage"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
