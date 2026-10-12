"""Build the real wheel, install it into a throwaway venv and drive the installed script.

Nothing is mocked: this needs network access for pip to fetch the build backend.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import ellipt

ROOT = Path(__file__).resolve().parent.parent
FAMILY = "\U0001f468\u200d\U0001f469\u200d\U0001f467"


def _run(cmd: list[str], stdin: bytes = b"") -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.run(cmd, input=stdin, capture_output=True, env=env, timeout=600, check=False)


def test_wheel_installs_and_the_script_works(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "-q", "-w", str(dist), str(ROOT)]
    )
    assert built.returncode == 0, built.stderr.decode(errors="replace")
    wheels = list(dist.glob("ellipt-*.whl"))
    assert [w.name for w in wheels] == [f"ellipt-{ellipt.__version__}-py3-none-any.whl"]
    archive = zipfile.ZipFile(wheels[0])
    names = archive.namelist()
    assert "ellipt/py.typed" in names and "ellipt/_ucd_part1.py" in names
    assert any(n.endswith("licenses/LICENSE-UNICODE") for n in names)
    assert not [n for n in names if n.startswith(("data/", "tests/", "scripts/"))]
    entry = next(n for n in names if n.endswith("entry_points.txt"))
    assert "ellipt = ellipt._cli:main" in archive.read(entry).decode()

    env_dir = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
    bindir = env_dir / ("Scripts" if os.name == "nt" else "bin")
    python = bindir / ("python.exe" if os.name == "nt" else "python")
    script = bindir / ("ellipt.exe" if os.name == "nt" else "ellipt")
    installed = _run([str(python), "-m", "pip", "install", "-q", "--no-index", str(wheels[0])])
    assert installed.returncode == 0, installed.stderr.decode(errors="replace")
    assert script.is_file()

    done = _run([str(script), "8"], b"hello world\nok\r\n")
    assert (done.returncode, done.stdout) == (0, b"hello...\nok\r\n")
    done = _run([str(script), "4", "--marker", "\u2026"], f"ab{FAMILY}cd\n".encode())
    assert done.stdout == "ab\u2026\n".encode()  # the family is 2 columns: kept whole or not at all
    done = _run([str(script), "5", "--marker", "\u2026"], f"ab{FAMILY}cd\n".encode())
    assert done.stdout == f"ab{FAMILY}\u2026\n".encode()
    done = _run([str(script), "16", "--path"], b"/srv/www/site/public/index.html\n")
    assert done.stdout == b"/.../index.html\n"
    done = _run([str(script), "9", "-w", "middle", "-u", "bytes"], b"0123456789abcdef\n")
    assert done.stdout == b"012...def\n"
    failed = _run([str(script), "2"], b"hello\n")
    assert failed.returncode == 1 and b"does not fit" in failed.stderr and failed.stdout == b""
    version = _run([str(script), "--version"])
    assert version.stdout.strip() == f"ellipt {ellipt.__version__}".encode()
    helped = _run([str(script), "--help"])
    assert helped.returncode == 0 and b"examples:" in helped.stdout
    module = _run([str(python), "-m", "ellipt", "3"], b"abcdef\n")
    assert module.stdout == b"...\n"

    probe = "import ellipt; print(ellipt.UNICODE_VERSION, ellipt.__file__)"
    shown = _run([str(python), "-c", probe]).stdout.decode()
    assert shown.startswith(f"{ellipt.UNICODE_VERSION} ") and str(env_dir) in shown
