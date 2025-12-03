import yaml
from pathlib import Path
from typing import Any, Dict

class Prompts:
    _prompts: Dict[str, Any] = {}
    _loaded: bool = False

    @classmethod
    def load(cls):
        if cls._loaded:
            return
        
        
        base_dir = Path(__file__).resolve().parent.parent
        prompts_path = base_dir / "prompts.yaml"
        
        if not prompts_path.exists():
            raise FileNotFoundError(f"Prompts file not found at {prompts_path}")
            
        with open(prompts_path, "r", encoding="utf-8") as f:
            cls._prompts = yaml.safe_load(f)
        
        cls._loaded = True

    @classmethod
    def get(cls, key: str) -> str:
        if not cls._loaded:
            cls.load()
            
        keys = key.split(".")
        value = cls._prompts
        
        try:
            for k in keys:
                value = value[k]
            
            if not isinstance(value, str):
                 raise ValueError(f"Key {key} does not point to a string prompt")
                 
            return value
        except (KeyError, TypeError):
            raise KeyError(f"Prompt key '{key}' not found")
