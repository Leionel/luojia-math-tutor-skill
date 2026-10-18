"""Read and hash local R6.4 evidence using its original artifact validators."""
import argparse
import json
from pathlib import Path
import subprocess
from r5_quality import ROOT, verify_artifacts as verify_legacy
from r64_quality import load_material, verify_artifacts
from s5_quality import digest, load_json


def audit():
    load_material()  # Validates the unchanged R5/R64 freezes, not current runtime quality.
    snapshot = load_json(ROOT/'evaluation/r64/acceptance-2026-10-17.json')
    final_path = ROOT/'results/r64/final-v3.json'
    legacy_path = ROOT/'results/r64/r5-full-v1.json'
    final, legacy = load_json(final_path), load_json(legacy_path)
    legacy_count = verify_legacy(legacy_path)
    rows = [*final['records']['exploration'], *final['records']['private']]
    verify_artifacts(rows, final_path)
    logs = [{**row, 'exists': (ROOT/row['path']).exists(),
             'sha256_matches': (ROOT/row['path']).exists() and digest(ROOT/row['path']) == row['sha256']}
            for row in snapshot['validation']['logs']]
    browser = []
    for task in final['levels']['E2']['automation']['tasks']:
        for row in task['artifact_refs']:
            browser.append(dict(task=task['task_id'], **row,
                                matches=(ROOT/row['path']).exists() and digest(ROOT/row['path']) == row['sha256']))
    failures = []
    for name in ('results/r64/r5-original-recheck.json', 'results/r64/capture-first.json',
                 'results/r64/npm-test.log', 'results/r61/real-model-attempt1.json',
                 'results/r61/real-model-attempt2.json'):
        p = ROOT/name
        row = dict(path=name, available=p.exists(), sha256=digest(p) if p.exists() else None)
        if p.exists() and p.suffix == '.json':
            data = load_json(p)
            row['observed'] = {k: data[k] for k in ('completed_runs', 'matched_ablation_cases', 'failures') if k in data}
        failures.append(row)
    source_drift = [name for name, sha in snapshot['source_sha256'].items()
                    if not (ROOT/name).exists() or digest(ROOT/name) != sha]
    browser_drift = [name for name, sha in snapshot['browser_source_sha256'].items()
                     if not (ROOT/name).exists() or digest(ROOT/name) != sha]
    git = lambda *args: subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()
    return dict(version='r7-local-evidence-audit-v1', head=git('rev-parse', 'HEAD'),
                branch=git('branch', '--show-current'), status=git('status', '--short'),
                upstream_ahead_commits=git('log', '--oneline', '@{upstream}..HEAD').splitlines(),
                frozen_material_verified=True, verified_legacy_artifacts=legacy_count,
                verified_exploration_private_artifacts=len(rows), snapshot_levels_equal=snapshot['levels'] == final['levels'],
                levels=final['levels'], legacy_intervention_matches=legacy['matched_ablation_cases'],
                logs=logs, browser_artifacts=browser, preserved_failures=failures,
                current_source_drift=source_drift, current_browser_source_drift=browser_drift,
                source_hashes={name: digest(ROOT/name) for name in (
                    'evaluation/r64/acceptance-2026-10-17.json', 'results/r64/final-v3.json',
                    'results/r64/r5-full-v1.json', 'scripts/r64_r5_capture.py')},
                provider_requests_this_audit=0, current_model_quality=None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to(ROOT/'results') or target.exists():
        parser.error('use a new output inside results/')
    target.parent.mkdir(parents=True, exist_ok=True)
    report = audit()
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('verified_legacy_artifacts', 'verified_exploration_private_artifacts',
                                           'snapshot_levels_equal', 'current_source_drift', 'current_browser_source_drift')}))
