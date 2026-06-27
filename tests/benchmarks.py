import os
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

os.environ["OPENAI_API_KEY"] = LLM_API_KEY or "a"
os.environ["OPENAI_BASE_URL"] = LLM_BASE_URL

from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric

from tests.utils import parse_trace


def _build_test_case(trace):
    parsed = parse_trace(trace)
    if not parsed["input"] or not parsed["actual_output"] or not parsed["retrieval_context"]:
        return None
    return LLMTestCase(
        input=parsed["input"],
        actual_output=parsed["actual_output"],
        retrieval_context=parsed["retrieval_context"],
    )


def benchmark_fairthfulness(trace):
    # Faithfulness	¿Las afirmaciones están soportadas por el contexto?
    test_case = _build_test_case(trace)
    if test_case is None:
        return None
    metric = FaithfulnessMetric(threshold=0.7, model=LLM_MODEL, include_reason=True)
    metric.measure(test_case)
    return metric.score


def benchmark_answer_relevance(trace):
    # Answer Relevance	¿La respuesta responde la query?
    test_case = _build_test_case(trace)
    if test_case is None:
        return None
    metric = AnswerRelevancyMetric(threshold=0.7, model=LLM_MODEL, include_reason=True)
    metric.measure(test_case)
    return metric.score


def benchmark_context_precision(trace):
    # Context Precision	¿Los chunks relevantes están rankeados primero?
    pass


def benchmark_context_recall(trace):
    # Context Recall	¿Se recuperaron todos los chunks necesarios?
    pass
