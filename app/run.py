import uvicorn

from app.database.crud import create_admin, create_post, get_user_by_username
from app.database.redis import redis
from app.database.sqlite import db
from app.factory import create_app
from app.utils.auth import get_password_hash

main_app = create_app()


@main_app.on_event('startup')
async def startup_event() -> None:
    # Initialize SQLite asynchronously
    await db.init()

    # Add Admin if it doesn't already exist
    async with db.create_session() as session:
        if not await get_user_by_username(session=session, username='admin'):
            user = await create_admin(
                session=session,
                username='admin',
                full_name='Some Name',
                hashed_password=get_password_hash('12345'),
            )
            await create_post(
                session=session,
                header='USA starts withdrawal of troops from Afghanistan',
                photo=b'',
                text='',
                author=user,
            )
            await create_post(
                session=session,
                header='Trump is the first American President being impeached twice',
                photo=b'',
                text='',
                author=user,
            )
            await create_post(
                session=session,
                header='Havertz double leaves Fulham in trouble',
                photo=b'',
                text='',
                author=user,
            )
            await create_post(
                session=session,
                header='Manchester City could clinch the Football Premier League',
                photo=b'',
                text='',
                author=user,
            )
            await create_post(
                session=session,
                header='La Liga: Real Madrid vs Osasuna - who will win the first prize?',
                photo=b'',
                text='',
                author=user,
            )

    # Initialize Redis asynchronously
    await redis.init()


@main_app.on_event('shutdown')
async def shutdown_event() -> None:
    await redis.close()


if __name__ == '__main__':
    # Only for debugging within the PyCharm IDE.
    # To run this app from terminal use `docker-compose up`
    uvicorn.run(main_app, host='0.0.0.0', port=8000)
