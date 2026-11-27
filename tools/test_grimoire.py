#!/usr/bin/python3 -I
"""Self-check of grim + inscribe against a throwaway vault. Run: python3 tools/test_grimoire.py"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent


def run(tool, *args, stdin=None, ok=True):
    r = subprocess.run([sys.executable, "-I", str(TOOLS / f"{tool}.py"), *args], input=stdin or "",
                       capture_output=True, text=True, env={**os.environ, "GRIMOIRE_VAULT": vault})
    assert (r.returncode == 0) == ok, f"{tool} {args}: rc={r.returncode}\n{r.stdout}{r.stderr}"
    return r.stdout + r.stderr


with tempfile.TemporaryDirectory() as vault:
    for s in ("engine", "snippets", "inbox"):
        os.mkdir(f"{vault}/{s}")
        Path(f"{vault}/{s}/_about.md").write_text(f"{s} shelf\n")

    run("inscribe", "new", "engine/ownership", "-s", "who simulates physics", "-t", "physics,Net",
        stdin="# Ownership\n\n## Rules\n- one\n\n## Other\ntext [[Spring.luau]]\n")
    run("inscribe", "new", "snippets/Spring.luau", "-s", "a spring", stdin="return {}\n")
    run("inscribe", "new", "magic/x", "-s", "nope", stdin="x", ok=False)         # unknown shelf needs --new-shelf
    run("inscribe", "new", "magic/x", "-s", "a spell", "--new-shelf", "spells", stdin="x")
    assert Path(f"{vault}/magic/_about.md").read_text() == "spells\n"
    run("inscribe", "new", "magic/y", "-s", "s", "--new-shelf", "again", stdin="x", ok=False)
    run("inscribe", "new", "engine/ownership", "-s", "dup", stdin="x", ok=False)  # no overwrite
    run("inscribe", "new", "engine/Bad_Name", "-s", "x", stdin="x", ok=False)

    run("inscribe", "add", "ownership", "-s", "rules", stdin="- two\n")
    text = Path(f"{vault}/engine/ownership.md").read_text()
    assert "- one\n- two\n\n## Other" in text, text                              # list stays a list
    run("inscribe", "replace", "ownership", "text", "prose")
    run("inscribe", "replace", "ownership", "zzz", "y", ok=False)
    run("inscribe", "meta", "Spring", "-s", "a damped spring")
    assert Path(f"{vault}/snippets/Spring.luau").read_text().count("summary:") == 1

    out = run("grim", "find", "simulates")
    assert out.startswith("engine/ownership — who simulates physics"), out
    out = run("grim", "show", "ownership", "-s", "other")
    assert "prose" in out and "- one" not in out and "Spring.luau — a damped spring" in out, out
    assert "engine       1" in run("grim"), run("grim")
    assert "net" in run("grim", "show", "ownership")                             # tags lowercased

    run("inscribe", "jot", "streaming pauses teleports")
    assert "1 jots" in run("inscribe", "check")
    Path(f"{vault}/engine/broken.md").write_text("---\nsummary: s\n---\n# B\n[[nowhere]]\n")
    assert "broken link [[nowhere]]" in run("inscribe", "check", ok=False)

print("ok")
