from uuid import uuid4
from hashlib import sha256
from time import perf_counter

from log import get_logger, log_trace_event, trace_context
from config import (
    LLM_API_KEY,
    LLM_MODEL,
    LLM_BASE_URL,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT,
    LLM_MAX_RETRIES,
    LLM_ENABLE_THINKING,
    LLM_REASONING_BUDGET,
    SYSTEM_PROMPT_VERSION,
)

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

logger = get_logger(__name__)
MAX_REASONING_STEPS = 5
REASONING_LIMIT_MESSAGE = "No pude completar el análisis porque se alcanzó el límite de pasos de razonamiento."
EMPTY_RESPONSE_RETRY_MESSAGE = (
    "La respuesta final anterior estuvo vacia. Responde ahora al usuario en espanol, "
    "de forma concisa y usando los resultados de herramientas que ya estan en el contexto. "
    "No vuelvas a llamar herramientas salvo que sea estrictamente necesario."
)
EMPTY_RESPONSE_FALLBACK_MESSAGE = (
    "No pude generar una respuesta final sintetizada porque el modelo devolvio una respuesta vacia. "
    "Las consultas internas si se ejecutaron; estos son los resultados disponibles:"
)


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


def _prompt_hash(messages: list) -> str | None:
    for message in messages:
        if getattr(message, "type", None) == "system":
            content = str(getattr(message, "content", ""))
            return sha256(content.encode("utf-8")).hexdigest()[:12]
    return None


def _content_is_empty(content) -> bool:
    if content is None:
        return True
    if isinstance(content, str):
        return not content.strip()
    if isinstance(content, list):
        return all(_content_is_empty(item.get("text", item) if isinstance(item, dict) else item) for item in content)
    return False


def _is_empty_final_response(response) -> bool:
    return not getattr(response, "tool_calls", None) and _content_is_empty(getattr(response, "content", None))


def _last_tool_outputs(messages: list, limit: int = 2, max_chars: int = 2800) -> str:
    outputs = []
    for message in reversed(messages):
        if getattr(message, "type", None) == "tool":
            content = str(getattr(message, "content", "")).strip()
            if content:
                outputs.append(content)
            if len(outputs) >= limit:
                break
    outputs.reverse()
    text = "\n\n".join(outputs)
    if len(text) > max_chars:
        return text[:max_chars].rstrip() + "\n..."
    return text


def _empty_response_fallback(messages: list) -> AIMessage:
    tool_outputs = _last_tool_outputs(messages)
    if not tool_outputs:
        return AIMessage(content="No pude generar una respuesta final porque el modelo devolvio una respuesta vacia.")
    return AIMessage(content=f"{EMPTY_RESPONSE_FALLBACK_MESSAGE}\n\n{tool_outputs}")


