"""Final-input replay budget/failure behavior, never fixture quality scores."""
import copy
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts'))
from r7_quality import admission, replay
from r5_quality import sha
from s5_budget import BudgetRejected
from s5_quality import load_json


def inputs():
    messages = [{'role': 'user', 'content': '公开合成数学输入'}]
    packet = dict(source_sha256={}, planned=2, completed=0, failed=0, not_run=2,
        records=[dict(case_id='test', arm=a, messages=copy.deepcopy(messages), messages_sha256=sha(messages),
                      status='not_run', quality=None, usage=None, actual_cost=None) for a in ('D0', 'D1')],
        quality=None, usage=None, actual_cost=None, provider_requests=0)
    approval = dict(packet_sha256=sha(packet), endpoint='https://fixture.invalid/v1/chat/completions',
        model='offline-model', max_requests=2, currency='USD', max_cost='0.02', per_request_upper_cost='0.01',
        max_output_tokens=100, max_input_tokens=500, input_tokens_upper_by_messages_sha256={sha(messages): 100},
        all_billable_items_bounded=True, timeout_seconds=1)
    for field in ('authorization_ref', 'outbound_data_authorization_ref', 'author_review_ref',
                  'independent_math_review_ref', 'model_version', 'price_source',
                  'all_billable_items_upper_bound_review_ref', 'input_token_measurement_ref'):
        approval[field] = 'synthetic-test-only'
    return packet, approval


def test_ambient_key_never_supplies_missing_authorization_or_review(monkeypatch):
    monkeypatch.setenv('R7_REPLAY_API_KEY', 'offline-test-key')
    packet, approval = inputs()
    del approval['independent_math_review_ref']
    with pytest.raises(BudgetRejected, match='missing_independent_math_review_ref'):
        admission(packet, approval)
    packet['records'][0]['messages'][0]['content'] = 'different outbound input'
    with pytest.raises(BudgetRejected, match='reviewed_packet_mismatch'):
        admission(packet, inputs()[1])


@pytest.mark.asyncio
async def test_truncation_consumes_budget_preserves_text_and_stops_remaining_arm(tmp_path, monkeypatch):
    import r7_quality
    monkeypatch.setattr(r7_quality, 'LEDGER_ROOT', tmp_path/'budgets')
    packet, approval = inputs()
    requests = []
    def model(request):
        requests.append(request)
        saved = load_json(tmp_path/'replay.json')
        assert saved['records'][0]['status'] == 'reserved_before_send'
        return httpx.Response(200, json={'model': 'offline-model', 'usage': {'total_tokens': 13},
            'choices': [{'finish_reason': 'length', 'message': {'content': 'unfinished response'}}]})
    data = await replay(packet, approval, tmp_path/'replay.json', 'fixture', httpx.MockTransport(model))
    assert len(requests) == 1 and data['reserved_cost_upper_bound'] == '0.01'
    assert (data['completed'], data['failed'], data['not_run']) == (0, 1, 1)
    assert data['records'][0]['response_text'] == 'unfinished response'
    assert data['records'][1]['status'] == 'not_run' and data['quality'] is None
    # Another output filename cannot reset the same approval's request/cost budget.
    await replay(inputs()[0], approval, tmp_path/'second.json', 'fixture', httpx.MockTransport(
        lambda request: httpx.Response(500)))
    with pytest.raises(BudgetRejected, match='request_budget_exhausted'):
        await replay(inputs()[0], approval, tmp_path/'third.json', 'fixture', httpx.MockTransport(model))
