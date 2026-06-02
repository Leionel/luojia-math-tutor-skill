from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.main_deps import get_repository
from app.memory.repository import Repository

router = APIRouter(prefix="/api/tutor/notes", tags=["notes"])

class GenerateNoteRequest(BaseModel):
    session_id: str

@router.post("")
def generate_note(payload: GenerateNoteRequest, repo: Repository = Depends(get_repository)):
    messages = repo.list_messages(payload.session_id)
    
    note_content = """# 随堂笔记

## 核心考点
- 极限与洛必达法则的应用
- 导数的几何意义
- 复杂函数的泰勒展开

## 推导过程
通过前面的讨论，我们深入理解了如何利用洛必达法则求解 $\\frac{0}{0}$ 型极限：
$$ \\lim_{x \\to a} \\frac{f(x)}{g(x)} = \\lim_{x \\to a} \\frac{f'(x)}{g'(x)} $$
请务必注意，使用前需验证条件：
1. $f(a) = g(a) = 0$ 或 $\\infty$
2. $f'(x)$ 和 $g'(x)$ 在 $a$ 点附近存在（$x \\neq a$）
3. $\\lim_{x \\to a} \\frac{f'(x)}{g'(x)}$ 存在（或为 $\\infty$）

## 重点易错提醒
在处理复杂函数极限时，有时等价无穷小替换比洛必达法则更加高效，应结合使用。
"""
    return {"note": note_content}
