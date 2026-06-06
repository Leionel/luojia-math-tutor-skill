import pytest
from app.llm.openai_compatible import OpenAICompatibleClient
from app.config import get_settings

@pytest.mark.asyncio
async def test_create_embedding_fallback():
    client = OpenAICompatibleClient(get_settings())
    vec = await client.create_embedding("极限与连续", api_key="invalid_key")
    assert isinstance(vec, list)
    assert len(vec) == 0
