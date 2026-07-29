import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


@pytest.mark.parametrize("path", sorted((ROOT / "domain").glob("*.py")))
def test_domain_has_no_outward_dependencies(path: Path) -> None:
    forbidden = {
        "aiogram",
        "aiogram_i18n",
        "application",
        "commands",
        "database",
        "filters",
        "infrastructure",
        "keyboards",
        "middlewares",
        "presentation",
        "routers",
        "sqlalchemy",
    }
    assert imported_roots(path).isdisjoint(forbidden)


@pytest.mark.parametrize(
    "path",
    sorted((ROOT / "application" / "services").glob("*.py")),
)
def test_application_services_depend_inward(path: Path) -> None:
    forbidden = {
        "aiogram",
        "aiogram_i18n",
        "commands",
        "database",
        "filters",
        "infrastructure",
        "keyboards",
        "middlewares",
        "presentation",
        "routers",
        "sqlalchemy",
    }
    assert imported_roots(path).isdisjoint(forbidden)
