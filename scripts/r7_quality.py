"""Prepare reviewed-input E1 packets or replay exact Teacher inputs after authorization.

Reuses R5/R64 capture and S5 budget/JSON contracts. Replay is a final-Teacher
component experiment, not a live native routing/retrieval/guard experiment.
"""
import argparse
import asyncio
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from r5_quality import ROOT, load_cases, sha, verify_artifacts as verify_r5
from r64_quality import verify_artifacts as verify_r64
from s5_budget import BudgetLedger, BudgetRejected, OfflineBudgetPolicy, amount
from s5_quality import digest, load_json

CASES = ('E06', 'E08', 'E10', 'N01', 'N02', 'N03', 'N04', 'G03', 'Q03')
LEDGER_ROOT = ROOT/'results/r7/live-budgets'
CONFOUNDS = ['final_teacher_input_replay_only', 'upstream_review_and_routing_are_offline_fixtures',
             'D2_differs_in_prompt_and_evidence_not_single_factor', 'no_live_output_guard_or_persistence',
             'public_development_agent_prepared_not_unseen']


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def prepare(legacy_path, private_path=None):
    verify_r5(legacy_path)
    data = load_json(legacy_path)
    material = load_cases(ROOT/'evaluation/r5/cases-v1.json')
    dimensions = load_json(ROOT/'evaluation/r64/rubric-v1.json')['dimensions']
    records = []
    for row in data['records']:
        if row['case_id'] not in CASES:
            continue
        if row['status'] != 'completed':
            raise ValueError('selected development arm did not complete')
        artifact = load_json(legacy_path.parent/row['artifact_ref'])
        calls = [c for c in artifact['model_calls'] if c['kind'] == 'generation_fixture']
        if len(calls) != 1:
            raise ValueError('requires exactly one captured final Teacher input')
        case = next(c for c in material['cases'] if c['id'] == row['case_id'])
        records.append(dict(case_id=row['case_id'], arm=row['arm'], messages=calls[0]['input_messages'],
                            input_sha256=row['input_sha256'], rubric=case['rubric'], rubric_sha256=row['rubric_sha256']))
    if len(records) != len(CASES)*3:
        raise ValueError('all selected D0/D1/D2 arms required; missing remains missing')
    sources = dict(data['capture_source_sha256'])
    if private_path:
        private = load_json(private_path)
        rows = private['records']['private']
        verify_r64(rows, private_path)
        if len(rows) != 18 or any(r['status'] != 'completed' for r in rows):
            raise ValueError('all nine private pairs required')
        sources.update(private['provenance']['source_sha256'])
        for row in rows:
            artifact = load_json(private_path.parent/row['artifact_ref'])
            if len(artifact['model_calls']) != 1:
                raise ValueError('requires one private Teacher input')
            records.append(dict(case_id=row['case_id'], arm=row['arm'], messages=artifact['model_calls'][0]['messages'],
                                input_sha256=row['input_sha256'], history_sha256=row['history_sha256'],
                                normalized_prompt_sha256=row['normalized_prompt_sha256'],
                                rubric=load_json(ROOT/'evaluation/r64/rubric-v1.json'),
                                rubric_sha256=digest(ROOT/'evaluation/r64/rubric-v1.json')))
    sources['scripts/r7_quality.py'] = digest(Path(__file__))
    for row in records:
        row.update(messages_sha256=sha(row['messages']), status='not_run', response_text=None,
                   usage=None, actual_cost=None, quality=None,
                   review={'reviewer_id': None, 'reviewed_at': None, 'failure_codes': [],
                           'ratings': {d: {'rating': None, 'status': 'not_reviewed', 'reason': 'pending',
                                           'quote': None, 'basis': None} for d in dimensions}})
    return dict(version='r7-teacher-replay-v1', scope=CONFOUNDS, source_sha256=sources,
                source_report_sha256=digest(legacy_path), records=records,
                planned=len(records), completed=0, failed=0, not_run=len(records),
                quality=None, usage=None, actual_cost=None, provider_requests=0,
                model=None, model_version=None, author_review='pending', independent_review='pending')


@dataclass(frozen=True)
class ReviewedReplayPolicy(OfflineBudgetPolicy):
    price_contract_kind: str = 'reviewed_provider_upper_bound'

    def validate(self):
        if self.price_contract_kind != 'reviewed_provider_upper_bound':
            raise BudgetRejected('reviewed_price_bound_required')
        # Reuse S5 endpoint, numeric, request and output-bound validation.
        OfflineBudgetPolicy.validate(replace(self, price_contract_kind='synthetic_fixture'))


