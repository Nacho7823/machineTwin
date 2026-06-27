from pathlib import Path
from . import agent_test, benchmarks
from .utils import load_folder


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

    for folder in test_folders:
        folder_str = str(folder)
        folder_name = folder.name
        print("=" * 60)
        print(f"Ejecutando caso de prueba: {folder_name}")
        print("=" * 60)

        agent = agent_test.TestMachineTwin(base_dir, work_dir)
        configs, user_query = load_folder(folder_str)

        agent.rag_archives(configs["rag_archives"])
        agent.sim_archives(configs["sim_archives"])
        agent.load()

        conversation_id = f"test_{folder_name}"
        chat, trace = agent.input(user_query, conversation_id=conversation_id)

        print(f"Consulta del Usuario: {user_query}")
        print(f"Respuesta del Agente: {chat}")
        print("-" * 40)

        expected_output = configs.get("expected_output", "")

        faithfulness_score = benchmarks.benchmark_fairthfulness(trace)
        answer_relevance_score = benchmarks.benchmark_answer_relevance(trace)
        context_precision_score = benchmarks.benchmark_context_precision(trace, expected_output)
        context_recall_score = benchmarks.benchmark_context_recall(trace, expected_output)

        print(f"Métricas de Evaluación:")
        print(f"  - Faithfulness: {faithfulness_score}")
        print(f"  - Answer Relevance: {answer_relevance_score}")
        print(f"  - Context Precision: {context_precision_score}")
        print(f"  - Context Recall: {context_recall_score}")
        print("\n")

        if faithfulness_score is not None:
            results["faithfulness"].append(faithfulness_score)
        if answer_relevance_score is not None:
            results["answer_relevance"].append(answer_relevance_score)
        if context_precision_score is not None:
            results["context_precision"].append(context_precision_score)
        if context_recall_score is not None:
            results["context_recall"].append(context_recall_score)

    print("=" * 60)
    print("RESUMEN CONSOLIDADO DE PROMEDIOS DE BENCHMARKS")
    print("=" * 60)
    for metric, scores in results.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        metric_name = metric.replace("_", " ").title()
        print(f"  - Promedio {metric_name}: {avg:.4f} (basado en {len(scores)} pruebas)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    test()
