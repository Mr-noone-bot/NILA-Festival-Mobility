# NILA Git Branch Strategy

## 1. Branch Architecture

To prevent race conditions, merge conflicts, and accidental regressions during the 24-hour sprint, development is organized around personal feature branches:

```
                  ┌── gugaan-prediction ──┐
                  │                       │
                  ├── sanjay-backend ─────┤
── main (stable) ─┼                       ├── main (tested integrations)
                  ├── chandhana-frontend ─┤
                  │                       │
                  └── madhu-data ─────────┘
```

---

## 2. Designated Branch Roles

- **`main`**: The canonical production-ready branch. Must always be deployable and runnable. All code merged here has passed health and regression checks.
- **`gugaan-prediction`**: Active development branch for crowd prediction models, surge simulation, and Gemini copilot orchestration.
- **`sanjay-backend`**: Active development branch for FastAPI endpoints, OR-Tools fixed-fleet optimization, and OSRM routing proxy.
- **`chandhana-frontend`**: Active development branch for React, Vite, Tailwind UI, MapLibre, and deck.gl visualizations.
- **`madhu-data`**: Active development branch for Tamil Nadu festival, temple, stop, and route data curation and schema validation.

---

## 3. Workflow & Policy

1. **Owner-Managed Branches**: Working branches are created and managed by the Project Owner as team members onboard.
2. **Sync Frequently**: Before starting a feature or preparing a PR, rebase or merge from `main`:
   ```bash
   git checkout <your-branch>
   git fetch origin
   git merge origin/main
   ```
3. **Integration Gate**: Merges into `main` occur in small, verified increments after confirming:
   - Backend tests pass (`pytest`)
   - Frontend builds cleanly (`npm run build`)
   - No secrets or untracked temporary files are introduced
