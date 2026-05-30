from fastapi import APIRouter

router = APIRouter(tags=["Mastery"])

@router.get("/users/{user_id}/mastery")
def get_user_mastery(user_id: str):
    return [
        {"subject": "微积分", "A": 80, "fullMark": 100},
        {"subject": "线性代数", "A": 65, "fullMark": 100},
        {"subject": "概率统计", "A": 90, "fullMark": 100},
        {"subject": "深度推导", "A": 50, "fullMark": 100},
        {"subject": "逻辑基础", "A": 70, "fullMark": 100}
    ]
