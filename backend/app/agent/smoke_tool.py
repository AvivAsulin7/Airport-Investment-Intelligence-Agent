"""A non-aviation test tool used only by Phase 4 smoke tests.

It exercises Pydantic input validation and the content_and_artifact path without
touching any assignment scenario logic.
"""

from langchain.tools import tool
from pydantic import BaseModel, Field

_FIXTURE = {"alpha": 11, "beta": 22, "gamma": 33}


class LookupInput(BaseModel):
    key: str = Field(pattern=r"^[a-z]{1,10}$", description="Lowercase key, e.g. 'alpha'.")


@tool(args_schema=LookupInput, response_format="content_and_artifact")
def lookup_test_value(key: str) -> tuple[str, dict]:
    """Look up a fixed test value by key (smoke-test tool, not aviation data)."""
    if key not in _FIXTURE:
        raise KeyError(key)
    artifact = {"result_type": "smoke_test", "key": key, "value": _FIXTURE[key], "source_type": "test_fixture"}
    return f"value for {key} is {_FIXTURE[key]}", artifact
