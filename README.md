# qa-testgen-prototype

Исследовательский прототип сравнивает прямую генерацию pytest-тестов и
мультиагентную двухуровневую генерацию через BDD-сценарии. Proposed workflow
генерирует сценарии, валидирует их, преобразует в pytest и программно проверяет
синтаксис с циклом исправления.

## Запуск

```bash
cp .env.example .env
pip install -e .
python -m qa_testgen.cli run-proposed \
  --project-dir examples/ecommerce/app \
  --requirements-file examples/ecommerce/requirements.md
```

Baseline запускается командой `run-baseline`, сводка артефактов - `compare`.

## Docker Compose

```bash
docker compose run --rm qa-testgen run-proposed \
  --project-dir examples/ecommerce/app \
  --requirements-file examples/ecommerce/requirements.md
```

