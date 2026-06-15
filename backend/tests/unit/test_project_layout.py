from pathlib import Path


def test_required_project_files_exist() -> None:
    root = Path(__file__).parents[3]
    required = [
        root / ".env.example",
        root / "Makefile",
        root / "backend" / "pyproject.toml",
        root / "frontend" / "package.json",
    ]
    assert all(path.exists() for path in required)
