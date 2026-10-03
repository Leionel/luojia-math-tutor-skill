"""Optional operator-declared plain token pricing; no live price guesses."""
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re


def price(settings, model=None):
    try:
        base, resolved = settings.resolve_request(model)
        config = json.loads(settings.llm_prices_json)
        value = config.get(model or settings.llm_model)
        if not isinstance(value, dict) or value.get("resolved_model") != resolved or value.get("base_url_sha256") != hashlib.sha256(base.rstrip('/').encode()).hexdigest(): return None
        if value.get("currency") not in {"USD", "CNY"} or value.get("billing_mode") != "plain_input_output": return None
        if not isinstance(value.get("version"),str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-v\d{1,3})?",value["version"]): return None
        result = {"currency":value["currency"], "version":value["version"]}
        for key in ("input_per_million", "output_per_million"):
            number = value.get(key)
            if type(number) not in {int,float,str}: return None
            rate = Decimal(str(number))
            if not rate.is_finite() or not 0 <= rate <= 1000000: return None
            result[key] = str(rate)
        return result
    except (ValueError, TypeError, AttributeError, InvalidOperation):
        return None


def cost(usage, pricing):
    if not usage or not pricing: return None
    amount = (Decimal(usage["prompt_tokens"])*Decimal(pricing["input_per_million"]) +
              Decimal(usage["completion_tokens"])*Decimal(pricing["output_per_million"]))/1000000
    return {"amount":str(amount.quantize(Decimal('0.00000001'))), "currency":pricing["currency"],
            "price_version":pricing["version"], "scope":"reported_plain_tokens_estimate"}
