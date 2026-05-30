"""提示策略测试。"""
from app.tutor.hint_policy import HintLevel, decide_hint_level, hint_level_instruction


class TestDecideHintLevel:
    def test_direct_mode_gives_near_answer(self):
        level = decide_hint_level(0.8, 0, False, mode="direct")
        assert level == HintLevel.NEAR_ANSWER

    def test_high_mastery_no_errors_independent(self):
        level = decide_hint_level(0.8, 0, False)
        assert level == HintLevel.INDEPENDENT

    def test_user_requested_hint(self):
        level = decide_hint_level(0.8, 0, True)
        assert level >= HintLevel.LIGHT_HINT

    def test_one_consecutive_error(self):
        level = decide_hint_level(0.5, 1, False)
        assert level >= HintLevel.LIGHT_HINT

    def test_two_consecutive_errors(self):
        level = decide_hint_level(0.5, 2, False)
        assert level >= HintLevel.FORMULA_HINT

    def test_three_consecutive_errors(self):
        level = decide_hint_level(0.5, 3, False)
        assert level == HintLevel.NEAR_ANSWER

    def test_low_mastery_upgrades(self):
        level = decide_hint_level(0.15, 0, False)
        assert level >= HintLevel.FORMULA_HINT

    def test_medium_low_mastery(self):
        level = decide_hint_level(0.35, 0, False)
        assert level >= HintLevel.LIGHT_HINT

    def test_never_exceeds_near_answer(self):
        level = decide_hint_level(0.0, 10, True, mode="socratic")
        assert level == HintLevel.NEAR_ANSWER


class TestHintInstruction:
    def test_all_levels_have_instructions(self):
        for level in HintLevel:
            text = hint_level_instruction(level)
            assert len(text) > 10
