from fastapi import FastAPI

from app.routers import auth, comments, posts, users


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(posts.router)
    app.include_router(comments.router)
    return app
