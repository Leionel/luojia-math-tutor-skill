from app.config import get_settings
from app.tutor.prompt_policy import load_teaching_prompt, PROMPT_VERSION


def test_visual_protocol_is_in_actual_teaching_prompt():
    prompt = load_teaching_prompt(get_settings().skill_file)
    assert PROMPT_VERSION == "teaching-v2.4"
    assert "visual-v1" in prompt
    assert '<plot function="x^2-1" domain="-2,2" />' in prompt
    assert "不能据此宣称连续" in prompt
    assert "禁止外联、iframe、文件和父页面访问" in prompt
