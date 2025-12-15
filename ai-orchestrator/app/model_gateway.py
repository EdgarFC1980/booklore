import yaml
import httpx
from dataclasses import dataclass
from .settings import settings

@dataclass
class ModelTarget:
    name: str
    backend: str
    host: str | None
    model: str

class ModelGateway:
    def __init__(self) -> None:
        with open(settings.models_config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        self.default_tier = cfg.get("default_tier", "local_light")
        self.tiers = cfg.get("tiers", {})

    async def classify(self, prompt: str, tier: str | None = None) -> str:
        tier = tier or self.default_tier
        t = self.tiers[tier]

        if t["backend"] == "ollama":
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(
                    f'{t["host"].rstrip("/")}/api/generate',
                    json={"model": t["model"], "prompt": prompt, "stream": False},
                )
                r.raise_for_status()
                return r.json().get("response", "")

        raise RuntimeError("backend no soportado")
