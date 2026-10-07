"""S5.1: validate/replay offline observations, or print a no-network execution plan."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import os

from s5_quality import build_report, digest, load_json, validate_manifest, valid_sha

ROOT = Path(__file__).resolve().parents[1]


def provenance() -> dict:
    def git(*args):
        result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    files = sorted([*(ROOT / 'apps/api/app').rglob('*.py'), ROOT / 'scripts/s5_quality.py', ROOT / 'scripts/s5_runtime_capture.py', ROOT / 'scripts/s5_content.py', ROOT / 'scripts/s5_episode_capture.py', Path(__file__)])
    return {'report_builder_sha': git('rev-parse', 'HEAD'),
            'report_builder_source_dirty': bool(git('status', '--porcelain')),
            'source_sha256': {p.relative_to(ROOT).as_posix(): digest(p) for p in files}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'evaluation/s5/manifest.json')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--offline', action='store_true')
    mode.add_argument('--dry-run', action='store_true')
    parser.add_argument('--observations', type=Path)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--recorded-answers',type=Path,help='bounded public-case answer sidecar; caller supplied, not authenticated')
    parser.add_argument('--capture-fixtures', action='store_true', help='owned real graph/worker with fixed model, fresh temporary databases')
    parser.add_argument('--capture-episodes',action='store_true',help='two fixed-model in-process ASGI development workflows')
    parser.add_argument('--markdown-output', type=Path)
    parser.add_argument('--review-packet-output', type=Path)
    parser.add_argument('--content-markdown-output', type=Path)
    parser.add_argument('--profile', type=Path, help='sanitized planning metadata; never credentials or endpoint URLs')
    parser.add_argument('--output', type=Path, default=ROOT / 'results/s5-offline.json')
    args = parser.parse_args(argv)
    try:
        if args.capture_fixtures and args.capture_episodes:raise ValueError('choose one capture mode')
        if args.offline and args.profile:
            raise ValueError('profile is only accepted in dry-run')
        manifest = load_json(args.manifest)
        cases = validate_manifest(manifest)
        mh = digest(args.manifest)
        from s5_content import validate_content, exact_math_checks, prepare_review_packet, render_content
        content = validate_content(args.manifest)
        outputs=[x.resolve() for x in (args.output,args.markdown_output,args.review_packet_output,args.content_markdown_output) if x]
        inputs={x.resolve() for x in (args.manifest,args.observations,args.reviews,args.profile,args.recorded_answers) if x}
        if manifest.get('content_file'):inputs.add((args.manifest.resolve().parent/manifest['content_file']).resolve())
        if len(outputs)!=len(set(outputs)) or any(x in inputs for x in outputs):raise ValueError('outputs must not overwrite inputs or each other')
        obs = load_json(args.observations) if args.observations else None
        if args.recorded_answers:
            if not args.offline or args.observations or args.capture_fixtures or args.capture_episodes:
                raise ValueError('recorded answers require offline without other observation sources')
            from s5_content import recorded_answers_to_observations
            obs=recorded_answers_to_observations(args.manifest,args.recorded_answers)
        if args.capture_fixtures or args.capture_episodes:
            if not args.offline or args.observations or args.reviews:
                raise ValueError('capture-fixtures requires offline, without supplied observations or reviews')
            capture_ids={'episode-newton-reference','episode-linear-revision'} if args.capture_episodes else {'runtime-correct','runtime-incorrect','runtime-reference','runtime-unknown'}
            if manifest['split'] != 'runner_fixture' or {c['id'] for c in cases} != capture_ids:
                raise ValueError('capture only supports its fixed public cases')
            env = {k: v for k,v in os.environ.items() if 'KEY' not in k and 'TOKEN' not in k}
            env.update(LUOJIA_NO_DOTENV='1',PYTHONUTF8='1')
            with tempfile.TemporaryDirectory(prefix='s5-capture-output-') as folder:
                captured=Path(folder)/'observations.json'
                process=subprocess.run([sys.executable,str(ROOT/('scripts/s5_episode_capture.py' if args.capture_episodes else 'scripts/s5_runtime_capture.py')),
                    str(args.manifest.resolve()),str(captured)],env=env,capture_output=True,timeout=100)
                if process.returncode or not captured.exists():
                    raise ValueError('runtime capture failed; no quality result inferred')
                obs=load_json(captured)
        reviews = load_json(args.reviews) if args.reviews else None
        report = build_report(manifest, mh, obs, reviews, dry_run=args.dry_run)
        profile = load_json(args.profile) if args.profile else None
        # Planning only. S5.3 must implement real transport reservation and cost bounds.
        pending = ['live_execution_not_implemented', 'live_consumption_not_authorized']
        profile_summary = None
        if profile is not None:
            if set(profile) != {'version', 'model_label', 'endpoint_sha256', 'max_requests', 'currency', 'max_cost'}:
                raise ValueError('profile must contain only sanitized planning fields')
            if profile['version'] != 's5-plan-profile-v1' or not valid_sha(profile['endpoint_sha256']):
                raise ValueError('invalid profile version or endpoint hash')
            if not isinstance(profile['model_label'], str) or not 1 <= len(profile['model_label']) <= 80:
                raise ValueError('invalid model label')
            if type(profile['max_requests']) is not int or profile['max_requests'] < 0:
                raise ValueError('invalid request proposal')
            if profile['currency'] not in {None, 'CNY', 'USD'}:
                raise ValueError('invalid proposed currency')
            cost = profile['max_cost']
            if cost is not None and (type(cost) not in {int, float} or not math.isfinite(cost) or cost <= 0):
                raise ValueError('invalid cost proposal')
            profile_summary = {k: profile[k] for k in ('endpoint_sha256', 'max_requests', 'currency', 'max_cost')}
            profile_summary['model_label_sha256'] = hashlib.sha256(profile['model_label'].encode()).hexdigest()
        planned_runs = sum(c['planned_runs'] for c in cases)
        proposed_requests = planned_runs * 6
        if profile is None:
            pending.append('profile_not_supplied')
        elif profile['max_requests'] < proposed_requests:
            pending.append('proposed_request_limit_below_worst_case')
        if profile is None or profile['currency'] is None or profile['max_cost'] is None:
            pending.append('cost_proposal_missing')
        pending.append('provider_billable_upper_bound_not_verified')
        report.update(provenance())
        if args.recorded_answers:
            report['recording_provenance']={'attestation':'caller_supplied_unverified','source_sha256':digest(args.recorded_answers),'runtime_versions':'not_provided'}
        if content is not None:
            report['content_review'] = {'content_sha256':manifest['content_sha256'],'prepared_cases':len(content['cases']),'agent_prepared_only':True,'human_review':'pending','independent_human_review':'pending'}
            report['independent_arithmetic'] = exact_math_checks()
        report['input_artifact_sha256'] = {name: digest(path) for name, path in
            [('manifest', args.manifest), ('observations', args.observations), ('reviews', args.reviews), ('profile', args.profile),('recorded_answers',args.recorded_answers)] if path}
        report['preflight'] = {'planned_runs': planned_runs, 'worst_case_requests_without_probe': proposed_requests,
                               'per_run_assumed_request_cap': 6, 'protocol_probe_requests': 0,
                               'profile': profile_summary, 'live_ready': False, 'pending': pending}
        report['profile_versions'] = {'prompt': 'teaching-v2.6', 'guard': 'delivery-v2', 'checker': 'step-v1',
                                      'meaning': 'current source contracts; replay is not a live run under these versions'}
        if args.review_packet_output:
            packet=prepare_review_packet(args.manifest)
            args.review_packet_output.parent.mkdir(parents=True,exist_ok=True)
            args.review_packet_output.write_text(json.dumps(packet,ensure_ascii=False,indent=2),encoding='utf-8')
        if args.content_markdown_output:
            if content is None:raise ValueError('no content to render')
            args.content_markdown_output.parent.mkdir(parents=True,exist_ok=True)
            args.content_markdown_output.write_text(render_content(content),encoding='utf-8')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        if args.markdown_output:
            from s5_quality import render_markdown
            args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
            args.markdown_output.write_text(render_markdown(report), encoding='utf-8')
        print(f"S5 offline report: {report['executed_cases']}/{report['planned_cases']} executed; complete={report['report_complete']}; quality remains separately scored")
        print(f'Report: {args.output}')
        return 0 if report['report_complete'] else 1
    except (ValueError, OSError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        # No raw prompts, filenames, tokens or endpoint credentials in diagnostics.
        print(f'S5 input/report contract rejected: {type(exc).__name__}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
