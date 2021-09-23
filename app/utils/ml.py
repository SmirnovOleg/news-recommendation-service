import asyncio
import pickle
from pathlib import Path
from typing import List

import torch
from sentence_transformers import SentenceTransformer, util
from sqlalchemy.ext.asyncio import AsyncSession
from torch import Tensor

from app.config import (
    K_NEAREST_NEIGHBOURS,
    MODEL_DIRECTORY_NAME,
    MODEL_NAME,
    POSTS_SIMILARITY_THRESHOLD,
)
from app.database.crud import get_all_posts_for_last_week
from app.database.models import Post
from app.database.redis import redis

path_to_model = Path(__file__).parent.parent.parent / '.model' / MODEL_DIRECTORY_NAME
if path_to_model.exists():  # pragma: no cover
    model = SentenceTransformer(model_name_or_path=str(path_to_model.absolute()))
else:
    model = SentenceTransformer(model_name_or_path=MODEL_NAME)


async def get_or_calculate_embedding_of_header(header: str) -> Tensor:
    if await redis.exists(header):
        pickled_tensor = await redis.get(header)
        return pickle.loads(pickled_tensor)

    embedding = model.encode(header, convert_to_tensor=True)
    await redis.set(header, pickle.dumps(embedding))
    return embedding


async def find_similar_recent_posts(
    session: AsyncSession, original_post: Post
) -> List[Post]:
    recent_posts = await get_all_posts_for_last_week(session)
    headers = [post.header for post in recent_posts]

    original_header_embedding = await get_or_calculate_embedding_of_header(
        original_post.header
    )
    all_headers_embeddings = await asyncio.gather(
        *[get_or_calculate_embedding_of_header(header) for header in headers]
    )

    # pylint: disable=no-member
    cosine_scores = util.pytorch_cos_sim(
        a=original_header_embedding.unsqueeze(dim=0),
        b=torch.cat([tensor.unsqueeze(dim=0) for tensor in all_headers_embeddings]),
    )

    post2score = {post: cosine_scores[0][i] for i, post in enumerate(recent_posts)}
    filtered_posts = filter(
        lambda post: post2score[post] > POSTS_SIMILARITY_THRESHOLD, recent_posts
    )
    sorted_posts = sorted(
        filtered_posts, key=lambda post: post2score[post], reverse=True
    )

    # Skip the first embedding since it corresponds to the original post itself
    return sorted_posts[1 : 1 + K_NEAREST_NEIGHBOURS]
