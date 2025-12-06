# Prompts

LLM プロンプトテンプレート。

## ファイル

| ファイル | 役割 |
|---------|------|
| `prompts.yaml` | 全プロンプトテンプレート |

## プロンプト一覧

| キー | 用途 |
|-----|------|
| `metadata_generator.generate` | ゲーム情報の初回生成 |
| `metadata_critic.improve` | 生成結果の検証・修正 |
| `link_resolve.resolve` | 外部URL検証 |

## 使用方法

```python
from app.services.generator import _load_prompt
prompt = _load_prompt("metadata_generator.generate")
```
