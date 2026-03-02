"""Unit-style tests for core/evidence.py.

Usage:
    python3 scripts/test_evidence.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.evidence import extract_evidence


def test_basic_extraction() -> None:
    text = (
        "Built data pipelines using Python and Apache Airflow. "
        "Skills: Python, JavaScript, SQL, Docker. "
        "Containerized microservices with Docker and deployed via Kubernetes."
    )
    result = extract_evidence(text, ["python", "docker"])
    assert len(result["python"]) == 2, f"Expected 2 snippets for python, got {len(result['python'])}"
    assert len(result["docker"]) == 2, f"Expected 2 snippets for docker, got {len(result['docker'])}"
    print("  PASS: basic extraction")


def test_word_boundary() -> None:
    """'java' must not match 'javascript'."""
    text = "Proficient in JavaScript and TypeScript for frontend development."
    result = extract_evidence(text, ["java"])
    assert result["java"] == [], f"Expected no match for 'java', got {result['java']}"
    print("  PASS: word boundary (java != javascript)")


def test_special_chars() -> None:
    """Skills like c++ and c# should match."""
    text = "Developed real-time systems in C++ for 3 years. Also used C# for tooling."
    result = extract_evidence(text, ["c++", "c#"])
    assert len(result["c++"]) >= 1, f"Expected match for c++, got {result['c++']}"
    assert len(result["c#"]) >= 1, f"Expected match for c#, got {result['c#']}"
    print("  PASS: special chars (c++, c#)")


def test_multi_word_skill() -> None:
    text = "Applied machine learning models to predict customer churn."
    result = extract_evidence(text, ["machine learning"])
    assert len(result["machine learning"]) == 1
    print("  PASS: multi-word skill")


def test_max_two_snippets() -> None:
    text = (
        "Used Python for scripting. "
        "Built APIs with Python Flask. "
        "Deployed Python services to AWS."
    )
    result = extract_evidence(text, ["python"])
    assert len(result["python"]) <= 2, f"Expected max 2, got {len(result['python'])}"
    print("  PASS: max 2 snippets")


def test_empty_text() -> None:
    result = extract_evidence("", ["python"])
    assert result["python"] == []
    result2 = extract_evidence("   ", ["python"])
    assert result2["python"] == []
    print("  PASS: empty text")


def test_truncation() -> None:
    long_sentence = "Used Python " + "in a very complex scenario " * 20 + "at scale."
    result = extract_evidence(long_sentence, ["python"])
    assert len(result["python"]) == 1
    assert len(result["python"][0]) <= 210  # 200 + "..."
    assert result["python"][0].endswith("...")
    print("  PASS: truncation")


def test_case_insensitive() -> None:
    text = "Proficient in DOCKER containerization and Docker Compose."
    result = extract_evidence(text, ["docker"])
    assert len(result["docker"]) >= 1
    print("  PASS: case insensitive")


def main() -> None:
    print("=== Evidence Extraction Tests ===\n")
    test_basic_extraction()
    test_word_boundary()
    test_special_chars()
    test_multi_word_skill()
    test_max_two_snippets()
    test_empty_text()
    test_truncation()
    test_case_insensitive()
    print("\n=== All tests passed ===")


if __name__ == "__main__":
    main()
