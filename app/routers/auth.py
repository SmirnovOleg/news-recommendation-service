from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.database.sqlite import db
from app.schema import TokenResponseModel
from app.utils.auth import authenticate_user, create_access_token

router = APIRouter()


@router.post('/token', response_model=TokenResponseModel)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(db.get_session),
) -> TokenResponseModel:
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.username}, expires_delta=access_token_expires
    )
    return TokenResponseModel(access_token=access_token, token_type='bearer')
