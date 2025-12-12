# the-ultimate-analysis-machine

Monorepo for market and financial analysis workflows. The top-level `Makefile` controls the **daily-analysis-system** located in `src/daily-analysis-system/`, while configuration yaml files live under `config/`.

## Daily workflow (run from repo root)

```bash
make install        # set up the venv for daily-analysis-system
make fetch-all      # pull indices, holdings, and news data
make analyze-daily  # run Claude/Ollama analysis prompts
make daily          # fetch-all + analyze-daily
make update-pages   # convert markdown → docs/*.html
make deploy         # update-pages + commit + push
```

All HTML lives in root `docs/`, which is also the GitHub Pages publish directory. Markdown sources remain inside `src/daily-analysis-system/reports/markdown/`.

## Automation helpers

Wrapper scripts under `utils/` forward arguments to the same Make targets:

- `utils/run_daily.sh` – `make daily` (fetch + analyze)
- `utils/fetch_all.sh` – `make fetch-all`
- `utils/update_pages.sh` – `make update-pages`
- `utils/deploy.sh` – `make deploy`

Feel free to append extra flags (e.g., `TIME_SUFFIX=0800 utils/run_daily.sh`).

## Environment configuration

- Copy `.env.example.local` → `.env` (at the repo root) and fill in `CLAUDE_CODE_OAUTH_TOKEN`, `TZ`, and other secrets.
- `utils/run_daily_workflow.sh` automatically loads this root `.env` (and only falls back to the subproject if needed), so cron/launchd and local shells share the same config.
- Keep `.env` out of Git; only the sample files should be tracked.

## GitHub Pages

- `.github/workflows/build-pages.yml` installs dependencies, runs `make update-pages`, and auto-commits `docs/` whenever reports, scripts, or the workflow change.
- Local preview: `make preview-pages` → browse http://localhost:8000.
- Manual publishing: `make deploy` (updates HTML, commits `docs/` + `reports/`, pushes to `main`).

For the detailed architecture, troubleshooting tips, and configuration schemas, see `src/daily-analysis-system/README.md` and `src/daily-analysis-system/QUICKSTART.md`.
