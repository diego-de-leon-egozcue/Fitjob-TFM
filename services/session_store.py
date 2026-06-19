"""
session_store.py — Almacenamiento en memoria de sesiones de usuario.
Sin base de datos. Los datos se pierden al reiniciar el servidor.
"""

import threading
from typing import Any


class SessionStore:
    """Dict thread-safe de sesiones indexado por session_id UUID."""

    def __init__(self):
        self._data: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create(self, session_id: str) -> None:
        with self._lock:
            self._data[session_id] = {"history": []}

    def get(self, session_id: str) -> dict:
        with self._lock:
            return self._data.get(session_id, {})

    def set(self, session_id: str, key: str, value: Any) -> None:
        with self._lock:
            if session_id not in self._data:
                self._data[session_id] = {"history": []}
            self._data[session_id][key] = value

    def exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._data
