# pylint: disable=too-many-arguments

import pytest
from sqlalchemy import select
from starlette import status

from app.database.crud import (
    InvalidPageNumException,
    PostNotFoundException,
    PostsOnPage,
    get_posts_by_page,
    remove_post_by_id,
)
from app.database.models import Post
from app.database.redis import redis


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin')
async def test_add_new_post(client, session, admin, admin_access_token, post1):
    resp = await client.post(
        url='/posts',
        headers={'Authorization': f'Bearer {admin_access_token}'},
        data={'header': post1.header, 'text': post1.text},
    )

    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json() == {'id': post1.id}

    result = await session.execute(select(Post).filter(Post.id == post1.id))
    post_from_db = result.scalars().first()

    assert post_from_db.author_id == admin.id
    assert post_from_db.header == post1.header
    assert post_from_db.text == post1.text
    assert post_from_db.photo is None


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_user')
async def test_add_new_post_forbidden(client, user_access_token, post1):
    resp = await client.post(
        url='/posts',
        headers={'Authorization': f'Bearer {user_access_token}'},
        data={'header': post1.header, 'text': post1.text},
    )

    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json() == {'detail': 'Only admins can add new posts'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_get_all_posts_for_last_week(
    client, admin_access_token, post1, post2, post3
):
    resp = await client.get(
        url='/posts/recent',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'page': 1,
        'total_pages': 1,
        'posts': [
            {
                'id': post1.id,
                'header': post1.header,
                'text': post1.text,
                'photo': None,
                'posted_at': str(post1.posted_at).replace(' ', 'T'),
                'author': {
                    'id': post1.author.id,
                    'username': post1.author.username,
                    'full_name': post1.author.full_name,
                },
            },
            {
                'id': post2.id,
                'header': post2.header,
                'text': post2.text,
                'photo': None,
                'posted_at': str(post2.posted_at).replace(' ', 'T'),
                'author': {
                    'id': post2.author.id,
                    'username': post2.author.username,
                    'full_name': post2.author.full_name,
                },
            },
            {
                'id': post3.id,
                'header': post3.header,
                'text': post3.text,
                'photo': None,
                'posted_at': str(post3.posted_at).replace(' ', 'T'),
                'author': {
                    'id': post3.author.id,
                    'username': post3.author.username,
                    'full_name': post3.author.full_name,
                },
            },
        ],
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts', 'mock_page_size')
async def test_get_all_posts_for_last_week_page_one(
    client, admin_access_token, post1, post2
):
    resp = await client.get(
        url='/posts/recent?page=1',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'page': 1,
        'total_pages': 2,
        'posts': [
            {
                'id': post1.id,
                'header': post1.header,
                'text': post1.text,
                'photo': None,
                'posted_at': str(post1.posted_at).replace(' ', 'T'),
                'author': {
                    'id': post1.author.id,
                    'username': post1.author.username,
                    'full_name': post1.author.full_name,
                },
            },
            {
                'id': post2.id,
                'header': post2.header,
                'text': post2.text,
                'photo': None,
                'posted_at': str(post2.posted_at).replace(' ', 'T'),
                'author': {
                    'id': post2.author.id,
                    'username': post2.author.username,
                    'full_name': post2.author.full_name,
                },
            },
        ],
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts', 'mock_page_size')
async def test_get_all_posts_for_last_week_page_two(client, admin_access_token, post3):
    resp = await client.get(
        url='/posts/recent?page=2',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'page': 2,
        'total_pages': 2,
        'posts': [
            {
                'id': post3.id,
                'header': post3.header,
                'text': post3.text,
                'photo': None,
                'posted_at': str(post3.posted_at).replace(' ', 'T'),
                'author': {
                    'id': post3.author.id,
                    'username': post3.author.username,
                    'full_name': post3.author.full_name,
                },
            }
        ],
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    'add_admin', 'add_three_posts', 'add_three_comments', 'mock_page_size'
)
async def test_get_posts_invalid_page(client, admin_access_token):
    resp = await client.get(
        url='/posts/recent?page=123',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json() == {'detail': 'Page number is too big'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_remove_existing_post(client, session, admin_access_token, post1):
    resp = await client.delete(
        url=f'/posts/{post1.id}',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {'success': True}

    result = await session.execute(select(Post).filter(Post.id == post1.id))
    assert result.scalars().first() is None


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_remove_nonexistent_post(client, admin_access_token):
    resp = await client.delete(
        url='/posts/1234',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json() == {'detail': 'Post with id = 1234 was not found'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_remove_nonexistent_post_dao(session):
    with pytest.raises(PostNotFoundException):
        await remove_post_by_id(session, 123)


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_user', 'add_three_posts')
async def test_remove_existing_post_forbidden(client, user_access_token):
    resp = await client.delete(
        url='/posts/1234',
        headers={'Authorization': f'Bearer {user_access_token}'},
    )

    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json() == {'detail': 'Only admins can remove posts'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_get_single_post(client, admin, admin_access_token, post1):
    resp = await client.get(
        url=f'/posts/{post1.id}',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'id': post1.id,
        'header': post1.header,
        'text': post1.text,
        'photo': None,
        'posted_at': str(post1.posted_at).replace(' ', 'T'),
        'author': {
            'id': post1.author.id,
            'username': post1.author.username,
            'full_name': post1.author.full_name,
        },
    }

    browsing_history = await redis.zrangebyscore(admin.id)
    assert browsing_history == [str(post1.id).encode()]


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_get_single_nonexistent_post(client, admin_access_token):
    resp = await client.get(
        url='/posts/1234',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json() == {'detail': 'Post with id = 1234 was not found'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_three_posts')
async def test_get_posts_invalid_page_dao(session):
    with pytest.raises(InvalidPageNumException):
        await get_posts_by_page(session, page=123)


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_three_posts')
async def test_get_posts_dao(session, post3):
    posts = await get_posts_by_page(session, page=2)
    target_post = await session.execute(select(Post).filter(Post.id == post3.id))
    assert posts == PostsOnPage(posts=[target_post.scalars().first()], total_pages=2)
