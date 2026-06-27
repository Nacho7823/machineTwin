from . import agent_test, benchmarks
from .utils import load_folder


def test():
    agent = agent_test.TestMachineTwin()

    configs, user_query = load_folder("tests/files/fail_on_temperature")
    # configs, user_query = load_folder("tests/files/ask_inexistent_machine")
    agent.rag_archives(configs["rag_archives"])
    agent.sim_archives(configs["sim_archives"])

    agent.load()

    conversation_id = "test_fail_on_temperature"
    chat, trace = agent.input(user_query, conversation_id=conversation_id)

    print(f"User query: {user_query}")
    print(f"Chat: {chat}")
    print(f"Trace: {trace}")

    expected_output = configs.get("expected_output", "")

    fairthfulness_score = benchmarks.benchmark_fairthfulness(trace)
    answer_relevance_score = benchmarks.benchmark_answer_relevance(trace)
    context_precision_score = benchmarks.benchmark_context_precision(trace, expected_output)
    context_recall_score = benchmarks.benchmark_context_recall(trace, expected_output)

    print(f"Faithfulness: {fairthfulness_score}")
    print(f"Answer Relevance: {answer_relevance_score}")
    print(f"Context Precision: {context_precision_score}")
    print(f"Context Recall: {context_recall_score}")


if __name__ == "__main__":
    test()
