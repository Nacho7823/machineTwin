from pathlib import Path
import json
from hashlib import sha256
from datetime import datetime, timezone

import config
from . import agent_test, benchmarks
from .utils import load_folder, parse_trace


def _average(scores):
    values = [score for score in scores if score is not None]
    return sum(values) / len(values) if values else None


def _measure_all(trace, expected_output, model):
    return {
        "faithfulness": benchmarks.benchmark_fairthfulness(trace, model=model),
        "answer_relevance": benchmarks.benchmark_answer_relevance(trace, model=model),
        "context_precision": benchmarks.benchmark_context_precision(trace, expected_output, model=model),
        "context_recall": benchmarks.benchmark_context_recall(trace, expected_output, model=model),
    }


def _tools_ok(trace, expected_tools):
    if not expected_tools:
        return True
    parsed = parse_trace(trace)
    used = set(parsed["tools_used"])
    return all(tool in used for tool in expected_tools)


def _prompt_hash() -> str | None:
    try:
        content = config.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return None
    return sha256(content.encode("utf-8")).hexdigest()[:12]


def test():
    base_dir = Path(__file__).parent.parent
    work_dir = Path(__file__).parent / "test_folder"
    
    files_dir = Path(__file__).parent / "files"
    test_folders = sorted([p for p in files_dir.iterdir() if p.is_dir()])

    print(f"Se encontraron {len(test_folders)} casos de prueba para ejecutar.\n")

    results = {
        "faithfulness": [],
        "answer_relevance": [],
        "context_precision": [],
        "context_recall": [],
    }
    case_reports = []

    for folder in test_folders:
        folder_str = str(folder)
        folder_name = folder.name
        print("=" * 60)
        print(f"Ejecutando caso de prueba: {folder_name}")
        print("=" * 60)

        agent = agent_test.TestMachineTwin(base_dir, work_dir)
        configs, user_queries = load_folder(folder_str)

        agent.rag_archives(configs["rag_archives"])
        agent.sim_archives(configs["sim_archives"])
        agent.load()

        conversation_id = f"test_{folder_name}"
        if isinstance(user_queries, str):
            user_queries = [user_queries]

        chat = ""
        trace = []
        for user_query in user_queries:
            chat, turn_trace = agent.input(user_query, conversation_id=conversation_id)
            trace.extend(turn_trace)

        print(f"Consulta del Usuario: {user_queries[-1]}")
        print(f"Respuesta del Agente: {chat}")
        print("-" * 40)

        expected_output = configs.get("expected_output", "")
        metric_scores = _measure_all(trace, expected_output, benchmarks.JUDGE_LLM_MODEL)
        second_scores = None
        if benchmarks.SECOND_JUDGE_LLM_MODEL:
            second_scores = _measure_all(trace, expected_output, benchmarks.SECOND_JUDGE_LLM_MODEL)

        faithfulness_score = metric_scores["faithfulness"]
        answer_relevance_score = metric_scores["answer_relevance"]
        context_precision_score = metric_scores["context_precision"]
        context_recall_score = metric_scores["context_recall"]
        metric_average = _average(metric_scores.values())
        tools_passed = _tools_ok(trace, configs.get("expected_tools", []))
        non_empty_answer = bool(str(chat).strip())
        deterministic_checks = {
            "answer_non_empty": non_empty_answer,
            "expected_tools_used": tools_passed,
        }
        deterministic_passed = all(deterministic_checks.values())
        approved = deterministic_passed if metric_average is None else deterministic_passed and metric_average >= configs.get("minimum_score", 0.7)

        print(f"Métricas de Evaluación:")
        print(f"  - Faithfulness: {faithfulness_score}")
        print(f"  - Answer Relevance: {answer_relevance_score}")
        print(f"  - Context Precision: {context_precision_score}")
        print(f"  - Context Recall: {context_recall_score}")
        print("\n")
        print(f"  - Promedio del caso: {metric_average}")
        print(f"  - Tools esperadas OK: {tools_passed}")
        print(f"  - Respuesta no vacia: {non_empty_answer}")
        print(f"  - Aprobado: {approved}")
        print("\n")

        if faithfulness_score is not None:
            results["faithfulness"].append(faithfulness_score)
        if answer_relevance_score is not None:
            results["answer_relevance"].append(answer_relevance_score)
        if context_precision_score is not None:
            results["context_precision"].append(context_precision_score)
        if context_recall_score is not None:
            results["context_recall"].append(context_recall_score)

        case_reports.append({
            "case": folder_name,
            "queries": user_queries,
            "answer": chat,
            "metrics": metric_scores,
            "second_judge_metrics": second_scores,
            "metric_average": metric_average,
            "expected_tools": configs.get("expected_tools", []),
            "deterministic_checks": deterministic_checks,
            "approved": approved,
        })

    print("=" * 60)
    print("RESUMEN CONSOLIDADO DE PROMEDIOS DE BENCHMARKS")
    print("=" * 60)
    for metric, scores in results.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        metric_name = metric.replace("_", " ").title()
        print(f"  - Promedio {metric_name}: {avg:.4f} (basado en {len(scores)} pruebas)")
    approved_count = sum(1 for case in case_reports if case["approved"])
    approval_rate = approved_count / len(case_reports) if case_reports else 0.0
    print(f"  - Porcentaje de aprobacion: {approval_rate:.2%} ({approved_count}/{len(case_reports)})")
    print("=" * 60 + "\n")

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent_model": config.LLM_MODEL,
        "judge_model": benchmarks.JUDGE_LLM_MODEL,
        "second_judge_model": benchmarks.SECOND_JUDGE_LLM_MODEL or None,
        "System Prompt version": config.SYSTEM_PROMPT_VERSION,
        "prompt_hash": _prompt_hash(),
        "averages": {
            metric: (sum(scores) / len(scores) if scores else None)
            for metric, scores in results.items()
        },
        "approval_rate": approval_rate,
        "cases": case_reports,
    }
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"benchmark_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Reporte guardado en: {report_path}")


if __name__ == "__main__":
    test()
