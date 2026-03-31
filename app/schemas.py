from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        orm_mode = True

class DocumentResponse(BaseModel):
    id: int
    title: str
    company_name: str
    document_type: str
    uploaded_by: str
    created_at: datetime

    class Config:
        orm_mode = True