# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=too-many-lines

import asyncio
from datetime import datetime

import fakeredis
import fakeredis.aioredis
import pytest
from httpx import AsyncClient

from app.config import settings
from app.database.models import Comment, Post, User, UserRole
from app.database.redis import redis
from app.database.sqlite import db
from app.factory import create_app
from app.schema import (
    CommentHeavyResponseModel,
    PostHeavyResponseModel,
    UserResponseModel,
)
from app.utils.auth import get_password_hash


@pytest.fixture()
def test_app():
    app = create_app()
    return app


@pytest.fixture(autouse=True)
async def init_sqlite(mocker):
    mocker.patch.object(settings, 'sqlite_url', 'sqlite+aiosqlite:///test.db')
    await db.init()
    yield
    await db.close()


@pytest.fixture(autouse=True)
async def init_redis(mocker):
    fake_redis_pool = await fakeredis.aioredis.create_redis_pool(
        server=fakeredis.FakeServer()
    )
    mocker.patch.object(redis, 'redis', fake_redis_pool)
    yield
    await redis.close()


@pytest.fixture
@pytest.mark.usefixtures('init_sqlite', 'init_redis')
async def client(test_app):
    async with AsyncClient(app=test_app, base_url='http://test') as ac:
        yield ac


@pytest.fixture
@pytest.mark.usefixtures('init_sqlite')
async def session():
    async with db.create_session() as s:
        yield s


@pytest.fixture(scope='session')
def loop():
    return asyncio.get_event_loop()


@pytest.fixture
def admin():
    return UserResponseModel(id=1, username='admin', full_name='Some Name')


@pytest.fixture
def admin_password():
    return '12345'


@pytest.fixture
async def add_admin(session, admin, admin_password):
    admin = User(
        username=admin.username,
        full_name=admin.full_name,
        hashed_password=get_password_hash(admin_password),
        role=UserRole.ADMIN,
    )
    session.add(admin)
    await session.commit()


@pytest.fixture
def admin_access_token():
    return (
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiJ9.'
        'RTorVw9_Ct0bujXXBFn78iMmTTHR9h7byWrOlfTkUk4'
    )


@pytest.fixture
def user():
    return UserResponseModel(id=2, username='user', full_name='Some Name')


@pytest.fixture
def user_password():
    return '123'


@pytest.fixture
async def add_user(session, user, user_password):
    user = User(
        username=user.username,
        full_name=user.full_name,
        hashed_password=get_password_hash(user_password),
        role=UserRole.CLIENT,
    )
    session.add(user)
    await session.commit()


@pytest.fixture
def user_access_token():
    return (
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyIn0.'
        'MRTmuDXku7p4irdVIX_UXIzIx5x3PU9RQPu13S6UhC0'
    )


@pytest.fixture
def datetime_utcnow():
    return datetime.utcnow()


@pytest.fixture
def post1(admin, datetime_utcnow):
    return PostHeavyResponseModel(
        id=1,
        header='USA starts withdrawal of troops from Afghanistan',
        text='text1',
        author=admin,
        posted_at=datetime_utcnow,
    )


@pytest.fixture
def post2(admin, datetime_utcnow):
    return PostHeavyResponseModel(
        id=2,
        header='Manchester City could clinch the Football Premier League',
        text='text2',
        author=admin,
        posted_at=datetime_utcnow,
    )


@pytest.fixture
def post3(admin, datetime_utcnow):
    return PostHeavyResponseModel(
        id=3,
        header='La Liga: Real Madrid vs Osasuna - who will win the first prize?',
        text='text3',
        author=admin,
        posted_at=datetime_utcnow,
    )


@pytest.fixture
def three_posts(post1, post2, post3):
    return post1, post2, post3


@pytest.fixture
@pytest.mark.usefixtures('add_admin')
async def add_three_posts(session, admin, post1, post2, post3):
    posts = [
        Post(
            id=post1.id,
            header=post1.header,
            text=post1.text,
            posted_at=post1.posted_at,
            author_id=admin.id,
        ),
        Post(
            id=post2.id,
            header=post2.header,
            text=post2.text,
            posted_at=post2.posted_at,
            author_id=admin.id,
        ),
        Post(
            id=post3.id,
            header=post3.header,
            text=post3.text,
            posted_at=post3.posted_at,
            author_id=admin.id,
        ),
    ]
    for post in posts:
        session.add(post)
        await session.commit()


@pytest.fixture
def mock_page_size(mocker):
    mocker.patch('app.utils.common.PAGE_SIZE', 2)


@pytest.fixture
def post4(admin, datetime_utcnow):
    return PostHeavyResponseModel(
        id=4,
        header='Something about Russia (again): breaking news from St Petersburg',
        text='text4',
        author=admin,
        posted_at=datetime_utcnow,
    )


@pytest.fixture
def post5(admin, datetime_utcnow):
    return PostHeavyResponseModel(
        id=5,
        header='Moscow City: where can you travel in Russia?',
        text='text5',
        author=admin,
        posted_at=datetime_utcnow,
    )


@pytest.fixture
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def add_two_more_posts(session, admin, post4, post5):
    posts = [
        Post(
            id=post4.id,
            header=post4.header,
            text=post4.text,
            posted_at=post4.posted_at,
            author_id=admin.id,
        ),
        Post(
            id=post5.id,
            header=post5.header,
            text=post5.text,
            posted_at=post5.posted_at,
            author_id=admin.id,
        ),
    ]
    for post in posts:
        session.add(post)
        await session.commit()


@pytest.fixture
def comment1(admin, datetime_utcnow, post1):
    return CommentHeavyResponseModel(
        id=1, text='comment1', author=admin, post=post1, posted_at=datetime_utcnow
    )


@pytest.fixture
def comment2(admin, datetime_utcnow, post1):
    return CommentHeavyResponseModel(
        id=2, text='comment2', author=admin, post=post1, posted_at=datetime_utcnow
    )


@pytest.fixture
def comment3(admin, datetime_utcnow, post1):
    return CommentHeavyResponseModel(
        id=3, text='comment3', author=admin, post=post1, posted_at=datetime_utcnow
    )


@pytest.fixture
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def add_three_comments(session, admin, post1, comment1, comment2, comment3):
    comments = [
        Comment(
            id=comment1.id,
            text=comment1.text,
            posted_at=comment1.posted_at,
            author_id=admin.id,
            post_id=post1.id,
        ),
        Comment(
            id=comment2.id,
            text=comment2.text,
            posted_at=comment2.posted_at,
            author_id=admin.id,
            post_id=post1.id,
        ),
        Comment(
            id=comment3.id,
            text=comment3.text,
            posted_at=comment3.posted_at,
            author_id=admin.id,
            post_id=post1.id,
        ),
    ]
    for comment in comments:
        session.add(comment)
        await session.commit()
