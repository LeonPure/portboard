from __future__ import annotations

import hashlib
import os
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).parents[2]
INSTALLER = ROOT / "install.sh"


def _fake_release(tmp_path: Path, *, version: str = "9.8.7") -> tuple[Path, Path]:
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    target = "darwin-arm64"
    binary_name = f"portboard-{target}"
    binary = release_dir / binary_name
    binary.write_text(f"#!/bin/sh\nprintf 'portboard {version}\\n'\n", encoding="utf-8")
    binary.chmod(0o755)

    archive = release_dir / f"{binary_name}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(binary, arcname=binary_name)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (release_dir / "SHA256SUMS").write_text(
        f"{checksum}  {archive.name}\n",
        encoding="utf-8",
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        """#!/bin/sh
output=""
url=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --output) output="$2"; shift 2 ;;
    --proto) shift 2 ;;
    --*) shift ;;
    *) url="$1"; shift ;;
  esac
done
if [ -z "$output" ]; then
  printf '{"tag_name":"v%s"}\n' "$FAKE_VERSION"
else
  cp "$FAKE_RELEASE_DIR/${url##*/}" "$output"
fi
""",
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    return release_dir, fake_bin


def _installer_env(tmp_path: Path, release_dir: Path, fake_bin: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "FAKE_RELEASE_DIR": str(release_dir),
            "FAKE_VERSION": "9.8.7",
            "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
            "PORTBOARD_ARCH": "arm64",
            "PORTBOARD_INSTALL_DIR": str(tmp_path / "install"),
            "PORTBOARD_OS": "Darwin",
            "PORTBOARD_RELEASE_BASE_URL": "https://example.invalid/releases/download",
            "PORTBOARD_RELEASES_API": "https://example.invalid/releases",
        }
    )
    env.pop("PORTBOARD_VERSION", None)
    return env


def test_installs_latest_release_with_verified_checksum(tmp_path: Path) -> None:
    release_dir, fake_bin = _fake_release(tmp_path)
    env = _installer_env(tmp_path, release_dir, fake_bin)

    result = subprocess.run(
        ["sh", str(INSTALLER)],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    installed = tmp_path / "install" / "portboard"
    assert installed.stat().st_mode & 0o111
    assert subprocess.check_output([installed, "--version"], text=True).strip() == "portboard 9.8.7"
    assert f"Installed portboard 9.8.7 to {installed}" in result.stdout


def test_accepts_exact_prerelease_version_without_v_prefix(tmp_path: Path) -> None:
    release_dir, fake_bin = _fake_release(tmp_path, version="0.1.0a2")
    env = _installer_env(tmp_path, release_dir, fake_bin)
    env["PORTBOARD_VERSION"] = "0.1.0a2"

    subprocess.run(["sh", str(INSTALLER)], check=True, env=env)

    installed = tmp_path / "install" / "portboard"
    assert subprocess.check_output([installed, "--version"], text=True).strip() == "portboard 0.1.0a2"


def test_rejects_checksum_mismatch(tmp_path: Path) -> None:
    release_dir, fake_bin = _fake_release(tmp_path)
    (release_dir / "SHA256SUMS").write_text(
        f"{'0' * 64}  portboard-darwin-arm64.tar.gz\n",
        encoding="utf-8",
    )
    env = _installer_env(tmp_path, release_dir, fake_bin)

    result = subprocess.run(
        ["sh", str(INSTALLER)],
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.returncode != 0
    assert "checksum verification failed" in result.stderr
    assert not (tmp_path / "install" / "portboard").exists()


def test_rejects_unsupported_platform_before_downloading(tmp_path: Path) -> None:
    release_dir, fake_bin = _fake_release(tmp_path)
    env = _installer_env(tmp_path, release_dir, fake_bin)
    env["PORTBOARD_OS"] = "Windows"
    env["PORTBOARD_VERSION"] = "9.8.7"

    result = subprocess.run(
        ["sh", str(INSTALLER)],
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.returncode != 0
    assert "unsupported operating system: Windows" in result.stderr


def test_help_documents_version_and_install_directory() -> None:
    result = subprocess.run(
        ["sh", str(INSTALLER), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--version VERSION" in result.stdout
    assert "--install-dir DIRECTORY" in result.stdout
