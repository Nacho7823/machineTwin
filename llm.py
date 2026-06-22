from uuid import uuid4

from log import get_logger, log_trace_event
from config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, ToolMessage

logger = get_logger(__name__)
MAX_REASONING_STEPS = 5
REASONING_LIMIT_MESSAGE = "No pude completar el análisis porque se alcanzó el límite de pasos de razonamiento."


def _message_to_dict(message) -> dict:
    data = {
        "type": getattr(message, "type", type(message).__name__),
        "content": getattr(message, "content", ""),
    }
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        data["tool_calls"] = tool_calls
    tool_call_id = getattr(message, "tool_call_id", None)
    if tool_call_id:
        data["tool_call_id"] = tool_call_id
    return data


def _messages_to_dicts(messages: list) -> list[dict]:
    return [_message_to_dict(message) for message in messages]


class LLMAgent:
    def __init__(self, tools: dict):
        self._agent = None
        self._tools = tools
        api_key = LLM_API_KEY if LLM_API_KEY else "a"
        self._agent = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=api_key,
            openai_api_base=LLM_BASE_URL,
            temperature=0.3,
        ).bind_tools(list(self._tools.values()))

    @property
    def ready(self) -> bool:
        return self._agent is not None

    def invoke(self, messages: list):
        trace_id = str(uuid4())
        step = 0
        log_trace_event({
            "trace_id": trace_id,
            "event": "llm_request",
            "step": step,
            "messages": _messages_to_dicts(messages),
        })
        response = self._agent.invoke(messages)
        log_trace_event({
            "trace_id": trace_id,
            "event": "llm_response",
            "step": step,
            "response": _message_to_dict(response),
        })

        while response.tool_calls:
            if step >= MAX_REASONING_STEPS:
                logger.warning("Se alcanzo el limite de pasos de razonamiento del agente.")
                limit_response = AIMessage(content=REASONING_LIMIT_MESSAGE)
                log_trace_event({
                    "trace_id": trace_id,
                    "event": "reasoning_limit_reached",
                    "step": step,
                    "max_steps": MAX_REASONING_STEPS,
                    "response": _message_to_dict(limit_response),
                })
                return limit_response

            messages.append(response)
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                logger.info(f"El agente decidio llamar a la herramienta '{tool_name}' con argumentos: {tool_args}")
                tool = self._tools.get(tool_name)
                if tool:
                    tool_output = tool.invoke(tool_args)
                else:
                    tool_output = f"Error: Herramienta '{tool_name}' no encontrada."
                    logger.warning(f"Intento de usar herramienta no existente '{tool_name}'")
                log_trace_event({
                    "trace_id": trace_id,
                    "event": "tool_call",
                    "step": step,
                    "tool": tool_name,
                    "input": tool_args,
                    "output": str(tool_output),
                })
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_id))
            step += 1
            log_trace_event({
                "trace_id": trace_id,
                "event": "llm_request",
                "step": step,
                "messages": _messages_to_dicts(messages),
            })
            response = self._agent.invoke(messages)
            log_trace_event({
                "trace_id": trace_id,
                "event": "llm_response",
                "step": step,
                "response": _message_to_dict(response),
            })

        return response