def admission(packet, approval):
    if approval.get('packet_sha256') != sha(packet):
        raise BudgetRejected('reviewed_packet_mismatch')
    for field in ('authorization_ref', 'outbound_data_authorization_ref', 'author_review_ref',
                  'independent_math_review_ref', 'model_version', 'price_source',
                  'all_billable_items_upper_bound_review_ref', 'input_token_measurement_ref'):
        if not isinstance(approval.get(field), str) or not approval[field].strip():
            raise BudgetRejected('missing_'+field)
    if approval.get('all_billable_items_bounded') is not True:
        raise BudgetRejected('unbounded_billable_items')
    for name, expected in packet['source_sha256'].items():
        if not (ROOT/name).is_file() or digest(ROOT/name) != expected:
            raise BudgetRejected('source_drift_recapture_required')
    for row in packet['records']:
        if sha(row['messages']) != row['messages_sha256'] or row['status'] != 'not_run':
            raise BudgetRejected('changed_or_previously_run_input')
    upper = approval.get('input_tokens_upper_by_messages_sha256', {})
    ceiling = approval.get('max_input_tokens')
    if type(ceiling) is not int or not 1 <= ceiling <= 100000:
        raise BudgetRejected('input_token_ceiling_required')
    if any(type(upper.get(r['messages_sha256'])) is not int or not 0 < upper[r['messages_sha256']] <= ceiling
           for r in packet['records']):
        raise BudgetRejected('reviewed_input_token_bounds_required')
    policy = ReviewedReplayPolicy(endpoint=approval['endpoint'], model=approval['model'],
        max_requests=approval['max_requests'], max_cost=approval['max_cost'], currency=approval['currency'],
        per_request_upper_cost=approval['per_request_upper_cost'], max_output_tokens=approval['max_output_tokens'])
    policy.validate()
    if policy.max_requests != packet['planned'] or amount(policy.max_cost) < amount(policy.per_request_upper_cost)*packet['planned']:
        raise BudgetRejected('budget_must_cover_fixed_denominator')
    if not 1 <= approval.get('timeout_seconds', 0) <= 45:
        raise BudgetRejected('timeout_bound_required')
    return policy


async def replay(packet, approval, output, key, transport=None):
    import httpx
    policy = admission(packet, approval)
    ledger = BudgetLedger(LEDGER_ROOT/(sha(approval)+'.sqlite'), policy)
    # A new output is mandatory. Even a crash leaves reservations charged; no refund/retry.
    packet.update(model=policy.model, model_version=approval['model_version'],
                  authorization_sha256=sha(approval), execution='authorized_final_teacher_replay')
    write(output, packet)
    async with httpx.AsyncClient(transport=transport or httpx.AsyncHTTPTransport(retries=0),
                                timeout=approval['timeout_seconds'], follow_redirects=False, trust_env=False) as client:
        for row in packet['records']:
            payload = dict(model=policy.model, messages=row['messages'], stream=False, temperature=0,
                           max_tokens=policy.max_output_tokens)
            request_id = ledger.reserve(sha(payload))
            row.update(status='reserved_before_send', request_sha256=sha(payload), reservation_id=request_id)
            packet['provider_requests'] += 1
            write(output, packet)
            started = time.monotonic()
            try:
                # Total deadline includes body consumption. No SDK retries, tools, search or redirects.
                response = await asyncio.wait_for(client.post(policy.endpoint, json=payload,
                    headers={'Authorization': 'Bearer '+key}), timeout=approval['timeout_seconds'])
                ledger.finish(request_id, 'response_received')
                row['http_status'] = response.status_code
                response.raise_for_status()
                row['response_body_sha256'] = hashlib.sha256(response.content).hexdigest()
                body = response.json()
                row['usage'] = body.get('usage')  # provider reported, unknown remains null
                row['returned_model'] = body.get('model')
                row['finish_reason'] = body['choices'][0].get('finish_reason')
                row['response_text'] = body['choices'][0]['message'].get('content')
                row['response_sha256'] = sha(row['response_text'])
                if row['finish_reason'] != 'stop' or not isinstance(row['response_text'], str) or not row['response_text'].strip():
                    raise ValueError('incomplete_or_unsupported_completion')
                row['status'] = 'completed'
            except (Exception, asyncio.CancelledError) as error:
                ledger.finish(request_id, 'failed')
                row.update(status='failed', failure_type=type(error).__name__)
            finally:
                row['latency_ms'] = round((time.monotonic()-started)*1000, 3)
                packet.update(completed=sum(r['status']=='completed' for r in packet['records']),
                              failed=sum(r['status']=='failed' for r in packet['records']),
                              not_run=sum(r['status']=='not_run' for r in packet['records']),
                              reserved_cost_upper_bound=str(amount(policy.per_request_upper_cost)*packet['provider_requests']))
                write(output, packet)
            if row['status'] != 'completed':
                break  # failures and unexecuted rows stay in the planned denominator
    return packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', type=Path, help='current R64-routed R5 report')
    mode.add_argument('--live', type=Path, help='exact prepared packet; never enabled by environment keys')
    parser.add_argument('--private-report', type=Path)
    parser.add_argument('--approval', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if not target.is_relative_to(ROOT/'results') or target.exists() or target.with_suffix('.budget.sqlite').exists():
        parser.error('new output inside results/ required')
    target.parent.mkdir(parents=True, exist_ok=True)
    if args.prepare:
        packet = prepare(args.prepare.resolve(), args.private_report.resolve() if args.private_report else None)
        write(target, packet)
    else:
        if not args.approval:
            parser.error('explicit run/input/review/price approval file required')
        packet, approval = load_json(args.live), load_json(args.approval)
        admission(packet, approval)  # before importing or constructing any network transport
        key = os.environ.get('R7_REPLAY_API_KEY')
        if not key:
            parser.error('explicit temporary R7_REPLAY_API_KEY required; dotenv is never loaded')
        packet = asyncio.run(replay(packet, approval, target, key))
    print(json.dumps({k: packet[k] for k in ('planned', 'completed', 'failed', 'not_run', 'quality', 'provider_requests')}))
    return 0 if not packet['failed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
