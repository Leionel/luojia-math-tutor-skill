import asyncio
import httpx
import time
import os

AGENT_PARSE_API = "https://mineru.net/api/v1/agent/parse/file"
AGENT_TASK_API = "https://mineru.net/api/v1/agent/parse/"

async def extract_markdown_agent_api(filepath: str) -> str:
    """
    Use MinerU lightweight Agent API to extract markdown from a file.
    No token required. Rate limited by IP.
    """
    filename = os.path.basename(filepath)
    
    # 1. Create Task
    async with httpx.AsyncClient() as client:
        payload = {
            "file_name": filename,
            "enable_table": True,
            "enable_formula": True,
            "is_ocr": False
        }
        res = await client.post(AGENT_PARSE_API, json=payload, timeout=30.0)
        res_data = res.json()
        if res_data.get("code") != 0:
            raise Exception(f"Failed to create MinerU task: {res_data.get('msg')}")
        
        task_id = res_data["data"]["task_id"]
        file_url = res_data["data"]["file_url"]
        
    # 2. Upload File to OSS
    async with httpx.AsyncClient() as client:
        with open(filepath, "rb") as f:
            file_data = f.read()
        put_res = await client.put(file_url, content=file_data, timeout=60.0)
        if put_res.status_code not in (200, 201):
            raise Exception(f"Failed to upload file to MinerU OSS: {put_res.status_code}")
            
    # 3. Poll for result
    async with httpx.AsyncClient() as client:
        max_retries = 30 # 30 * 2s = 60s
        for _ in range(max_retries):
            await asyncio.sleep(2)
            task_res = await client.get(f"{AGENT_TASK_API}{task_id}", timeout=30.0)
            task_data = task_res.json()
            
            if task_data.get("code") != 0:
                raise Exception(f"Task query failed: {task_data.get('msg')}")
                
            state = task_data["data"]["state"]
            if state == "done":
                markdown_url = task_data["data"]["markdown_url"]
                # Fetch markdown content
                md_res = await client.get(markdown_url, timeout=30.0)
                return md_res.text
            elif state == "failed":
                err_msg = task_data["data"].get("err_msg", "Unknown error")
                raise Exception(f"MinerU parsing failed: {err_msg}")
            # else keep polling (waiting-file, pending, running)
            
        raise Exception("MinerU task polling timeout")
