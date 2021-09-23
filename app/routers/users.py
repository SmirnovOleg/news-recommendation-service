from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import UserAlreadyExistsException, create_user
from app.database.models import User
from app.database.sqlite import db
from app.schema import UserRegisterRequestBodyModel, UserResponseModel
from app.utils.auth import get_current_active_user, get_password_hash

router = APIRouter()


@router.post('/users', status_code=status.HTTP_201_CREATED)
async def register_new_user(
    body: UserRegisterRequestBodyModel, session: AsyncSession = Depends(db.get_session)
) -> UserResponseModel:
    try:
        user = await create_user(
            session,
            body.username,
            body.full_name,
            get_password_hash(body.password.get_secret_value()),
        )
    except UserAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User with specified username already exists',
        ) from e

    return UserResponseModel(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
    )


@router.get('/users/me', response_model=UserResponseModel)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponseModel:
    return UserResponseModel(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
    )
