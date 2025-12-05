from app.core.prompts_data import PROMPTS


class Prompts:
    @classmethod
    def get(cls, key: str) -> str:
        keys = key.split(".")
        value = PROMPTS
        try:
            for k in keys:
                value = value[k]
            if not isinstance(value, str):
                raise ValueError(f"Key {key} does not point to a string prompt")
            return value
        except (KeyError, TypeError):
            raise KeyError(f"Prompt key '{key}' not found")
