from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage


class ToolCallingFakeModel(GenericFakeChatModel):
    """Scripted chat model for no-LLM tests.

    GenericFakeChatModel does not implement bind_tools (verified in Phase 4), which
    create_agent requires; binding is a no-op because the replies are scripted.
    """

    def bind_tools(self, tools, **kwargs):
        return self


def tool_call(name: str, args: dict, call_id: str) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])
