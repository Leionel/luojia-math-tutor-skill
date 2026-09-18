import pytest
from app.knowledge.boundary import BoundaryChecker, BoundaryPolicy, ScopeLevel


@pytest.fixture
def boundary_checker():
    checker = BoundaryChecker()
    checker.set_policy(BoundaryPolicy(
        course_id="numerical_analysis",
        unit_id="NA_NEWTON",
        scope_level=ScopeLevel.CORE.value,
        max_expansion_depth=2
    ))
    checker.set_policy(BoundaryPolicy(
        course_id="numerical_analysis",
        unit_id="MATH_CONTINUITY",
        scope_level=ScopeLevel.PREREQUISITE.value,
        max_expansion_depth=1
    ))
    checker.set_policy(BoundaryPolicy(
        course_id="numerical_analysis",
        unit_id="NA_COUNTER_NEWTON_CYCLE",
        scope_level=ScopeLevel.EXTENSION.value,
        max_expansion_depth=1
    ))
    checker.set_policy(BoundaryPolicy(
        course_id="numerical_analysis",
        unit_id="OPT_MULTIVARIATE",
        scope_level=ScopeLevel.EXTERNAL.value,
        max_expansion_depth=0
    ))
    return checker


def test_core_unit_expansion_allowed(boundary_checker):
    allowed, reason = boundary_checker.can_expand("NA_NEWTON", current_depth=1)
    assert allowed is True
    assert reason == "allowed"

    # Beyond max_expansion_depth=2
    allowed_deep, reason_deep = boundary_checker.can_expand("NA_NEWTON", current_depth=3)
    assert allowed_deep is False
    assert "exceeds_max" in reason_deep


def test_extension_expansion_blocked_when_disallowed(boundary_checker):
    allowed_no_ext, _ = boundary_checker.can_expand("NA_COUNTER_NEWTON_CYCLE", current_depth=1, allow_extension=False)
    assert allowed_no_ext is False

    allowed_ext, _ = boundary_checker.can_expand("NA_COUNTER_NEWTON_CYCLE", current_depth=1, allow_extension=True)
    assert allowed_ext is True


def test_external_unit_expansion_strictly_blocked(boundary_checker):
    allowed, reason = boundary_checker.can_expand("OPT_MULTIVARIATE", current_depth=1, allow_extension=True)
    assert allowed is False
    assert reason == "external_boundary_blocked"


def test_filter_units_respects_boundary(boundary_checker):
    uids = ["NA_NEWTON", "MATH_CONTINUITY", "NA_COUNTER_NEWTON_CYCLE", "OPT_MULTIVARIATE"]

    # Core only
    core_filtered = boundary_checker.filter_units(uids, allow_extension=False, allow_prerequisite=False)
    assert core_filtered == ["NA_NEWTON"]

    # Core + Prerequisite
    prereq_filtered = boundary_checker.filter_units(uids, allow_extension=False, allow_prerequisite=True)
    assert prereq_filtered == ["NA_NEWTON", "MATH_CONTINUITY"]

    # Core + Prerequisite + Extension
    full_filtered = boundary_checker.filter_units(uids, allow_extension=True, allow_prerequisite=True)
    assert "NA_COUNTER_NEWTON_CYCLE" in full_filtered
    assert "OPT_MULTIVARIATE" not in full_filtered


def test_untracked_units_fail_closed(boundary_checker):
    # A unit without a policy is UNCLASSIFIED and must not be treated as core.
    assert boundary_checker.get_scope_level("NA_UNKNOWN_UNIT") == ScopeLevel.UNCLASSIFIED

    allowed, reason = boundary_checker.can_expand("NA_UNKNOWN_UNIT", current_depth=1)
    assert allowed is False
    assert reason == "unclassified_requires_teacher_review"

    # Candidate evidence only: excluded unless explicitly allowed.
    assert boundary_checker.filter_units(["NA_UNKNOWN_UNIT"]) == []
    assert boundary_checker.filter_units(["NA_UNKNOWN_UNIT"], allow_unclassified=True) == ["NA_UNKNOWN_UNIT"]


def test_inspect_boundary_decision_typed_contract(boundary_checker):
    decision = boundary_checker.inspect_boundary_decision(
        ["NA_NEWTON", "MATH_CONTINUITY", "OPT_MULTIVARIATE", "NA_UNKNOWN_UNIT"],
        allow_extension=False,
    )
    assert decision.core_units == ["NA_NEWTON"]
    assert decision.prerequisite_units == ["MATH_CONTINUITY"]
    assert decision.extension_units == []
    assert decision.unclassified_units == ["NA_UNKNOWN_UNIT"]
    assert decision.crossing_type == "external_boundary"
    assert decision.has_boundary_crossing is True

    as_dict = decision.to_dict()
    assert as_dict["blocked_units"] == [{"unit_id": "OPT_MULTIVARIATE", "reason": "external_boundary"}]

    # Round-trips through the dict contract used by prompt_builder.
    restored = type(decision).from_dict(as_dict)
    assert restored.core_units == decision.core_units
    assert restored.unclassified_units == decision.unclassified_units
