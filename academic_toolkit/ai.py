"""Optional low-latency local AI adapter.

AI is never required for deterministic toolkit actions and never executes shell
commands. It only classifies natural-language requests into allow-listed intents.
Created by Fredy Luis Vidalón Lozano.
"""
from __future__ import annotations
import json
import urllib.request
from dataclasses import dataclass

ALLOWED_INTENTS = {
    "install_program", "uninstall_program", "prepare_career",
    "clean_temporaries", "diagnose_mysql", "repair_mysql",
    "list_installed", "unknown"
}

@dataclass
class AIConfig:
    endpoint: str = "http://127.0.0.1:11434/api/chat"
    model: str = "qwen3:0.6b"
    timeout: float = 8.0
    keep_alive: str = "10m"
    num_ctx: int = 1024
    num_predict: int = 80

class LocalAI:
    def __init__(self, config: AIConfig | None = None):
        self.config = config or AIConfig()

    def classify(self, text: str) -> dict:
        prompt = (
            "Classify the Windows support request. Return JSON only with keys "
            "intent, target, confidence. intent must be one of: "
            + ", ".join(sorted(ALLOWED_INTENTS)) + ". Request: " + text[:800]
        )
        payload = {
            "model": self.config.model,
            "stream": False,
            "keep_alive": self.config.keep_alive,
            "messages": [{"role":"user","content":prompt}],
            "options": {"temperature":0, "num_ctx":self.config.num_ctx,
                        "num_predict":self.config.num_predict}
        }
        request = urllib.request.Request(
            self.config.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        raw = data.get("message", {}).get("content", "{}")
        raw = raw.strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(raw)
        if result.get("intent") not in ALLOWED_INTENTS:
            result["intent"] = "unknown"
        return result

    def warmup(self) -> bool:
        """Load the configured model into memory without granting capabilities."""
        try:
            self.classify("listar programas instalados")
            return True
        except Exception:
            return False
