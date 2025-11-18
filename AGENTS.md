# Repository Guidelines

## Project Structure & Modules
- `backend/`: FastAPI prototype (`main.py`, routers, `job_manager.py`).
- `frontend/`: Streamlit UI (`app.py`) and static web console in `frontend/web/`.
- `modules/`: Pipeline stages (audio, STT, text, TTS, RVC, Wav2Lip), each with `run.py` and `config/`.
- `orchestrator/`: `pipeline_runner.py` and `config.yaml` for end‑to‑end runs.
- `data/`: Inputs, intermediate artifacts, and `data/runs/{run_name}/` outputs.
- `shared/`, `docs/`, `tests/`, `scripts/`: Shared schemas/utils, specs, pytest suite, and helper PowerShell scripts.

## Build, Test, and Development Commands
- Environment setup (Windows, recommended): `scripts/setup_env.ps1` to create `.venv_backend` / `.venv_frontend` and install requirements.
- Run backend API: `uvicorn backend.main:app --reload --port 8000`.
- Run Streamlit UI: `streamlit run frontend/app.py`.
- Orchestrator pipeline: `python orchestrator/pipeline_runner.py --input-media data/inputs/sample.mp4`.
- Tests (backend): `scripts/run_tests.ps1 -Marker smoke` or `python -m pytest tests`.

## Coding Style & Naming Conventions
- Python 3.10+ with type hints where practical; follow PEP 8 (4‑space indents, max ~88–100 chars).
- Use `snake_case` for files, functions, and variables; `PascalCase` for classes; keep names in English even if messages/docs are Korean.
- Keep modules small and composable; prefer pure functions over side effects in `modules/*/run.py`.
- Match existing patterns in `backend/` and `modules/` instead of introducing new frameworks.

## Testing Guidelines
- Use `pytest` with tests under `tests/` named `test_*.py`; mirror module names where possible (e.g., `test_pipeline_smoke.py`).
- Prefer fast, deterministic tests; mock heavy models and subprocess calls (see existing smoke tests for patterns).
- Before opening a PR, run `scripts/run_tests.ps1 -Marker smoke` or `python -m pytest tests`.

## Commit & Pull Request Guidelines
- Follow the existing style: short, imperative subject with a prefix when relevant, e.g. `feat: 모듈 실행 로직 개선`, `fix: STT 설정 경로 버그`.
- Commits should be scoped to one logical change (code + tests + docs).
- PRs should include: purpose summary, key changes, how to run/verify (commands), and screenshots or logs for UI or pipeline changes.

## Agent-Specific Instructions
- Do not reorganize top‑level directories without explicit request; keep new code within the closest relevant module.
- Prefer minimal, targeted changes and avoid adding heavy dependencies without discussion.
- When editing configs under `modules/*/config` or `orchestrator/config.yaml`, preserve existing schema and placeholders; add new fields in a backward‑compatible way.
