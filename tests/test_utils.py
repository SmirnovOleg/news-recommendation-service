# pylint: disable=too-many-arguments
import base64

import pytest
from fastapi import HTTPException

from app.utils.common import (
    base64_optional_encode,
    get_post_or_throw_not_found_exception,
)


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_three_posts')
async def test_get_post_or_throw_not_found_exception(session):
    with pytest.raises(HTTPException):
        await get_post_or_throw_not_found_exception(session, post_id=123)


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_three_posts')
async def test_get_post_common_util(session, post1):
    post = await get_post_or_throw_not_found_exception(session, post_id=post1.id)
    assert post.id == post1.id
    assert post.header == post1.header
    assert post.text == post1.text


@pytest.mark.asyncio
async def test_base64_optional_encode():
    assert base64_optional_encode(''.encode()) == base64.b64encode(''.encode())
    assert base64_optional_encode(None) is None
