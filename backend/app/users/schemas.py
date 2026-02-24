"""User request/response schemas."""
from typing import Optional

from pydantic import BaseModel, EmailStr


class InviteRequest(BaseModel):
    email: EmailStr
    role: str
    name: Optional[str] = None


class UserListResponse(BaseModel):
    id: str
    name: Optional[str]
    email: str
    role: str
    status: str
    last_login: Optional[str] = None
    created_at: str


class ChangeRoleRequest(BaseModel):
    role: str
