from pathlib import Path
import json
import os
from hashlib import sha256
from datetime import datetime, timezone

import config
from . import agent_test, benchmarks
from .utils import load_folder, parse_trace


ALL_METRICS = ["faithfulness", "answer_relevance", "context_precision"]
DEFAULT_TEST_PROFILE = "semantic_rag"

PROFILE_DESCRIPTIONS = {
    "functional": "19 casos con checks deterministas y sin LLM-as-judge.",
    "semantic_rag": "19 casos con judge semantico y RAG en casos representativos.",
    "exhaustive": "19 casos con las tres metricas en todos los casos.",
}

SEMANTIC_RAG_PROFILE_METRICS = {
    "current_status": ["faithfulness", "answer_relevance"],
    "documented_operation": ["faithfulness", "answer_relevance", "context_precision"],
    "high_vibration_advice": ["faithfulness", "answer_relevance", "context_precision"],
    "maintenance_recommendation": ["faithfulness", "answer_relevance", "context_precision"],
    "operational_problem_summary": ["answer_relevance"],
    "out_of_limits": ["faithfulness", "answer_relevance"],
    "rag_source_request": ["faithfulness", "answer_relevance", "context_precision"],
    "recent_events": ["faithfulness", "answer_relevance"],
    "stop_criteria": ["faithfulness", "answer_relevance", "context_precision"],
    "verify_failure_actions": ["faithfulness", "answer_relevance", "context_precision"],
}


def _average(scores):
    values = [score for score in scores if score is not None]
    return sum(values) / len(values) if values else None


def _measure_selected(trace, expected_output, model, metric_names):
    available = {
        "faithfulness": lambda: benchmarks.benchmark_faithfulness(trace, model=model),
        "answer_relevance": lambda: benchmarks.benchmark_answer_relevance(trace, model=model),
        "context_precision": lambda: benchmarks.benchmark_context_precision(trace, expected_output, model=model),
    }
    scores = {name: None for name in available}
    for name in metric_names:
        if name not in available:
            print(f"  - Metrica desconocida ignorada: {name}")
            continue
        scores[name] = available[name]()
    return scores


def _active_profile():
    return os.getenv("TEST_PROFILE", DEFAULT_TEST_PROFILE).strip().lower() or DEFAULT_TEST_PROFILE


def _case_judge_metrics(folder_name):
    profile = _active_profile()
    if profile == "functional":
        return []
    if profile == "semantic_rag":
        return SEMANTIC_RAG_PROFILE_METRICS.get(folder_name, [])
    if profile == "exhaustive":
        return ALL_METRICS
    valid = ", ".join(PROFILE_DESCRIPTIONS)
    raise ValueError(f"TEST_PROFILE invalido: {profile}. Valores validos: {valid}")


def _profile_label():
    return _active_profile()


def _tools_ok(trace, expected_tools):
    if not expected_tools:
        return True
    parsed = parse_trace(trace)
    used = set(parsed["tools_used"])
    return all(tool in used for tool in expected_tools)


def _agent_response_ok(answer: str) -> bool:
    error_markers = [
        "Error al consultar el LLM",
        "Rate limit exceeded",
        "Free model usage limit reached",
    ]
    return bool(str(answer).strip()) and not any(marker in str(answer) for marker in error_markers)


def _prompt_hash() -> str | None:
    try:
        content = config.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return None
    return sha256(content.encode("utf-8")).hexdigest()[:12]


def _build_report(status, results, case_reports, total_cases):
    approved_count = sum(1 for case in case_reports if case["approved"])
    approval_rate = approved_count / len(case_reports) if case_reports else 0.0
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "agent_model": config.LLM_MODEL,
        "judge_model": benchmarks.JUDGE_LLM_MODEL,
        "test_profile": _profile_label(),
        "second_judge_model": benchmarks.SECOND_JUDGE_LLM_MODEL or None,
        "System Prompt version": config.SYSTEM_PROMPT_VERSION,
        "prompt_hash": _prompt_hash(),
        "total_cases": total_cases,
        "completed_cases": len(case_reports),
        "averages": {
            metric: (sum(scores) / len(scores) if scores else None)
            for metric, scores in results.items()
        },
        "metric_counts": {
            metric: len(scores)
            for metric, scores in results.items()
        },
        "approval_rate": approval_rate,
        "cases": case_reports,
    }


