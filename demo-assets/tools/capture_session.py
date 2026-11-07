#!/usr/bin/env python3
"""Capture a real Simple ATM Simulation session in a Windows pseudo-terminal.

This script is Windows-only because it uses ConPTY through pywinpty. It records
the exact ANSI output of the compiled program, timestamps every chunk, and
marks the moments used for screenshots.

Build first:
    g++ -std=c++17 -O2 -o atm.exe "Atm Simulation.cpp"

Install the asset-tool dependencies:
    py -m pip install -r demo-assets/tools/requirements.txt

Then run:
    py demo-assets/tools/capture_session.py

The resulting session.json is consumed by render_assets.py.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXE = REPO_ROOT / ("atm.exe" if os.name == "nt" else "atm")
DEFAULT_OUT = REPO_ROOT / "demo-assets" / "tools" / "session.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--cols", type=int, default=90)
    parser.add_argument("--rows", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.exe.is_file():
        print(f"error: executable not found: {args.exe}", file=sys.stderr)
        print('build it with: g++ -std=c++17 -O2 -o atm.exe "Atm Simulation.cpp"', file=sys.stderr)
        return 1

    try:
        from winpty import PtyProcess
    except ImportError:
        print("error: pywinpty is required: py -m pip install -r demo-assets/tools/requirements.txt", file=sys.stderr)
        return 1

    process = PtyProcess.spawn([str(args.exe)], cwd=str(REPO_ROOT), dimensions=(args.rows, args.cols))
    chunks: list[tuple[float, str]] = []
    snapshots: dict[str, float] = {}
    lock = threading.Lock()
    stop = False
    search_pos = 0
    start = time.monotonic()

    def reader() -> None:
        while not stop:
            try:
                data = process.read(4096)
            except Exception:
                break
            if not data:
                break
            with lock:
                chunks.append((time.monotonic(), data))

    threading.Thread(target=reader, daemon=True).start()

    def current_text() -> str:
        with lock:
            return "".join(chunk for _, chunk in chunks)

    def wait_for(marker: str, timeout: float = 20.0) -> None:
        nonlocal search_pos
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            text = current_text()
            index = text.find(marker, search_pos)
            if index != -1:
                search_pos = index + len(marker)
                return
            time.sleep(0.03)
        raise TimeoutError(f"timed out waiting for marker: {marker!r}")

    def send(text: str) -> None:
        process.write(text)

    def snapshot(name: str) -> None:
        snapshots[name] = round(time.monotonic() - start, 3)

    try:
        wait_for("ready")
        time.sleep(0.2)
        snapshot("splash")

        wait_for("choice (1-3):")
        time.sleep(0.7)
        snapshot("main_menu")
        send("1\r")

        wait_for("Account ID:")
        time.sleep(0.7)
        snapshot("sign_in")
        send("1001\r")

        wait_for("PIN (1/3):")
        time.sleep(0.4)
        send("1234\r")

        wait_for("ACCESS GRANTED")
        time.sleep(0.3)
        snapshot("welcome")

        wait_for("choice (1-5):")
        time.sleep(0.7)
        snapshot("dashboard")
        send("2\r")

        wait_for("Amount to deposit:")
        time.sleep(0.4)
        send("250\r")

        wait_for("[ press enter ]")
        time.sleep(0.6)
        snapshot("deposit_result")
        send("\r")

        wait_for("choice (1-5):")
        time.sleep(0.4)
        send("4\r")

        wait_for("[ press enter ]")
        time.sleep(0.8)
        snapshot("history")
        send("\r")

        wait_for("choice (1-5):")
        time.sleep(0.4)
        send("5\r")

        wait_for("choice (1-3):")
        time.sleep(0.5)
        snapshot("main_menu_end")
        send("3\r")

        wait_for("Goodbye.")
        time.sleep(0.2)
        snapshot("goodbye")

        process.wait()
    finally:
        time.sleep(0.3)
        stop = True
        try:
            process.close()
        except Exception:
            pass

    with lock:
        data = [(round(moment - start, 3), chunk) for moment, chunk in chunks]

    if not data:
        print("error: no output captured", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "cols": args.cols,
                "rows": args.rows,
                "chunks": data,
                "snapshots": snapshots,
            },
            handle,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print(f"captured {len(data)} chunks in {data[-1][0]:.2f}s", file=sys.stderr)
    print(f"snapshots: {snapshots}", file=sys.stderr)
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TimeoutError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
