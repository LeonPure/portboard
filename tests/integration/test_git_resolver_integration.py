from __future__ import annotations

import subprocess

from portboard.adapters.project.git_resolver import GitProjectResolver
from portboard.domain.models import ProjectInfo


def test_git_resolver_finds_the_repository_containing_a_nested_directory(
    tmp_path,
) -> None:
    repository = tmp_path / "sample-project"
    nested = repository / "src" / "package"
    nested.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "--quiet", str(repository)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert GitProjectResolver().resolve(str(nested)) == ProjectInfo(
        name="sample-project",
        root=str(repository),
    )
