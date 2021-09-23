from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from pydantic.types import SecretStr


class TokenResponseModel(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class UserResponseModel(BaseModel):
    id: int
    username: str
    full_name: str


class SuccessResponseModel(BaseModel):
    success: bool


class PostLightResponseModel(BaseModel):
    id: int


class PostHeavyResponseModel(BaseModel):
    id: int
    header: str
    photo: Optional[bytes]
    text: str
    author: UserResponseModel
    posted_at: datetime


class PostsPaginatedResponseModel(BaseModel):
    posts: List[PostHeavyResponseModel]
    page: int
    total_pages: int


class UserRegisterRequestBodyModel(BaseModel):
    username: str
    full_name: str
    password: SecretStr


class CommentLightResponseModel(BaseModel):
    id: int
    author_id: int
    post_id: int


class CommentHeavyResponseModel(BaseModel):
    id: int
    text: str
    author: UserResponseModel
    post: PostLightResponseModel
    posted_at: datetime


class CommentsPaginatedResponseModel(BaseModel):
    comments: List[CommentHeavyResponseModel]
    page: int
    total_pages: int
