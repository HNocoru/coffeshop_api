from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100,)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    name: str
    email: str
    role: str
    model_config = {
        "from_attributes": True,
    }

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"