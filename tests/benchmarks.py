import os
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

os.environ["OPENAI_API_KEY"] = LLM_API_KEY or "a"
os.environ["OPENAI_BASE_URL"] = LLM_BASE_URL
JUDGE_LLM_MODEL = LLM_MODEL
SECOND_JUDGE_LLM_MODEL = os.getenv("SECOND_JUDGE_LLM_MODEL", "")
MOSTRAR_LOGS = False

from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
)

from tests.utils import parse_trace


def _build_test_case(trace, expected_output=None):
    parsed = parse_trace(trace)
    if not parsed["input"] or not parsed["actual_output"] or not parsed["retrieval_context"]:
        return None
    return LLMTestCase(
        input=parsed["input"],
        actual_output=parsed["actual_output"],
        expected_output=expected_output,
        retrieval_context=parsed["retrieval_context"],
    )


def benchmark_fairthfulness(trace, model=JUDGE_LLM_MODEL):
    # Faithfulness	¿Las afirmaciones están soportadas por el contexto?
    test_case = _build_test_case(trace)
    if test_case is None:
        return None
    metric = FaithfulnessMetric(threshold=0.7, model=model, include_reason=True, verbose_mode=MOSTRAR_LOGS)
    metric.measure(test_case)
    return metric.score


def benchmark_answer_relevance(trace, model=JUDGE_LLM_MODEL):
    # Answer Relevance	¿La respuesta responde la query?
    test_case = _build_test_case(trace)
    if test_case is None:
        return None
    metric = AnswerRelevancyMetric(threshold=0.7, model=model, include_reason=True, verbose_mode=MOSTRAR_LOGS)
    metric.measure(test_case)
    return metric.score


def benchmark_context_precision(trace, expected_output, model=JUDGE_LLM_MODEL):
    # Context Precision	¿Los chunks relevantes están rankeados primero?
    test_case = _build_test_case(trace, expected_output=expected_output)
    if test_case is None:
        return None
    metric = ContextualPrecisionMetric(threshold=0.7, model=model, include_reason=True, verbose_mode=MOSTRAR_LOGS)
    metric.measure(test_case)
    return metric.score


def benchmark_context_recall(trace, expected_output, model=JUDGE_LLM_MODEL):
    # Context Recall	¿Se recuperaron todos los chunks necesarios?
    test_case = _build_test_case(trace, expected_output=expected_output)
    if test_case is None:
        return None
    metric = ContextualRecallMetric(threshold=0.7, model=model, include_reason=True, verbose_mode=MOSTRAR_LOGS)
    metric.measure(test_case)
    return metric.score
