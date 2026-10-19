"""Build the real sdist and wheel, install the wheel into a throwaway venv and use it.

Nothing is mocked: the build needs network access for pip to fetch the build backend.
The installed package is driven from an empty folder with ``-I``, so the source tree
cannot leak into the import path.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

import pytest

import ellipt

ROOT = Path(__file__).resolve().parent.parent
FAMILY = "\U0001f468‍\U0001f469‍\U0001f467"
MODULES = [*sorted(p.name for p in (ROOT / "src" / "ellipt").glob("*.py")), "py.typed"]
CONSUMER = """
import pickle, sys
import ellipt
from ellipt import ELLIPSIS, Truncation, measure, shorten, shorten_path, truncate
assert ellipt.__file__.startswith(sys.argv[1]), ellipt.__file__
r = truncate("hello brave new world", 15, marker=ELLIPSIS, words=True)
assert (r.text, r.removed, r.truncated) == ("hello brave…", " new world", True)
assert isinstance(r, Truncation) and pickle.loads(pickle.dumps(r)) == r
assert shorten("你好世界", 5, unit="columns", marker=ELLIPSIS) == "你好…"
assert measure("\U0001f1ea\U0001f1f8", "bytes") == 8
assert shorten_path("/home/me/projects/app/src/main.py", 20) == "/.../app/src/main.py"
assert list(ellipt.iter_graphemes("éx")) == ["é", "x"]
print(ellipt.__version__, ellipt.UNICODE_VERSION)
"""


def _run(
    cmd: list[str], stdin: bytes = b"", cwd: Path | None = None
) -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    return subprocess.run(
        cmd, input=stdin, capture_output=True, env=env, cwd=cwd, timeout=280, check=False
    )


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    dist = tmp_path_factory.mktemp("dist")
    done = _run([sys.executable, "-m", "build", "--outdir", str(dist), str(ROOT)])
    assert done.returncode == 0, done.stderr.decode(errors="replace")[-3000:]
    version = ellipt.__version__
    assert sorted(p.name for p in dist.iterdir()) == [
        f"ellipt-{version}-py3-none-any.whl",
        f"ellipt-{version}.tar.gz",
    ]
    return dist / f"ellipt-{version}-py3-none-any.whl", dist / f"ellipt-{version}.tar.gz"


def test_the_wheel_holds_the_package_and_its_licences_only(built: tuple[Path, Path]) -> None:
    names = zipfile.ZipFile(built[0]).namelist()
    info = f"ellipt-{ellipt.__version__}.dist-info/"
    assert sorted(n for n in names if not n.startswith(info)) == [f"ellipt/{m}" for m in MODULES]
    assert sorted(n[len(info) :] for n in names if n.startswith(info)) == [
        "METADATA",
        "RECORD",
        "WHEEL",
        "entry_points.txt",
        "licenses/LICENSE",
        "licenses/LICENSE-UNICODE",
    ]
    archive = zipfile.ZipFile(built[0])
    assert "ellipt = ellipt._cli:main" in archive.read(info + "entry_points.txt").decode()
    meta = archive.read(info + "METADATA").decode()
    assert f"
Version: {ellipt.__version__}
" in meta
    runtime = [r for r in meta.splitlines() if r.startswith("Requires-Dist") and "extra" not in r]
    assert runtime == []
    assert "Classifier: Development Status :: 5 - Production/Stable" in meta


def test_the_sdist_holds_sources_tests_and_docs_but_no_fetched_data(
    built: tuple[Path, Path],
) -> None:
    with tarfile.open(built[1]) as archive:
        names = {n.split("/", 1)[1] for n in archive.getnames() if "/" in n}
    for wanted in ("LICENSE", "LICENSE-UNICODE", "README.md", "CHANGELOG.md", "GUIDE.md"):
        assert wanted in names, wanted
    assert {f"src/ellipt/{m}" for m in MODULES} <= names
    assert "data/ucd/MANIFEST.json" in names and "scripts/fetch_upstream.py" in names
    assert "tests/conftest.py" in names and "pyproject.toml" in names
    junk = [n for n in names if "__pycache__" in n or n.endswith((".pyc", ".txt"))]
    assert junk == []
    assert not [n for n in names if n.startswith(("CERT-", "IMPROVEMENTS", ".github", "dist"))]


def test_the_installed_wheel_works_from_an_empty_folder(
    built: tuple[Path, Path], tmp_path: Path
) -> None:
    env_dir = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
    bindir = env_dir / ("Scripts" if os.name == "nt" else "bin")
    python = bindir / ("python.exe" if os.name == "nt" else "python")
    script = bindir / ("ellipt.exe" if os.name == "nt" else "ellipt")
    installed = _run([str(python), "-m", "pip", "install", "-q", "--no-index", str(built[0])])
    assert installed.returncode == 0, installed.stderr.decode(errors="replace")
    empty = tmp_path / "empty"
    empty.mkdir()
    used = _run([str(python), "-I", "-c", CONSUMER, str(env_dir)], cwd=empty)
    assert used.returncode == 0, used.stderr.decode(errors="replace")
    assert used.stdout.decode().split() == [ellipt.__version__, ellipt.UNICODE_VERSION]

    def cli(args: list[str], data: bytes = b"") -> subprocess.CompletedProcess[bytes]:
        return _run([str(script), *args], data, cwd=empty)

    done = cli(["8"], b"hello world\nok\r\n")
    assert (done.returncode, done.stdout, done.stderr) == (0, b"hello...\nok\r\n", b"")
    done = cli(["4", "--marker", "…"], f"ab{FAMILY}cd\n".encode())
    assert done.stdout == "ab…\n".encode()  # the family is 2 columns: whole or not at all
    done = cli(["5", "-e"], f"ab{FAMILY}cd\n".encode())
    assert done.stdout == f"ab{FAMILY}…\n".encode()
    done = cli(["16", "--path"], b"/srv/www/site/public/index.html\n")
    assert done.stdout == b"/.../index.html\n"
    done = cli(["9", "-w", "middle", "-u", "bytes"], b"0123456789abcdef\n")
    assert done.stdout == b"012...def\n"
    source = tmp_path / "in.txt"
    source.write_bytes(b"\xef\xbb\xbfa\tbcdefghijk\n")
    done = cli(["12", "-e", str(source)])
    assert done.stdout == "a       bcd…\n".encode()
    failed = cli(["2"], b"hello\n")
    assert failed.returncode == 2 and b"does not fit" in failed.stderr and failed.stdout == b""
    failed = cli(["5"], b"ok\n\xff\n")
    assert failed.returncode == 1 and b"<stdin>: line 2 is not valid UTF-8" in failed.stderr
    assert failed.stdout == b"ok\n"
    failed = cli(["5", str(tmp_path / "missing.txt")])
    assert failed.returncode == 1 and b"missing.txt" in failed.stderr
    version = cli(["--version"])
    assert version.stdout.strip() == f"ellipt {ellipt.__version__}".encode()
    helped = cli(["--help"])
    assert helped.returncode == 0 and b"examples:" in helped.stdout
    module = _run([str(python), "-I", "-m", "ellipt", "3"], b"abcdef\n", cwd=empty)
    assert module.stdout == b"...\n"
