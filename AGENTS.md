# Repository Guidelines

## Project Structure & Module Organization

The primary app lives under `apps/`. `apps/api/app/` contains the FastAPI backend: routes in `api/`, tutoring orchestration in `tutor/`, model adapters in `llm/`, and math or knowledge utilities in named packages. Backend tests are in `apps/api/tests/`. The Next.js frontend is in `apps/web/`: route pages in `app/`, reusable UI in `components/`, shared client logic in `lib/`, and static assets in `public/`. Tutor instructions and curated knowledge data are in `luojia-math-tutor/`, especially `SKILL.md` and `references/`. Root-level `scripts/` hold eval and maintenance tools; `evaluation/` holds the retrieval eval set; `results/` is generated output and is not tracked.

## Build, Test, and Development Commands

- `npm install` and `cd apps/web && npm install`: install root and frontend dependencies.
- `npm run dev:api`: start FastAPI with reload on port `8000`.
- `npm run dev:web`: start Next.js on port `3000` (these two scripts use `npm.cmd` and are Windows-only).
- `npm test`: validate knowledge JSON, run the API test suite, and run frontend utility tests.
- `npm run build:web`: create and type-check the production frontend build.
- `cd apps/web && npm run lint`: run Next.js lint checks.

## Testing Guidelines

Backend tests use `pytest` and follow `test_*.py`; frontend helper tests use Node's test runner and `*.test.ts`. Add regression coverage for bug fixes. Before pushing, run `npm test` and keep CI (`.github/workflows/ci.yml`) green.

- IMPORTANT: run pytest **from `apps/api`** — a root-level `python -m pytest` collects ~36 unrelated errors.
- IMPORTANT: the suite must stay offline. `tests/conftest.py` sets `LUOJIA_NO_DOTENV=1` and strips LLM/MINERU keys; do not remove that gate.

## Commit & Pull Request Guidelines

Use concise, imperative commits matching project history: `feat:`, `fix:`, `test:`, or `docs:`. Keep each commit focused. Pull requests should summarize behavior changes, list verification commands, link relevant issues, and include screenshots for visible UI changes. Call out schema, environment, or knowledge-data changes explicitly.

## Security & Configuration Tips

Keep secrets in ignored `.env` files. Never commit `LLM_API_KEY`, `MINERU_API_KEY`, `DASHSCOPE_API_KEY`, `NEXT_PUBLIC_DESMOS_API_KEY`, user keys, databases, or uploaded files; run `git grep "sk-"` before pushing. Common settings include `DATABASE_URL`, `LLM_BASE_URL`, `LLM_MODEL`, `ALLOW_USER_API_KEY`, and `NEXT_PUBLIC_API_BASE_URL`. The MinerU token expires after 90 days: upload failures with 401/403 mean regenerate it at mineru.net/apiManage.

Treat model output, uploaded filenames, video metadata, and math expressions as untrusted. Use the existing sanitizers (`apps/web/lib/html-sanitize.ts`) and expression parsers instead of raw HTML rendering or dynamic evaluation.

## Agent Gotchas

- Do not run `next build` while `npm run dev` is serving: it corrupts `apps/web/.next`. Stop the dev server first.
- `apps/web/tailwind.config.ts` remaps default Tailwind color names (slate/indigo/rose/amber/...) onto the farm-ink tokens, so the class name is not the rendered color. New UI should use the semantic tokens (`paper`/`olive`/`dai`/`cinnabar`/`ochre`) instead of raw palette names.
- Retrieval evals: `python scripts/build_retrieval_eval.py` regenerates `evaluation/retrieval_eval.json` from the textbook graph; `python scripts/eval_retrieval.py` runs all four arms (BM25 / vector / hybrid / course-graph dry-run). Only the vector arm needs a key (`DASHSCOPE_API_KEY`); without it, a local TF-IDF+LSA fallback is used.
- `luojia_tutor2_branch_log.md` and `luojia_tutor2_course_graph_research_refined.md` are the project's memory — update them (and `CODEX_HANDOFF.md` for agent onboarding) at the end of a work round instead of leaving context in commit messages.
