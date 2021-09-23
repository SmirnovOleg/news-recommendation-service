import asyncio
import datetime
import itertools
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import (
    InvalidPageNumException,
    PostNotFoundException,
    create_post,
    get_all_posts_for_last_week,
    get_posts_by_page,
    get_recently_viewed_posts_for_last_week,
    remove_post_by_id,
    update_browsing_history,
)
from app.database.models import User, UserRole
from app.database.redis import redis
from app.database.sqlite import db
from app.schema import (
    PostHeavyResponseModel,
    PostLightResponseModel,
    PostsPaginatedResponseModel,
    SuccessResponseModel,
    UserResponseModel,
)
from app.utils.auth import get_current_active_user
from app.utils.common import (
    base64_optional_encode,
    calculate_total_pages,
    get_page_size,
    get_post_or_throw_not_found_exception,
)
from app.utils.ml import find_similar_recent_posts

router = APIRouter()


@router.post(
    '/posts', status_code=status.HTTP_201_CREATED, response_model=PostLightResponseModel
)
async def add_new_post(
    photo: Optional[bytes] = File(None),
    header: str = Form(...),
    text: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db.get_session),
) -> PostLightResponseModel:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only admins can add new posts',
        )

    post = await create_post(session, header, photo, text, author=current_user)

    return PostLightResponseModel(id=post.id)


@router.get('/posts/recent', response_model=PostsPaginatedResponseModel)
async def get_posts_for_last_week(
    page: Optional[int] = Query(None, ge=1),
    _: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db.get_session),
) -> PostsPaginatedResponseModel:
    try:
        if not page:
            posts, total_pages = await get_all_posts_for_last_week(session), 1
        else:
            posts, total_pages = await get_posts_by_page(session, page)
    except InvalidPageNumException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Page number is too big'
        ) from e

    return PostsPaginatedResponseModel(
        posts=[
            PostHeavyResponseModel(
                id=post.id,
                header=post.header,
                photo=base64_optional_encode(post.photo),
                text=post.text,
                posted_at=post.posted_at,
                author=UserResponseModel(
                    id=post.author.id,
                    username=post.author.username,
                    full_name=post.author.full_name,
                ),
            )
            for post in posts
        ],
        page=page or 1,
        total_pages=total_pages,
    )


@router.get('/posts/feed', response_model=PostsPaginatedResponseModel)
async def get_feed(
    page: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db.get_session),
) -> PostsPaginatedResponseModel:
    recent_posts = await get_recently_viewed_posts_for_last_week(
        session,
        redis,
        user_id=current_user.id,
        current_timestamp=datetime.datetime.utcnow().timestamp(),
    )

    relevant_posts = set(
        list(
            itertools.chain(
                *(
                    await asyncio.gather(
                        *[
                            find_similar_recent_posts(session, post)
                            for post in recent_posts
                        ]
                    )
                )
            )
        )
    )

    posts_to_recommend = list(relevant_posts - set(recent_posts))

    if page:
        page_size = get_page_size()
        start_post_idx = (page - 1) * page_size
        total_pages = calculate_total_pages(
            total_items=len(posts_to_recommend), page_size=page_size
        )
        if page > total_pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Page number is too big'
            )
        posts = posts_to_recommend[start_post_idx : start_post_idx + page_size]
    else:
        posts, total_pages = posts_to_recommend, 1

    return PostsPaginatedResponseModel(
        posts=[
            PostHeavyResponseModel(
                id=post.id,
                header=post.header,
                photo=base64_optional_encode(post.photo),
                text=post.text,
                posted_at=post.posted_at,
                author=UserResponseModel(
                    id=post.author.id,
                    username=post.author.username,
                    full_name=post.author.full_name,
                ),
            )
            for post in posts
        ],
        page=page or 1,
        total_pages=total_pages,
    )


@router.delete('/posts/{post_id}', response_model=SuccessResponseModel)
async def remove_existing_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db.get_session),
) -> SuccessResponseModel:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only admins can remove posts',
        )
    try:
        await remove_post_by_id(session, post_id)
    except PostNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Post with id = {post_id} was not found',
        ) from e

    return SuccessResponseModel(success=True)


@router.get('/posts/{post_id}', response_model=PostHeavyResponseModel)
async def get_single_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db.get_session),
) -> PostHeavyResponseModel:
    post = await get_post_or_throw_not_found_exception(session, post_id)

    await update_browsing_history(
        redis=redis,
        user_id=current_user.id,
        current_timestamp=datetime.datetime.utcnow().timestamp(),
        post_id=post.id,
    )

    return PostHeavyResponseModel(
        id=post.id,
        header=post.header,
        photo=base64_optional_encode(post.photo),
        text=post.text,
        posted_at=post.posted_at,
        author=UserResponseModel(
            id=post.author.id,
            username=post.author.username,
            full_name=post.author.full_name,
        ),
    )


@router.get('/posts/{post_id}/similar', response_model=List[PostHeavyResponseModel])
async def get_similar_posts(
    post_id: int,
    _: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(db.get_session),
) -> List[PostHeavyResponseModel]:
    post = await get_post_or_throw_not_found_exception(session, post_id)
    similar_posts = await find_similar_recent_posts(session=session, original_post=post)

    return [
        PostHeavyResponseModel(
            id=post.id,
            header=post.header,
            photo=base64_optional_encode(post.photo),
            text=post.text,
            posted_at=post.posted_at,
            author=UserResponseModel(
                id=post.author.id,
                username=post.author.username,
                full_name=post.author.full_name,
            ),
        )
        for post in similar_posts
    ]
