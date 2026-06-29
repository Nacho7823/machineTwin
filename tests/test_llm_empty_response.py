from langchain_core.messages import AIMessage, HumanMessage

from llm import EMPTY_RESPONSE_FALLBACK_MESSAGE, EMPTY_RESPONSE_RETRY_MESSAGE, LLMAgent


class FakeChatModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def invoke(self, messages):
        self.requests.append(list(messages))
        return self.responses.pop(0)


class FakeTool:
    def __init__(self, output):
        self.output = output

    def invoke(self, args):
        return self.output


def make_agent(responses, tool_output="resultado de herramienta"):
    agent = LLMAgent.__new__(LLMAgent)
    agent._agent = FakeChatModel(responses)
    agent._tools = {"detectar_fuera_de_limites": FakeTool(tool_output)}
    return agent


def test_llm_agent_retries_when_final_response_is_empty():
    agent = make_agent([
        AIMessage(
            content="",
            tool_calls=[{"name": "detectar_fuera_de_limites", "args": {}, "id": "call-1"}],
        ),
        AIMessage(content=""),
        AIMessage(content="No veo valores actuales fuera de rango critico."),
    ])

    response = agent.invoke([HumanMessage(content="Hay algun problema operativo?")])

    assert response.content == "No veo valores actuales fuera de rango critico."
    assert any(message.content == EMPTY_RESPONSE_RETRY_MESSAGE for message in agent._agent.requests[-1])


def test_llm_agent_returns_fallback_if_retry_is_empty():
    agent = make_agent([
        AIMessage(
            content="",
            tool_calls=[{"name": "detectar_fuera_de_limites", "args": {}, "id": "call-1"}],
        ),
        AIMessage(content=""),
        AIMessage(content=""),
    ], tool_output="Todas las variables estan normales.")

    response = agent.invoke([HumanMessage(content="Hay algun problema operativo?")])

    assert EMPTY_RESPONSE_FALLBACK_MESSAGE in response.content
    assert "Todas las variables estan normales." in response.content
