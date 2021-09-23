# pylint: disable=too-many-arguments

import pytest
from sqlalchemy import select
from starlette import status

from app.database.crud import InvalidPageNumException, get_comments_by_post_id_and_page
from app.database.models import Comment


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_add_new_comment(
    client, session, admin, admin_access_token, post1, comment1
):
    resp = await client.post(
        url=f'/posts/{post1.id}/comments',
        headers={'Authorization': f'Bearer {admin_access_token}'},
        data={'text': comment1.text},
    )

    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json() == {'id': post1.id, 'author_id': admin.id, 'post_id': post1.id}

    result = await session.execute(select(Comment).filter(Comment.id == comment1.id))
    comment_from_db = result.scalars().first()

    assert comment_from_db.author_id == admin.id
    assert comment_from_db.post_id == post1.id
    assert comment_from_db.text == comment1.text


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin', 'add_three_posts')
async def test_add_new_comment_for_nonexistent_post(
    client, admin_access_token, comment1
):
    resp = await client.post(
        url='/posts/123/comments',
        headers={'Authorization': f'Bearer {admin_access_token}'},
        data={'text': comment1.text},
    )

    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert resp.json() == {'detail': 'Post with id = 123 was not found'}


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    'add_admin', 'add_three_posts', 'add_three_comments', 'mock_page_size'
)
async def test_get_comments_page_one(
    client, admin_access_token, post1, comment1, comment2
):
    resp = await client.get(
        url=f'/posts/{post1.id}/comments?page=1',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'page': 1,
        'total_pages': 2,
        'comments': [
            {
                'id': comment1.id,
                'text': comment1.text,
                'posted_at': str(comment1.posted_at).replace(' ', 'T'),
                'author': {
                    'id': comment1.author.id,
                    'username': comment1.author.username,
                    'full_name': comment1.author.full_name,
                },
                'post': {'id': post1.id},
            },
            {
                'id': comment2.id,
                'text': comment2.text,
                'posted_at': str(comment2.posted_at).replace(' ', 'T'),
                'author': {
                    'id': comment2.author.id,
                    'username': comment2.author.username,
                    'full_name': comment2.author.full_name,
                },
                'post': {'id': post1.id},
            },
        ],
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    'add_admin', 'add_three_posts', 'add_three_comments', 'mock_page_size'
)
async def test_get_comments_page_two(client, admin_access_token, post1, comment3):
    resp = await client.get(
        url=f'/posts/{post1.id}/comments?page=2',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'page': 2,
        'total_pages': 2,
        'comments': [
            {
                'id': comment3.id,
                'text': comment3.text,
                'posted_at': str(comment3.posted_at).replace(' ', 'T'),
                'author': {
                    'id': comment3.author.id,
                    'username': comment3.author.username,
                    'full_name': comment3.author.full_name,
                },
                'post': {'id': post1.id},
            }
        ],
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    'add_admin', 'add_three_posts', 'add_three_comments', 'mock_page_size'
)
async def test_get_comments_all(
    client, admin_access_token, post1, comment1, comment2, comment3
):
    resp = await client.get(
        url=f'/posts/{post1.id}/comments',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'page': 1,
        'total_pages': 1,
        'comments': [
            {
                'id': comment1.id,
                'text': comment1.text,
                'posted_at': str(comment1.posted_at).replace(' ', 'T'),
                'author': {
                    'id': comment1.author.id,
                    'username': comment1.author.username,
                    'full_name': comment1.author.full_name,
                },
                'post': {'id': post1.id},
            },
            {
                'id': comment2.id,
                'text': comment2.text,
                'posted_at': str(comment2.posted_at).replace(' ', 'T'),
                'author': {
                    'id': comment2.author.id,
                    'username': comment2.author.username,
                    'full_name': comment2.author.full_name,
                },
                'post': {'id': post1.id},
            },
            {
                'id': comment3.id,
                'text': comment3.text,
                'posted_at': str(comment3.posted_at).replace(' ', 'T'),
                'author': {
                    'id': comment3.author.id,
                    'username': comment3.author.username,
                    'full_name': comment3.author.full_name,
                },
                'post': {'id': post1.id},
            },
        ],
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures(
    'add_admin', 'add_three_posts', 'add_three_comments', 'mock_page_size'
)
async def test_get_comments_invalid_page(client, admin_access_token, post1):
    resp = await client.get(
        url=f'/posts/{post1.id}/comments?page=123',
        headers={'Authorization': f'Bearer {admin_access_token}'},
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json() == {'detail': 'Page number is too big'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_three_posts')
async def test_get_comments_invalid_page_dao(session, post1):
    with pytest.raises(InvalidPageNumException):
        await get_comments_by_post_id_and_page(session, post1.id, page=123)
