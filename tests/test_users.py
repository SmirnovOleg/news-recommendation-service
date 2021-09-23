import pytest
from sqlalchemy import select
from starlette import status

from app.database.crud import UserAlreadyExistsException, create_admin
from app.database.models import User
from app.utils.auth import get_password_hash, verify_password
from tests.utils import create_access_token_without_exp


@pytest.mark.asyncio
async def test_register_new_user(client, session, admin, admin_password):
    resp = await client.post(
        url='/users',
        json={
            'username': admin.username,
            'full_name': admin.full_name,
            'password': admin_password,
        },
    )

    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json() == {
        'id': admin.id,
        'username': admin.username,
        'full_name': admin.full_name,
    }

    result = await session.execute(select(User).filter(User.username == admin.username))
    user_from_db = result.scalars().first()

    assert verify_password(admin_password, user_from_db.hashed_password)


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin')
async def test_register_existing_user(client, admin, admin_password):
    resp = await client.post(
        url='/users',
        json={
            'username': admin.username,
            'full_name': admin.full_name,
            'password': admin_password,
        },
    )

    assert resp.status_code == status.HTTP_409_CONFLICT
    assert resp.json() == {'detail': 'User with specified username already exists'}


@pytest.mark.asyncio
async def test_register_admin(session, admin, admin_password):
    await create_admin(
        session, admin.username, admin.full_name, get_password_hash(admin_password)
    )

    result = await session.execute(select(User).filter(User.username == admin.username))
    user_from_db = result.scalars().first()

    assert user_from_db.id == admin.id
    assert user_from_db.username == admin.username
    assert user_from_db.full_name == admin.full_name
    assert verify_password(admin_password, user_from_db.hashed_password)


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin')
async def test_register_existing_admin(session, admin, admin_password):
    with pytest.raises(UserAlreadyExistsException):
        await create_admin(
            session, admin.username, admin.full_name, get_password_hash(admin_password)
        )


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin')
async def test_login_for_access_token(
    mocker, client, admin, admin_password, admin_access_token
):
    mocker.patch(
        'app.routers.auth.create_access_token',
        side_effect=create_access_token_without_exp,
    )

    resp = await client.post(
        url='/token',
        data={
            'grant_type': '',
            'username': admin.username,
            'password': admin_password,
            'scope': '',
            'client_id': '',
            'client_secret': '',
        },
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {'access_token': admin_access_token, 'token_type': 'bearer'}


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin')
async def test_read_users_me(client, admin, admin_access_token):
    resp = await client.get(
        url='/users/me', headers={'Authorization': f'Bearer {admin_access_token}'}
    )

    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {
        'id': admin.id,
        'username': admin.username,
        'full_name': admin.full_name,
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin')
async def test_read_users_me_invalid_token(client, user_access_token):
    resp = await client.get(
        url='/users/me', headers={'Authorization': f'Bearer {user_access_token}'}
    )

    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp.json() == {'detail': 'Could not validate credentials'}
    assert resp.headers['WWW-Authenticate'] == 'Bearer'


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin')
async def test_login_for_access_token_with_incorrect_password(mocker, client, admin):
    mocker.patch(
        'app.routers.auth.create_access_token',
        side_effect=create_access_token_without_exp,
    )

    resp = await client.post(
        url='/token',
        data={
            'grant_type': '',
            'username': admin.username,
            'password': 'smth',
            'scope': '',
            'client_id': '',
            'client_secret': '',
        },
    )

    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp.json() == {'detail': 'Incorrect username or password'}
    assert resp.headers['WWW-Authenticate'] == 'Bearer'


@pytest.mark.asyncio
@pytest.mark.usefixtures('add_admin')
async def test_login_for_access_token_with_incorrect_login(
    mocker, client, admin_password, user
):
    mocker.patch(
        'app.routers.auth.create_access_token',
        side_effect=create_access_token_without_exp,
    )

    resp = await client.post(
        url='/token',
        data={
            'grant_type': '',
            'username': user.username,
            'password': admin_password,
            'scope': '',
            'client_id': '',
            'client_secret': '',
        },
    )

    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp.json() == {'detail': 'Incorrect username or password'}
    assert resp.headers['WWW-Authenticate'] == 'Bearer'
