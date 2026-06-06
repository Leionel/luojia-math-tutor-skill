import pytest
from unittest.mock import patch, AsyncMock
import httpx
import logging
from app.llm.openai_compatible import OpenAICompatibleClient
from app.config import get_settings

@pytest.mark.asyncio
async def test_create_embedding_success():
    client = OpenAICompatibleClient(get_settings())
    
    mock_response_data = {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "index": 0,
                "embedding": [0.1, 0.2, 0.3, 0.4]
            }
        ],
        "model": "text-embedding-v3",
        "usage": {"prompt_tokens": 5, "total_tokens": 5}
    }
    
    mock_response = httpx.Response(
        status_code=200,
        json=mock_response_data,
        request=httpx.Request("POST", "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings")
    )
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        vec = await client.create_embedding("极限与连续", api_key="test_key", model="text-embedding-v3")
        
        assert vec == [0.1, 0.2, 0.3, 0.4]
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["input"] == "极限与连续"
        assert kwargs["json"]["model"] == "text-embedding-v3"
        assert kwargs["headers"]["Authorization"] == "Bearer test_key"


@pytest.mark.asyncio
async def test_create_embedding_fallback(caplog):
    client = OpenAICompatibleClient(get_settings())
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.HTTPError("Mocked network error")
        
        with caplog.at_level(logging.ERROR):
            vec = await client.create_embedding("极限与连续", api_key="invalid_key")
            
            assert isinstance(vec, list)
            assert len(vec) == 0
            mock_post.assert_called_once()
            
            # 确认有错误日志输出
            assert any("Embedding API call failed" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_create_embedding_api_key_redirect(monkeypatch):
    settings = get_settings()
    original_llm_api_key = settings.llm_api_key
    settings.llm_api_key = ""
    
    client = OpenAICompatibleClient(settings)
    monkeypatch.setenv("QWEN_API_KEY", "mocked_qwen_key")
    
    mock_response = httpx.Response(
        status_code=200,
        json={"data": [{"embedding": [0.1]}]},
        request=httpx.Request("POST", "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings")
    )
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        await client.create_embedding("测试文本", model="qwen-embedding")
        
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer mocked_qwen_key"
        
    settings.llm_api_key = original_llm_api_key


@pytest.mark.asyncio
async def test_create_embedding_model_routing_priority():
    settings = get_settings()
    original_provider = settings.llm_provider
    settings.llm_provider = "glm"
    
    client = OpenAICompatibleClient(settings)
    
    mock_response = httpx.Response(
        status_code=200,
        json={"data": [{"embedding": [0.1]}]},
        request=httpx.Request("POST", "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings")
    )
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        await client.create_embedding("测试文本", api_key="test_key", model="text-embedding-v3")
        
        mock_post.assert_called_once()
        url = str(mock_post.call_args[0][0])
        assert "dashscope.aliyuncs.com" in url
        
    settings.llm_provider = original_provider


@pytest.mark.asyncio
async def test_create_embedding_moonshot_default():
    settings = get_settings()
    original_provider = settings.llm_provider
    settings.llm_provider = "moonshot"
    
    client = OpenAICompatibleClient(settings)
    
    mock_response = httpx.Response(
        status_code=200,
        json={"data": [{"embedding": [0.1]}]},
        request=httpx.Request("POST", "https://api.moonshot.cn/v1/embeddings")
    )
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        await client.create_embedding("测试文本", api_key="test_key")
        
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "moonshot-embed"
        
    settings.llm_provider = original_provider
