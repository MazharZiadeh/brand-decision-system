import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, EmailStr, Field


class Facilitator(BaseModel):
    """Authenticated agency operator.

    The domain model represents the identity, not credentials. Authentication
    (password, sessions, tokens) is the API/auth layer's concern.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: EmailStr
    display_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
