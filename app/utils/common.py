import base64
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

import app.database.crud as crud
from app.config import PAGE_SIZE
from app.database.models import Post


def calculate_total_pages(total_items: int, page_size: int) -> int:
    return (total_items - 1) // page_size + 1 if total_items != 0 else 1


def get_page_size() -> int:
    return PAGE_SIZE


def base64_optional_encode(value: Optional[bytes]) -> Optional[bytes]:
    if value is not None:
        return base64.b64encode(value)
    return None


async def get_post_or_throw_not_found_exception(
    session: AsyncSession, post_id: int
) -> Post:
    post = await crud.get_post_by_id(session, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Post with id = {post_id} was not found',
        )
    return post
