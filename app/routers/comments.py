from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import (
    InvalidPageNumException,
    create_comment,
    get_all_comments_by_post_id,
    get_comments_by_post_id_and_page,
)
from app.database.models import User
from app.database.sqlite import db
from app.schema import (
    CommentHeavyResponseModel,
    CommentLightResponseModel,
    CommentsPaginatedResponseModel,
    PostLightResponseModel,
    UserResponseModel,
)
from app.utils.auth import get_current_active_user
from app.utils.common import get_post_or_throw_not_found_exception

router = APIRouter()


@router.post(
    '/posts/{post_id}/comments',
    status_code=status.HTTP_201_CREATED,
    response_model=CommentLightResponseModel,
)
async def add_new_comment(
    post_id: int,
    text: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db.get_session),
) -> CommentLightResponseModel:
    post = await get_post_or_throw_not_found_exception(session, post_id)
    comment = await create_comment(session, text, author=current_user, post=post)

    return CommentLightResponseModel(
        id=comment.id, author_id=current_user.id, post_id=post.id
    )


@router.get('/posts/{post_id}/comments', response_model=CommentsPaginatedResponseModel)
async def get_comments(
    post_id: int,
    page: Optional[int] = Query(None, ge=1),
    _: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db.get_session),
) -> CommentsPaginatedResponseModel:
    try:
        if not page:
            comments = await get_all_comments_by_post_id(session, post_id)
            total_pages = 1
        else:
            comments, total_pages = await get_comments_by_post_id_and_page(
                session, post_id, page
            )
    except InvalidPageNumException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Page number is too big'
        ) from e

    return CommentsPaginatedResponseModel(
        comments=[
            CommentHeavyResponseModel(
                id=comment.id,
                text=comment.text,
                posted_at=comment.posted_at,
                author=UserResponseModel(
                    id=comment.author.id,
                    username=comment.author.username,
                    full_name=comment.author.full_name,
                ),
                post=PostLightResponseModel(id=post_id),
            )
            for comment in comments
        ],
        page=page or 1,
        total_pages=total_pages,
    )
