# NILA Hackathon Integration Rules

Every team member working on NILA must adhere to these 15 core integration rules:

1. **`main` Must Always Remain Runnable**: The `main` branch must never be broken. Any code pushed or merged into `main` must pass baseline tests and allow both backend and frontend to start cleanly.
2. **No Force Pushes**: `git push --force` and `git reset --hard` against remote branches are strictly prohibited.
3. **No API Keys or Secrets Committed**: Never commit `.env`, credentials, passwords, or personal access tokens. Use `.env.example` as a template and ensure all secret files remain in `.gitignore`.
4. **No Random Folder Restructuring**: The established repository tree is fixed. Do not relocate, rename, or nest top-level or architectural directories without team consensus.
5. **No Duplicate Implementations**: Calculations and logic must exist in their single authoritative module. Do not replicate routing, math, or data models across multiple places.
6. **Backend Owns Calculations**: All mathematical modeling, travel-time computations, crowd surge curves, and optimization logic belong exclusively to the backend.
7. **Frontend Owns Presentation**: The frontend handles rendering, user interaction, maps, heatmaps, and responsiveness. Frontend components must not invent business logic.
8. **Data Owner Owns Dataset Structures**: Madhu is the authoritative owner of `data/`. All updates to JSON schemas, temple metadata, and festival profiles must route through the data owner.
9. **Gemini Does Not Invent Numerical Results**: Gemini acts purely as an explanation and query orchestration layer. Predictions, fleet distributions, and route calculations are 100% deterministic.
10. **Optimization Must Enforce Fixed Fleet**: The sum of allocated buses across all stops must always equal the fixed fleet size $F_{\text{total}}$ before, during, and after optimization.
11. **Every Bus Movement Must Show Trade-Off**: Every repositioning instruction must explicitly expose Source Stop, Destination Stop, Buses Transferred, Departure, Arrival, Travel Duration, Source Service Loss, Expected Benefit, and Network Effect.
12. **All Major Features Must Have Tests**: Every core backend algorithm, schema, and API endpoint must have corresponding unit/integration tests in `tests/`.
13. **Changes Committed in Small Logical Units**: Commit frequently with clear, descriptive commit messages rather than giant mega-commits.
14. **Pull Before Starting Major Work**: Always `git pull origin <branch>` before beginning a development session to stay in sync and prevent merge conflicts.
15. **Never Silently Modify Another Teammate's Module**: Respect module ownership defined in `docs/integration/team-ownership.md`. Cross-module changes require explicit peer coordination.
