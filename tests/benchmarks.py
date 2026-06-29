import os
import signal
from contextlib import contextmanager
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

os.environ["OPENAI_API_KEY"] = LLM_API_KEY or "a"
os.environ["OPENAI_BASE_URL"] = LLM_BASE_URL
JUDGE_LLM_MODEL = LLM_MODEL
SECOND_JUDGE_LLM_MODEL = os.getenv("SECOND_JUDGE_LLM_MODEL", "")
JUDGE_MODE = os.getenv("JUDGE_MODE", "selected")
TEST_PROFILE = os.getenv("TEST_PROFILE", "").strip().lower()
JUDGE_METRIC_TIMEOUT_SECONDS = int(os.getenv("JUDGE_METRIC_TIMEOUT_SECONDS", "0"))
MOSTRAR_LOGS = False

from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
)

from tests.utils import parse_trace


class MetricTimeoutError(Exception):
    pass


@contextmanager
def _metric_timeout(metric_name: str):
    if JUDGE_METRIC_TIMEOUT_SECONDS <= 0:
        yield
        return

    def _handle_timeout(signum, frame):
        raise MetricTimeoutError(f"Timeout en {metric_name} despues de {JUDGE_METRIC_TIMEOUT_SECONDS}s")

    previous_handler = signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(JUDGE_METRIC_TIMEOUT_SECONDS)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def _measure_metric(metric, test_case, metric_name: str):
    try:
        with _metric_timeout(metric_name):
            metric.measure(test_case)
        return metric.score
    except Exception as e:
        print(f"  - {metric_name}: sin puntaje ({type(e).__name__}: {e})")
        return None


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
    return _measure_metric(metric, test_case, "faithfulness")


def benchmark_answer_relevance(trace, model=JUDGE_LLM_MODEL):
    # Answer Relevance	¿La respuesta responde la query?
    test_case = _build_test_case(trace)
    if test_case is None:
        return None
    metric = AnswerRelevancyMetric(threshold=0.7, model=model, include_reason=True, verbose_mode=MOSTRAR_LOGS)
    return _measure_metric(metric, test_case, "answer_relevance")


def benchmark_context_precision(trace, expected_output, model=JUDGE_LLM_MODEL):
    # Context Precision	¿Los chunks relevantes están rankeados primero?
    test_case = _build_test_case(trace, expected_output=expected_output)
    if test_case is None:
        return None
    metric = ContextualPrecisionMetric(threshold=0.7, model=model, include_reason=True, verbose_mode=MOSTRAR_LOGS)
    return _measure_metric(metric, test_case, "context_precision")
