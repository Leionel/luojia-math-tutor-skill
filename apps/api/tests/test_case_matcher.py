import pytest
from app.knowledge.case_schema import CaseDecision, TeachingCase
from app.knowledge.case_repository import TeachingCaseRepository
from app.knowledge.case_matcher import TeachingCaseMatcher


@pytest.fixture
def case_matcher():
    cases = [
        TeachingCase(
            case_id="CASE_NEWTON_INITIAL_VALUE",
            course_id="numerical_analysis",
            title="牛顿法初值敏感性与发散振荡排查",
            task_type="error_debugging",
            learning_objectives=["理解初值选择不当导致切线交点外溢、周期振荡或发散的原因"],
            concept_ids=["NA_NEWTON", "NA_LOCAL_CONVERGENCE", "NA_COUNTER_NEWTON_CYCLE"],
            required_condition_ids=["x_0 close to root"],
            accepted_variants=[
                "牛顿法为什么初值选不好会发散",
                "为什么牛顿法初值很重要",
                "牛顿迭代死循环怎么回事"
            ],
            diagnostic_probes=[
                {
                    "probe_id": "PROBE_NEWTON_INIT",
                    "question": "牛顿法是不是初值选在哪都能找到最近的根？",
                    "correct_answer": "不是，初值不合适可能导致迭代序列发散"
                }
            ],
            disclosure_policy="scaffolded"
        ),
        TeachingCase(
            case_id="CASE_NEWTON_MULTIPLE_ROOT",
            course_id="numerical_analysis",
            title="重根情形下牛顿法收敛性退化与改进格式",
            task_type="convergence_analysis",
            learning_objectives=["理解 m 重根导致牛顿法退化为线性收敛"],
            concept_ids=["NA_NEWTON", "MATH_MULTIPLE_ROOT", "NA_CONVERGENCE_ORDER"],
            required_condition_ids=["f'(x*)=0", "m > 1"],
            accepted_variants=[
                "重根情况下牛顿法的收敛阶是多少",
                "牛顿法算重根为什么变慢了"
            ],
            diagnostic_probes=[],
            disclosure_policy="scaffolded"
        ),
        TeachingCase(
            case_id="CASE_BISECTION_REQUIREMENTS",
            course_id="numerical_analysis",
            title="二分法使用条件与端点符号判断",
            task_type="concept_explanation",
            learning_objectives=["理解二分法成立的两个核心前提：连续性与端点函数值异号"],
            concept_ids=["NA_BISECTION", "MATH_CONTINUITY", "MATH_IVT"],
            required_condition_ids=["f(a)*f(b) < 0"],
            accepted_variants=[
                "二分法需要满足什么条件",
                "二分法什么时候可以用"
            ],
            diagnostic_probes=[],
            disclosure_policy="direct"
        )
    ]
    repo = TeachingCaseRepository(cases)
    return TeachingCaseMatcher(repo)


def test_match_exact_variant(case_matcher):
    res = case_matcher.match("牛顿法为什么初值选不好会发散")
    assert res.matched_case_id == "CASE_NEWTON_INITIAL_VALUE"
    assert res.decision in (CaseDecision.SAME_CASE, CaseDecision.VARIANT_OF_CASE)
    assert res.confidence >= 0.7
    assert res.diagnostic_probe is not None
    assert "PROBE_NEWTON_INIT" == res.diagnostic_probe["probe_id"]


def test_match_condition_divergence_variant(case_matcher):
    res = case_matcher.match("牛顿法求重根的收敛速度是多少？")
    assert res.matched_case_id == "CASE_NEWTON_MULTIPLE_ROOT"
    assert res.confidence > 0.4
    assert res.decision in (CaseDecision.SAME_CASE, CaseDecision.VARIANT_OF_CASE, CaseDecision.RELATED_CASE)


def test_match_unknown_topic_yields_new_case(case_matcher):
    res = case_matcher.match("请问薛定谔方程的波函数怎么在球坐标系下分离变量？")
    assert res.decision == CaseDecision.NEW_CASE
    assert res.review_required is True
    assert res.matched_case_id is None
