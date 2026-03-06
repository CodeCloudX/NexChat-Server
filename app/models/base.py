from sqlalchemy.ext.declarative import as_declarative, declared_attr
import enum

@as_declarative()
class Base:
    id: any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

# --- Centralized Enums to avoid Circular Imports ---

class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VOICE = "voice"

class ChatType(str, enum.Enum):
    DIRECT = "direct"
    GROUP = "group"

class MemberRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"
