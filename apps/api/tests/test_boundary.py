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