class LLMAgent:
    def __init__(self, tools: dict):
        self._agent = None
        self._tools = tools
        if not LLM_API_KEY or not LLM_MODEL or not LLM_BASE_URL:
            return
        extra_body = {}
        if LLM_ENABLE_THINKING:
            extra_body["chat_template_kwargs"] = {"enable_thinking": True}
            extra_body["reasoning_budget"] = LLM_REASONING_BUDGET
        self._agent = ChatOpenAI(
            model=LLM_MODEL,
            openai_api_key=LLM_API_KEY,
            openai_api_base=LLM_BASE_URL,
            temperature=LLM_TEMPERATURE,
            top_p=LLM_TOP_P,
            max_tokens=LLM_MAX_TOKENS,
            timeout=LLM_TIMEOUT,
            max_retries=LLM_MAX_RETRIES,
            extra_body=extra_body or None,
        ).bind_tools(list(self._tools.values()))

    @property
    def ready(self) -> bool:
        return self._agent is not None

    def _invoke_model(self, messages: list, trace_id: str, conversation_id: str | None, step: int):
        started = perf_counter()
        response = self._agent.invoke(messages)
        latency_ms = round((perf_counter() - started) * 1000, 2)
        finish_status = "tool_calls" if getattr(response, "tool_calls", None) else "ok"
        if _is_empty_final_response(response):
            finish_status = "empty"
        log_trace_event({
            "trace_id": trace_id,
            "conversation_id": conversation_id,
            "event": "llm_response",
            "step": step,
            "llm_model": LLM_MODEL,
            "System Prompt version": SYSTEM_PROMPT_VERSION,
            "prompt_hash": _prompt_hash(messages),
            "latency_ms": latency_ms,
            "finish_status": finish_status,
            "response": _message_to_dict(response),
        })
        return response

    def invoke(self, messages: list, conversation_id: str | None = None):
        trace_id = str(uuid4())
        step = 0
        log_trace_event({
            "trace_id": trace_id,
            "conversation_id": conversation_id,
            "event": "llm_request",
            "step": step,
            "llm_model": LLM_MODEL,
            "System Prompt version": SYSTEM_PROMPT_VERSION,
            "prompt_hash": _prompt_hash(messages),
            "messages": _messages_to_dicts(messages),
        })
        response = self._invoke_model(messages, trace_id, conversation_id, step)

        empty_response_retried = False
        while True:
            if not response.tool_calls:
                if _is_empty_final_response(response):
                    if not empty_response_retried:
                        empty_response_retried = True
                        logger.warning("El modelo devolvio una respuesta final vacia. Reintentando sintesis final.")
                        messages.append(HumanMessage(content=EMPTY_RESPONSE_RETRY_MESSAGE))
                        step += 1
                        log_trace_event({
                            "trace_id": trace_id,
                            "conversation_id": conversation_id,
                            "event": "empty_response_retry",
                            "step": step,
                            "llm_model": LLM_MODEL,
                            "System Prompt version": SYSTEM_PROMPT_VERSION,
                            "prompt_hash": _prompt_hash(messages),
                            "finish_status": "empty_retry",
                        })
                        log_trace_event({
                            "trace_id": trace_id,
                            "conversation_id": conversation_id,
                            "event": "llm_request",
                            "step": step,
                            "llm_model": LLM_MODEL,
                            "System Prompt version": SYSTEM_PROMPT_VERSION,
                            "prompt_hash": _prompt_hash(messages),
                            "messages": _messages_to_dicts(messages),
                        })
                        response = self._invoke_model(messages, trace_id, conversation_id, step)
                        continue

                    fallback_response = _empty_response_fallback(messages)
                    log_trace_event({
                        "trace_id": trace_id,
                        "conversation_id": conversation_id,
                        "event": "empty_response_fallback",
                        "step": step,
                        "llm_model": LLM_MODEL,
                        "System Prompt version": SYSTEM_PROMPT_VERSION,
                        "prompt_hash": _prompt_hash(messages),
                        "finish_status": "fallback",
                        "response": _message_to_dict(fallback_response),
                    })
                    return fallback_response
                return response

            if step >= MAX_REASONING_STEPS:
                logger.warning("Se alcanzo el limite de pasos de razonamiento del agente.")
                limit_response = AIMessage(content=REASONING_LIMIT_MESSAGE)
                log_trace_event({
                    "trace_id": trace_id,
                    "conversation_id": conversation_id,
                    "event": "reasoning_limit_reached",
                    "step": step,
                    "max_steps": MAX_REASONING_STEPS,
                    "llm_model": LLM_MODEL,
                    "System Prompt version": SYSTEM_PROMPT_VERSION,
                    "prompt_hash": _prompt_hash(messages),
                    "finish_status": "reasoning_limit",
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
                tool_started = perf_counter()
                tool_status = "ok"
                try:
                    with trace_context(trace_id=trace_id, conversation_id=conversation_id, step=step, tool=tool_name):
                        if tool:
                            tool_output = tool.invoke(tool_args)
                        else:
                            tool_output = f"Error: Herramienta '{tool_name}' no encontrada."
                            tool_status = "error"
                            logger.warning(f"Intento de usar herramienta no existente '{tool_name}'")
                except Exception as e:
                    tool_status = "error"
                    tool_output = f"Error ejecutando herramienta '{tool_name}': {type(e).__name__}: {e}"
                    logger.exception(f"Error al ejecutar herramienta '{tool_name}'")
                tool_latency_ms = round((perf_counter() - tool_started) * 1000, 2)
                log_trace_event({
                    "trace_id": trace_id,
                    "conversation_id": conversation_id,
                    "event": "tool_call",
                    "step": step,
                    "tool": tool_name,
                    "tool_status": tool_status,
                    "tool_latency_ms": tool_latency_ms,
                    "input": tool_args,
                    "output": str(tool_output),
                })
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_id))
            step += 1
            log_trace_event({
                "trace_id": trace_id,
                "conversation_id": conversation_id,
                "event": "llm_request",
                "step": step,
                "llm_model": LLM_MODEL,
                "System Prompt version": SYSTEM_PROMPT_VERSION,
                "prompt_hash": _prompt_hash(messages),
                "messages": _messages_to_dicts(messages),
            })
            response = self._invoke_model(messages, trace_id, conversation_id, step)

        return response
