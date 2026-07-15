from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase_one_directories_exist():
    expected = [
        "airflow",
        "spark",
        "kafka",
        "producer",
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


def test_phase_10_ml_files_exist():
    expected = [
        "ml/train_forecast.py",
        "ml/train_churn.py",
        "ml/train_recommendations.py",
        "ml/Dockerfile",
        "ml/requirements.txt",
        "docs/phase-10-ml.md",
    ]

    missing = [path for path in expected if not (ROOT / path).is_file()]

    assert missing == []


def test_phase_11_production_files_exist():
    expected = [
        ".github/workflows/ci.yml",
        "docs/schema-evolution.md",
        "docs/phase-11-production.md",
        ".env.dev",
        ".env.staging",
        ".env.prod",
    ]

    missing = [path for path in expected if not (ROOT / path).is_file()]

    assert missing == []