def _write_report(report_path, status, results, case_reports, total_cases):
    report = _build_report(status, results, case_reports, total_cases)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def test():
    base_dir = Path(__file__).parent.parent
    work_dir = Path(__file__).parent / "test_folder"
    
    files_dir = Path(__file__).parent / "files"
    test_folders = sorted([p for p in files_dir.iterdir() if p.is_dir()])

    print(f"Perfil de test: {_profile_label()}")
    if _active_profile():
        print(f"Descripcion: {PROFILE_DESCRIPTIONS.get(_active_profile(), 'Perfil no reconocido')}")
    print(f"Se encontraron {len(test_folders)} casos de prueba para ejecutar.\n")
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / f"benchmark_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

    results = {
        "faithfulness": [],
        "answer_relevance": [],
        "context_precision": [],
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
        judge_metrics = _case_judge_metrics(folder_name)
        metric_scores = _measure_selected(trace, expected_output, benchmarks.JUDGE_LLM_MODEL, judge_metrics)
        second_scores = None
        if benchmarks.SECOND_JUDGE_LLM_MODEL and judge_metrics:
            second_scores = _measure_selected(trace, expected_output, benchmarks.SECOND_JUDGE_LLM_MODEL, judge_metrics)

        faithfulness_score = metric_scores["faithfulness"]
        answer_relevance_score = metric_scores["answer_relevance"]
        context_precision_score = metric_scores["context_precision"]
        metric_average = _average(metric_scores.values())
        tools_passed = _tools_ok(trace, configs.get("expected_tools", []))
        non_empty_answer = bool(str(chat).strip())
        agent_response_ok = _agent_response_ok(chat)
        deterministic_checks = {
            "answer_non_empty": non_empty_answer,
            "agent_response_ok": agent_response_ok,
            "expected_tools_used": tools_passed,
        }
        deterministic_passed = all(deterministic_checks.values())
        approved = deterministic_passed if metric_average is None else deterministic_passed and metric_average >= configs.get("minimum_score", 0.7)

        print(f"Métricas de Evaluación:")
        print(f"  - Faithfulness: {faithfulness_score}")
        print(f"  - Answer Relevance: {answer_relevance_score}")
        print(f"  - Context Precision: {context_precision_score}")
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

        case_reports.append({
            "case": folder_name,
            "queries": user_queries,
            "answer": chat,
            "metrics": metric_scores,
            "second_judge_metrics": second_scores,
            "metric_average": metric_average,
            "expected_tools": configs.get("expected_tools", []),
            "judge_metrics": judge_metrics,
            "deterministic_checks": deterministic_checks,
            "approved": approved,
        })
        _write_report(report_path, "partial", results, case_reports, len(test_folders))

    print("=" * 60)
    print("RESUMEN CONSOLIDADO DE PROMEDIOS DE BENCHMARKS")
    print("=" * 60)
    for metric, scores in results.items():
        metric_name = metric.replace("_", " ").title()
        if scores:
            avg = sum(scores) / len(scores)
            print(f"  - Promedio {metric_name}: {avg:.4f} (basado en {len(scores)} pruebas)")
        else:
            print(f"  - Promedio {metric_name}: sin datos (basado en 0 pruebas)")
    approved_count = sum(1 for case in case_reports if case["approved"])
    approval_rate = approved_count / len(case_reports) if case_reports else 0.0
    print(f"  - Porcentaje de aprobacion: {approval_rate:.2%} ({approved_count}/{len(case_reports)})")
    print("=" * 60 + "\n")

    _write_report(report_path, "complete", results, case_reports, len(test_folders))
    print(f"Reporte guardado en: {report_path}")


if __name__ == "__main__":
    test()
