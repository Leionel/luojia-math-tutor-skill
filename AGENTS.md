# Repository Guidelines

## Project Structure & Module Organization

The primary app lives under `apps/`. `apps/api/app/` contains the FastAPI backend: routes in `api/`, tutoring orchestration in `tutor/`, model adapters in `llm/`, and math or knowledge utilities in named packages. Backend tests are in `apps/api/tests/`. The Next.js frontend is in `apps/web/`: route pages in `app/`, reusable UI in `components/`, shared client logic in `lib/`, and static assets in `public/`.

Tutor instructions and curated knowledge data are in `luojia-math-tutor/`, especially `SKILL.md` and `references/`. Root-level `scripts/` validate data and run cross-platform tests. Treat `outputs/`, `results/`, local databases, uploads, `.next/`, and virtual environments as generated artifacts.

## Build, Test, and Development Commands

- `npm install` and `cd apps/web && npm install`: install root and frontend dependencies.
- `npm run dev:api`: start FastAPI with reload on port `8000`.
- `npm run dev:web`: start Next.js on port `3000`.
- `npm test`: validate knowledge JSON, run the API test suite, and run frontend utility tests.
- `npm run test:api`: run backend `pytest` tests only.
- `npm run test:web:ui`: run Node tests for frontend runtime and security helpers.
- `npm run build:web`: create and type-check the production frontend build.
- `cd apps/web && npm run lint`: run Next.js lint checks.

## Coding Style & Naming Conventions

Use four spaces in Python and two in TypeScript/TSX. Keep API route handlers thin; place tutoring behavior in focused service modules. Use `snake_case` for Python, `PascalCase` for React components, and `camelCase` for TypeScript. Prefer existing UI components and CSS variables. Keep comments brief and explain intent.

## Testing Guidelines

Backend tests use `pytest` and follow `test_*.py`; frontend helper tests use Node's test runner and `*.test.ts`. Add regression coverage for bug fixes. Before opening a PR, run `npm test` and `npm run build:web`.

## Commit & Pull Request Guidelines

Use concise, imperative commits matching project history: `feat:`, `fix:`, `test:`, or `docs:`. Keep each commit focused. Pull requests should summarize behavior changes, list verification commands, link relevant issues, and include screenshots for visible UI changes. Call out schema, environment, or knowledge-data changes explicitly.

## Security & Configuration Tips

Keep secrets in ignored `.env` files. Never commit `LLM_API_KEY`, user keys, databases, or uploaded files. Common settings include `DATABASE_URL`, `LLM_BASE_URL`, `LLM_MODEL`, `ALLOW_USER_API_KEY`, and `NEXT_PUBLIC_API_BASE_URL`.
Treat model output, uploaded filenames, video metadata, and math expressions as untrusted. Use the existing sanitizers and expression parsers instead of raw HTML rendering or dynamic evaluation.
