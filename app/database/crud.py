from datetime import datetime, timedelta
from random import randint
from sqlite3 import IntegrityError
from typing import List, NamedTuple, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Comment, Post, User, UserRole
from app.database.redis import AsyncRedisAdapter
from app.utils.common import calculate_total_pages, get_page_size


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    result = await session.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def create_admin(
    session: AsyncSession, username: str, full_name: str, hashed_password: str
) -> User:
    return await create_user(
        session, username, full_name, hashed_password, UserRole.ADMIN
    )


async def create_user(
    session: AsyncSession,
    username: str,
    full_name: str,
    hashed_password: str,
    role: UserRole = UserRole.CLIENT,
) -> User:
    if await get_user_by_username(session, username):
        raise UserAlreadyExistsException

    user = User(
        username=username,
        full_name=full_name,
        hashed_password=hashed_password,
        role=role,
    )

    try:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    except IntegrityError as e:  # pragma: no cover
        if await get_user_by_username(session, username):
            raise UserAlreadyExistsException from e

    return user


async def create_post(
    session: AsyncSession, header: str, photo: Optional[bytes], text: str, author: User
) -> Post:
    post = Post(header=header, photo=photo, text=text, author=author)
    session.add(post)
    await session.commit()

    return post


async def get_post_by_id(session: AsyncSession, post_id: int) -> Optional[Post]:
    result = await session.execute(select(Post).filter(Post.id == post_id))
    return result.scalars().first()


async def remove_post_by_id(session: AsyncSession, post_id: int) -> None:
    post = await get_post_by_id(session, post_id)
    if post:
        try:
            await session.delete(post)
            await session.commit()
        except IntegrityError as e:  # pragma: no cover
            if not await get_post_by_id(session, post_id):
                raise PostNotFoundException from e
    else:
        raise PostNotFoundException


async def get_all_posts_for_last_week(session: AsyncSession) -> List[Post]:
    start_date = datetime.utcnow() - timedelta(weeks=1)
    return await get_all_posts_after_date(session, start_date)


async def get_all_posts_after_date(
    session: AsyncSession, start_date: datetime
) -> List[Post]:
    result = await session.execute(select(Post).filter(Post.posted_at >= start_date))
    return result.scalars().all()


class PostsOnPage(NamedTuple):
    posts: List[Post]
    total_pages: int


async def get_posts_by_page(session: AsyncSession, page: int) -> PostsOnPage:
    page_size = get_page_size()
    total_posts = (await session.execute(func.count(Post.id))).scalar()

    total_pages = calculate_total_pages(total_posts, page_size)
    if page > total_pages:
        raise InvalidPageNumException()

    posts = await session.execute(
        select(Post).offset((page - 1) * page_size).limit(page_size)
    )

    return PostsOnPage(posts=posts.scalars().all(), total_pages=total_pages)


async def update_browsing_history(
    redis: AsyncRedisAdapter, user_id: int, current_timestamp: float, post_id: int
) -> None:
    await redis.zadd(key=user_id, score=current_timestamp, member=post_id)


async def get_recently_viewed_posts_for_last_week(
    session: AsyncSession,
    redis: AsyncRedisAdapter,
    user_id: int,
    current_timestamp: float,
) -> List[Post]:
    start_timestamp_week_ago = (
        datetime.fromtimestamp(current_timestamp) - timedelta(weeks=1)
    ).timestamp()

    # According to https://stackoverflow.com/a/49773605
    # Periodically update the cache to keep browsing history only for the last week
    if randint(1, 5) == 1:  # pragma: no cover
        await redis.zremrangebyscore(key=user_id, max=start_timestamp_week_ago - 1)

    recently_viewed_posts_ids_encoded = await redis.zrangebyscore(
        key=user_id, min=start_timestamp_week_ago
    )
    recently_viewed_posts_ids = [
        post_id.decode() for post_id in recently_viewed_posts_ids_encoded
    ]

    relevant_posts = await session.execute(
        select(Post).filter(Post.id.in_(recently_viewed_posts_ids))
    )

    return relevant_posts.scalars().all()


async def create_comment(
    session: AsyncSession, text: str, author: User, post: Post
) -> Comment:
    comment = Comment(text=text, author=author, post=post)
    session.add(comment)
    await session.commit()

    return comment


async def get_all_comments_by_post_id(
    session: AsyncSession, post_id: int
) -> List[Comment]:
    result = await session.execute(select(Comment).filter(Comment.post_id == post_id))
    return result.scalars().all()


class CommentsOnPage(NamedTuple):
    comments: List[Comment]
    total_pages: int


async def get_comments_by_post_id_and_page(
    session: AsyncSession, post_id: int, page: int
) -> CommentsOnPage:
    page_size = get_page_size()
    total_comments = (
        await session.execute(
            select(func.count(Comment.id)).filter(Comment.post_id == post_id)
        )
    ).scalar()

    total_pages = calculate_total_pages(total_comments, page_size)
    if page > total_pages:
        raise InvalidPageNumException()

    comments = await session.execute(
        select(Comment).offset((page - 1) * page_size).limit(page_size)
    )

    return CommentsOnPage(comments=comments.scalars().all(), total_pages=total_pages)


class UserAlreadyExistsException(Exception):
    pass


class PostNotFoundException(Exception):
    pass


class InvalidPageNumException(Exception):
    pass
