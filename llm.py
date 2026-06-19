from log import get_logger
from config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage

logger = get_logger(__name__)


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
        response = self._agent.invoke(messages)

        while response.tool_calls:
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
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_id))
            response = self._agent.invoke(messages)

        return response
