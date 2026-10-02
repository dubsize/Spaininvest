import json
from types import SimpleNamespace

from arbscan.normalization.ai import AI_CONFIDENCE_CAP, AnthropicNormalizer


class FakeClient:
    def __init__(self, payload, stop_reason="end_turn"):
        self.payload = payload
        self.stop_reason = stop_reason
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(stop_reason=self.stop_reason, content=[SimpleNamespace(type="text", text=json.dumps(self.payload))])


def listing(title, description=""):
    return SimpleNamespace(id=1, title=title, description=description, brand_raw=None)


def test_skipped_when_rules_are_confident(normalizer):
    client = FakeClient({})
    ai = AnthropicNormalizer(client=client, model="claude-opus-5-5", min_rule_confidence=0.6)
    l = listing("Thermomix TM6")
    res = ai.maybe_improve(l, normalizer.normalize(l.title), normalizer)
    assert client.calls == [] and res.product_slug == "thermomix-tm6"


def test_ai_picks_catalogue_product_and_is_capped(normalizer):
    client = FakeClient({"product_slug": "thermomix-tm6", "attributes": [], "confidence": 0.99, "reason": "Robot de cocina Vorwerk 6ª generación"})
    ai = AnthropicNormalizer(client=client, model="claude-opus-5-5", min_rule_confidence=0.6)
    l = listing("Robot de cocina de Vorwerk, sexta generación")
    base = normalizer.normalize(l.title)
    res = ai.maybe_improve(l, base, normalizer)
    assert res.product_slug == "thermomix-tm6"
    assert res.confidence == AI_CONFIDENCE_CAP and res.method == "rules+ai"
    call = client.calls[0]
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert call["fallbacks"] == "default"


def test_unknown_slug_or_refusal_keeps_rule_result(normalizer):
    l = listing("Algo raro")
    base = normalizer.normalize(l.title)
    ai = AnthropicNormalizer(client=FakeClient({"product_slug": "not-in-catalog", "attributes": [], "confidence": 0.9, "reason": "x"}), model="m", min_rule_confidence=0.6)
    assert ai.maybe_improve(l, base, normalizer).product_slug is None
    refused = AnthropicNormalizer(client=FakeClient({}, stop_reason="refusal"), model="m", min_rule_confidence=0.6)
    assert refused.maybe_improve(l, base, normalizer) is base
