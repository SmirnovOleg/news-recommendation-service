from pydantic import BaseSettings, RedisDsn

HASHING_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

PAGE_SIZE = 2

K_NEAREST_NEIGHBOURS = 3
POSTS_SIMILARITY_THRESHOLD = 0.4
MODEL_NAME = 'average_word_embeddings_glove.6B.300d'
MODEL_DIRECTORY_NAME = f'sbert.net_models_{MODEL_NAME}'


class EnvSettings(BaseSettings):
    redis_url: RedisDsn = 'redis://localhost:6379/0'  # type: ignore
    sqlite_url: str = 'sqlite+aiosqlite:///news.db'  # type: ignore
    secret_key: str

    class Config:
        case_sensitive = False


settings = EnvSettings()
