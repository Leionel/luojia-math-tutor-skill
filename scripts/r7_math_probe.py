"""Recompute the R7 first-error witness through persisted root episodes; no model."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def capture():
    os.environ['LUOJIA_NO_DOTENV'] = '1'
    sys.path.insert(0, str(ROOT / 'apps/api'))
    from app.knowledge.course_service import CourseService
    from app.knowledge.course_store import CourseStore
    from app.math_tools.root_finding import RootAttempt
    from app.tutor.root_diagnostics import RootEpisodeService, RootSubmission, feedback_text
    records = []
    with tempfile.TemporaryDirectory(prefix='r7-math-') as directory:
        db = Path(directory) / 'course.db'
        service = RootEpisodeService(CourseService(store=CourseStore(db)))
        for name, extra, xs in (
            ('newton-domain-tail', {}, [1, 3, 4, -1]),
            ('newton-nonfinite-tail', {}, [1, 3, 4, 'NaN']),
            ('fixed-point-domain-tail', {'method': 'fixed_point', 'phi': '(x+4)/2', 'initial_value': 0}, [0, 2, 4, -1]),
        ):
            attempt = dict(method='newton', function='sqrt(x)-2', initial_value=1,
                           goal='residual', iterates=xs)
            attempt.update(extra)
            public = service.submit('r7-synthetic', name, RootSubmission(
                attempt_id=name, attempt=RootAttempt(**attempt)))
            reopened = RootEpisodeService(CourseService(store=CourseStore(db)))
            restored = reopened.replay('r7-synthetic', name, public['episode_id'])
            records.append(dict(case_id=name, input=attempt, report=public,
                                feedback=feedback_text(public), restored=restored))
            reopened.store.close()
        service.store.close()
    return dict(version='r7-first-error-probe-v1',
                head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                source_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
                    'apps/api/app/math_tools/root_finding.py', 'apps/api/app/tutor/root_diagnostics.py')},
                scope='real deterministic computation and persisted episodes; not model quality',
                provider_requests=0, quality=None, records=records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to(ROOT/'results') or target.exists():
        parser.error('use a new path inside results/; preserve before evidence')
    target.parent.mkdir(parents=True, exist_ok=True)
    data = capture()
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps([{'id': r['case_id'], 'first_error': r['report']['error_step'],
                       'family': r['report']['family']} for r in data['records']]))
