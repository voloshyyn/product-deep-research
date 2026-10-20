"""Ask the installed Codex app-server to discover the Skill; no model turn is started."""
from __future__ import annotations

import argparse
import json
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from research_core import utf8_console


def discover(codex: str, cwd: Path, expected_path: Path | None = None, timeout: float = 20) -> list[dict]:
    process = subprocess.Popen([codex, "app-server", "--stdio"], cwd=cwd, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    messages: queue.Queue = queue.Queue()

    def reader() -> None:
        try:
            for line in process.stdout:
                try:
                    messages.put(json.loads(line))
                except ValueError:
                    pass
        finally:
            messages.put(None)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()

    def send(message: dict) -> None:
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    def response(identifier: int) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                message = messages.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise ValueError("Codex app-server discovery timed out") from exc
            if message is None:
                raise ValueError("Codex app-server exited before returning discovery results")
            if message.get("id") == identifier:
                if "error" in message:
                    raise ValueError(f"Codex protocol error: {message['error']}")
                return message["result"]
        raise ValueError("Codex discovery timed out")

    try:
        send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "product-deep-research-discovery", "version": "1.0"}}})
        response(1)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "skills/list", "params": {"cwds": [str(cwd.resolve())], "forceReload": True}})
        result = response(2)
        matches = [skill for group in result.get("data", []) for skill in group.get("skills", [])
                   if skill.get("name") == "product-deep-research" and skill.get("enabled", True)]
        if expected_path:
            expected = expected_path.resolve()
            matches = [s for s in matches if Path(s["path"]).resolve() in {expected, expected / "SKILL.md"}]
        if not matches:
            raise ValueError("Skill was not discovered/enabled at the expected path. Check installation, /skills and Codex configuration.")
        return [{k: s.get(k) for k in ("name", "path", "scope", "enabled")} for s in matches]
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        if process.stdin:
            process.stdin.close()
        thread.join(timeout=1)
        if process.stdout:
            process.stdout.close()


def main() -> int:
    utf8_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--expected-path", type=Path)
    parser.add_argument("--codex", default=shutil.which("codex"))
    parser.add_argument("--repeat", type=int, choices=[1, 2], default=1, help="2 checks discovery across fresh app-server processes")
    args = parser.parse_args()
    try:
        if not args.codex:
            raise ValueError("codex executable is not available on PATH")
        results = [discover(args.codex, args.cwd, args.expected_path) for _ in range(args.repeat)]
        print(json.dumps({"discovered": True, "fresh_process_checks": len(results), "results": results}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print(f"Discovery error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
