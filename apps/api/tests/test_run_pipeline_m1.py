import json
import tempfile
from pathlib import Path
from app.knowledge.pipeline.runner import run_pipeline


def test_run_pipeline_m1_end_to_end():
    repo_root = Path(__file__).resolve().parents[3]
    sample_input = repo_root / "data" / "sample_linear_algebra_ch5.md"
    assert sample_input.exists()

    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as f:
        temp_output = Path(f.name)

    try:
        data = run_pipeline(sample_input, temp_output, course_id="test_la_101")
        assert "document" in data
        assert "units" in data
        assert "relations" in data

        assert data["document"]["course_id"] == "test_la_101"
        assert len(data["units"]) >= 5
        assert len(data["relations"]) >= 2

        # Check file content on disk
        saved = json.loads(temp_output.read_text(encoding="utf-8"))
        assert len(saved["units"]) == len(data["units"])
    finally:
        if temp_output.exists():
            temp_output.unlink()
