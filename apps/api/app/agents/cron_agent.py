import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from app.memory.repository import Repository
from app.config import get_settings
from app.llm.openai_compatible import OpenAICompatibleClient

logger = logging.getLogger(__name__)

async def run_proactive_review_cron():
    """
    Scans the mastery table for concepts with score < 0.5.
    Generates a proactive review message for the user.
    """
    settings = get_settings()
    repo = Repository(settings)
    llm = OpenAICompatibleClient(settings)
    
    with repo.connect() as conn:
        # Find concepts needing review
        # In a real app, we would join with users table.
        # For MVP, we just find any mastery record < 0.5 that hasn't been pushed recently.
        cursor = conn.execute(
            """
            SELECT id, user_id, concept, score, last_pushed_at 
            FROM mastery 
            WHERE score < 0.5
            """
        )
        records = cursor.fetchall()
        
        for record in records:
            user_id = record["user_id"]
            concept = record["concept"]
            score = record["score"]
            last_pushed = record["last_pushed_at"]
            
            # Simple debounce: if we pushed recently, skip. 
            # For testing, we might ignore this or just check if it's null.
            if last_pushed:
                # Basic check, just skip if it has ever been pushed for MVP
                continue
                
            logger.info(f"CronAgent: Generating review for user {user_id} on concept {concept} (score {score})")
            
            # Generate the review message
            prompt = f"你是一个温柔耐心的数学私教。你的学生最近在学习“{concept}”时遇到了困难，经常做错。请写一段简短的、充满鼓励的复习话术，主动引导他今天复习这个知识点。可以举一个小例子。字数不要超过150字。"
            
            messages = [
                {"role": "system", "content": "你是一个主动关怀学生的AI助教。"},
                {"role": "user", "content": prompt}
            ]
            
            ai_message = await llm.chat_completion(messages)
            if not ai_message:
                ai_message = "看来你需要复习一下" + concept + "，快来练习吧！"
            
            # Find the user's latest session to push the message into
            session_cursor = conn.execute(
                "SELECT id FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            session_row = session_cursor.fetchone()
            
            if session_row:
                session_id = session_row["id"]
                # Insert the proactive message
                import uuid
                from app.memory.models import now_iso
                msg_id = f"msg_{uuid.uuid4().hex[:8]}"
                conn.execute(
                    "INSERT INTO messages (id, session_id, role, content, intent, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (msg_id, session_id, "assistant", ai_message, "proactive_review", now_iso())
                )
                
                # Mark as pushed
                conn.execute(
                    "UPDATE mastery SET last_pushed_at = ? WHERE id = ?",
                    (now_iso(), record["id"])
                )
                
                logger.info(f"CronAgent: Pushed message to session {session_id}")
            
    return {"status": "ok", "records_processed": len(records)}

if __name__ == "__main__":
    asyncio.run(run_proactive_review_cron())
