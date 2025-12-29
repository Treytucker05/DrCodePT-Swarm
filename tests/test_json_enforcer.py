from pydantic import BaseModel
try:
    from pydantic import ConfigDict
except Exception:
    ConfigDict = None

from agent.llm.json_enforcer import enforce_json_response


class SamplePayload(BaseModel):
    foo: int

    if ConfigDict:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


def _schema_for(model):
    if hasattr(model, "model_json_schema"):
        return model.model_json_schema()
    return model.schema()


def test_json_repair_retry():
    calls = []

    def retry(prompt: str):
        calls.append(prompt)
        return '{"foo": 1}'

    data, error = enforce_json_response(
        "not json",
        model_cls=SamplePayload,
        schema=_schema_for(SamplePayload),
        retry_call=retry,
        max_retries=2,
    )

    assert error is None
    assert data == {"foo": 1}
    assert len(calls) == 1
