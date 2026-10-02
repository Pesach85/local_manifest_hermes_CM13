#!/usr/bin/env python3
"""Append one SKILL_SELF_RECEIPT line. No network, no prompt, no model."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SKILL_ID = "root-cause-5why"
EVIDENCE_CLASS = "SKILL_SELF_RECEIPT"
EVENT = "skill_invocation"
MODES = ("live_cursor", "test_fixture")


def skill_markdown(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parents[1] / "SKILL.md"


def parse_version(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("**Version:**"):
            return line.split("**Version:**", 1)[1].strip()
    raise ValueError("SKILL.md has no **Version:** line")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head(start: Path) -> str:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for parent in (current, *current.parents):
        if (parent / ".git").exists():
            out = subprocess.run(
                ["git", "-C", str(parent), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
            return out.stdout.strip()
    raise ValueError("git HEAD not found")


def build_receipt(
    skill_md: Path,
    *,
    repository_id: str,
    execution_mode: str,
    session_id: str | None = None,
) -> dict:
    if execution_mode not in MODES:
        raise ValueError(f"invalid execution_mode: {execution_mode}")
    text = skill_md.read_text(encoding="utf-8")
    receipt = {
        "event": EVENT,
        "evidence_class": EVIDENCE_CLASS,
        "skill_id": SKILL_ID,
        "skill_version": parse_version(text),
        "skill_sha256": sha256_file(skill_md),
        "repository_id": repository_id,
        "git_head": git_head(skill_md),
        "receipt_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execution_mode": execution_mode,
    }
    if session_id:
        receipt["session_id"] = session_id
    return receipt


def append_receipt(receipt: dict, ledger: Path) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(receipt, ensure_ascii=False, separators=(",", ":"))
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit one skill self-receipt")
    parser.add_argument("--execution-mode", required=True, choices=MODES)
    parser.add_argument("--repository-id", required=True)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--skill-md", dest="skill_md")
    parser.add_argument("--session-id", default="")
    args = parser.parse_args(argv)
    skill_md = skill_markdown(args.skill_md)
    if args.ledger is None:
        root = skill_md
        while not (root / ".git").exists():
            if root.parent == root:
                print("ledger directory not found", file=sys.stderr)
                return 1
            root = root.parent
        ledger = root / "config" / "intelligence" / "ledger" / "skill_invocations.jsonl"
    else:
        ledger = args.ledger
    if not ledger.parent.is_dir():
        print(f"missing ledger directory: {ledger.parent}", file=sys.stderr)
        return 1
    receipt = build_receipt(
        skill_md,
        repository_id=args.repository_id,
        execution_mode=args.execution_mode,
        session_id=args.session_id or None,
    )
    append_receipt(receipt, ledger)
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
