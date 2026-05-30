"""掌握度更新算法测试。"""
import pytest

from app.memory.mastery import MasteryUpdate, mastery_label, update_mastery


class TestUpdateMastery:
    def test_correct_independent_increases(self):
        result = update_mastery(0.5, is_correct=True, hint_level=0)
        assert result.new_score == pytest.approx(0.58)
        assert result.delta > 0

    def test_correct_with_hint_increases_less(self):
        result = update_mastery(0.5, is_correct=True, hint_level=2)
        assert result.new_score == pytest.approx(0.53)
        assert result.delta > 0

    def test_incorrect_decreases(self):
        result = update_mastery(0.5, is_correct=False)
        assert result.new_score == pytest.approx(0.44)
        assert result.delta < 0

    def test_score_capped_at_1(self):
        result = update_mastery(0.97, is_correct=True, hint_level=0)
        assert result.new_score == 1.0

    def test_score_floored_at_0(self):
        result = update_mastery(0.02, is_correct=False)
        assert result.new_score == 0.0

    def test_reason_independent(self):
        result = update_mastery(0.5, is_correct=True, hint_level=0)
        assert "独立" in result.reason

    def test_reason_with_hint(self):
        result = update_mastery(0.5, is_correct=True, hint_level=2)
        assert "提示" in result.reason

    def test_reason_wrong(self):
        result = update_mastery(0.5, is_correct=False)
        assert "答错" in result.reason


class TestMasteryLabel:
    def test_labels(self):
        assert mastery_label(0.9) == "熟练"
        assert mastery_label(0.7) == "掌握"
        assert mastery_label(0.5) == "一般"
        assert mastery_label(0.3) == "薄弱"
        assert mastery_label(0.1) == "未掌握"
