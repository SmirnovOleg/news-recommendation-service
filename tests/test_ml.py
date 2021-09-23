# pylint: disable=too-many-arguments

import pytest
from starlette import status

from app.database.redis import redis


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_get_similar_posts_empty(client, admin_access_token, post1):
    resp = await client.get(
        url=f'/posts/{post1.id}/similar',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_get_similar_posts_for_nonexistent(client, admin_access_token):
    resp = await client.get(
        url='/posts/123/similar',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json() == {'detail': 'Post with id = 123 was not found'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_get_similar_posts_symmetry(client, admin_access_token, post2, post3):
    resp_for_post2 = await client.get(
        url=f'/posts/{post2.id}/similar',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp_for_post2.status_code == status.HTTP_200_OK
    assert resp_for_post2.json() == [
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
    ]

    resp_for_post3 = await client.get(
        url=f'/posts/{post3.id}/similar',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp_for_post3.status_code == status.HTTP_200_OK
    assert resp_for_post3.json() == [
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
        }
    ]


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts', 'mock_page_size')
async def test_get_feed(
    client, admin, admin_access_token, post2, post3, datetime_utcnow
):
    # Update browsing history to get recommendations later
    await redis.zadd(key=admin.id, score=datetime_utcnow.timestamp(), member=post2.id)

    resp = await client.get(
        url='/posts/feed',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'page': 1,
        'total_pages': 1,
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
@pytest.mark.usefixtures('add_admin', 'add_three_posts', 'mock_page_size')
async def test_get_feed_page_one(
    client, admin, admin_access_token, post2, post3, datetime_utcnow
):
    # Update browsing history to get recommendations later
    await redis.zadd(key=admin.id, score=datetime_utcnow.timestamp(), member=post2.id)

    resp = await client.get(
        url='/posts/feed?page=1',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'page': 1,
        'total_pages': 1,
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
@pytest.mark.usefixtures('add_admin', 'add_three_posts', 'mock_page_size')
async def test_get_feed_invalid_page(
    client, admin, admin_access_token, post2, datetime_utcnow
):
    # Update browsing history to get recommendations later
    await redis.zadd(key=admin.id, score=datetime_utcnow.timestamp(), member=post2.id)

    resp = await client.get(
        url='/posts/feed?page=123',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json() == {'detail': 'Page number is too big'}
