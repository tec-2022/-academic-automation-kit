"""Fast prediction without requiring AI or telemetry."""
from __future__ import annotations
import re

RULES = [
    (r"\b(mysql|mariadb)\b.*\b(no|error|falla|conecta|inicia|abre)\b", "diagnose_mysql"),
    (r"\b(limpiar|temporales|basura)\b", "clean_temporaries"),
    (r"\b(desinstalar|eliminar|quitar)\b.*\b(programa|app|aplicaci[oó]n)?\b", "uninstall_program"),
    (r"\b(instalar|descargar)\b", "install_program"),
    (r"\b(ingenier[ií]a|carrera|universidad)\b", "prepare_career"),
]

def predict(text: str) -> tuple[str, float]:
    normalized = text.casefold().strip()
    for pattern, intent in RULES:
        if re.search(pattern, normalized):
            return intent, 0.90
    return "unknown", 0.0

def should_use_ai(text: str) -> bool:
    """AI is fallback only; deterministic prediction stays instant."""
    return predict(text)[0] == "unknown"
