"""
claude_cli.py — Llama al binario local de Claude Code via subprocess.
Mismo enfoque que PACO: sin API key, usa el claude.exe de la extensión VSCode.
"""

import os
import re
import subprocess
from pathlib import Path


def find_claude_bin() -> str:
    custom = os.getenv("CLAUDE_BIN", "").strip()
    if custom and Path(custom).exists():
        return custom
    candidates = sorted(
        Path.home().glob(".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude.exe"),
        reverse=True,
    )
    if candidates:
        return str(candidates[0])
    raise RuntimeError(
        "No se encontró el binario de Claude. "
        "Asegúrate de tener instalada la extensión Claude Code en VSCode, "
        "o añade CLAUDE_BIN=/ruta/al/claude.exe en el archivo .env"
    )


def call_claude(prompt: str, timeout: int = 180) -> str:
    """Ejecuta claude -p <prompt> y devuelve el texto de respuesta."""
    claude_bin = find_claude_bin()
    project_dir = Path(__file__).parent.parent

    result = subprocess.run(
        [claude_bin, "-p", prompt],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(project_dir),
        timeout=timeout,
    )

    # Limpiar códigos de color ANSI del output
    out = re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", result.stdout).strip()

    if not out and result.stderr:
        out = f"[Error del CLI: {result.stderr.strip()[:300]}]"

    return out or "[Sin respuesta]"
