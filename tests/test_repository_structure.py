from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase_one_directories_exist():
    expected = [
        "airflow",
        "spark",
        "kafka",
        "producer",
        "consumer",
        "data/bronze",
        "data/silver",
        "data/gold",
        "dbt",
        "ml",
        "fastapi",
        "streamlit",
        "monitoring",
        "docs",
    ]

    missing = [path for path in expected if not (ROOT / path).is_dir()]

    assert missing == []


def test_phase_one_docs_exist():
    expected = [
        "README.md",
        "docs/architecture.md",
        "docs/roadmap.md",
        "docker-compose.yml",
        ".env.example",
    ]

    missing = [path for path in expected if not (ROOT / path).is_file()]

    assert missing == []
