"""掌握度更新算法测试。"""
import pytest

from app.memory.mastery import MasteryUpdate, mastery_label, update_mastery


def test_bkt_independent_correct():
    # P(L) = 0.3
    # P(S) = 0.1, P(G) = 0.1, P(T) = 0.15
    # P(L|obs) = (0.3 * 0.9) / (0.3 * 0.9 + 0.7 * 0.1) = 0.27 / (0.27 + 0.07) = 0.27 / 0.34 ≈ 0.794
    # P(new) = 0.794 + (1 - 0.794) * 0.15 = 0.794 + 0.0309 ≈ 0.825
    res = update_mastery(0.3, is_correct=True, hint_level=0)
    assert 0.82 < res.new_score < 0.83
    assert res.reason == "独立正确解答，掌握度显著上升"


def test_bkt_hint_correct():
    # hint_level = 1 => P(G) = 0.40, P(T) = 0.05
    # P(L|obs) = (0.3 * 0.9) / (0.3 * 0.9 + 0.7 * 0.4) = 0.27 / (0.27 + 0.28) = 0.27 / 0.55 ≈ 0.491
    # P(new) = 0.491 + (1 - 0.491) * 0.05 = 0.491 + 0.025 ≈ 0.516
    res = update_mastery(0.3, is_correct=True, hint_level=1)
    assert 0.51 < res.new_score < 0.52
    assert res.reason == "借助少许提示解答，掌握度小幅上升"


def test_bkt_incorrect():
    # P(L) = 0.3
    # P(S) = 0.1, P(G) = 0.1
    # P(L|obs) = (0.3 * 0.1) / (0.3 * 0.1 + 0.7 * 0.9) = 0.03 / (0.03 + 0.63) = 0.03 / 0.66 ≈ 0.045
    # P(new) = 0.045 + (1 - 0.045) * 0.15 = 0.045 + 0.143 ≈ 0.188
    res = update_mastery(0.3, is_correct=False, hint_level=0)
    assert 0.18 < res.new_score < 0.19
    assert res.reason == "回答错误，掌握度下降"


class TestMasteryLabel:
    def test_labels(self):
        assert mastery_label(0.9) == "熟练"
        assert mastery_label(0.7) == "掌握"
        assert mastery_label(0.5) == "一般"
        assert mastery_label(0.3) == "薄弱"
        assert mastery_label(0.1) == "未掌握"
