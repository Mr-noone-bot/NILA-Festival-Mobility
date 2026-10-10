# NILA Team Module Ownership & Boundary Contracts

To ensure conflict-free, high-velocity parallel development across separate laptops during SAKTHI HACKFEST'26, module ownership is strictly partitioned.

---

## 1. Primary Module Ownership Matrix

| Team Member | Role | Owned Codebase Directories | Owned Test Directories |
| :--- | :--- | :--- | :--- |
| **Gugaan** | Project Owner / Integration Lead / Prediction + Simulation + Gemini | `backend/prediction/`<br>`backend/simulation/`<br>`backend/ai/` | `tests/prediction/`<br>`tests/simulation/`<br>`tests/ai/` |
| **Sanjay** | Backend + Optimization + Routing | `backend/api/`<br>`backend/core/`<br>`backend/optimization/`<br>`backend/routing/` | `tests/api/`<br>`tests/optimization/`<br>`tests/routing/` |
| **Chandhana** | Frontend + UI/UX + Maps | `frontend/` | `tests/frontend/` |
| **Madhu** | Tamil Nadu Data + Validation | `data/`<br>`docs/data/` | `tests/data/` |

---

## 2. Shared Assets

- `docs/` (Architecture, Contracts, Integration specs)
- `README.md`
- `requirements.txt`
- `.env.example`
- `.gitignore`

---

## 3. Boundary & Non-Interference Rules

1. **No Silent Overwrites**: No team member shall commit changes to another member's owned directory without explicit advance coordination.
2. **Interface First**: When an interface between two modules needs to change (e.g., Sanjay's optimization output shape consumed by Gugaan's AI Copilot or Chandhana's UI), the update MUST first be agreed upon in `docs/api/contracts.md`.
3. **Mock Dependencies**: Chandhana (Frontend) can mock API responses using the contracts in `docs/api/contracts.md` while Sanjay and Gugaan implement the endpoints.
4. **Isolated Testing**: Each teammate's tests reside in their designated `tests/<module>/` directory, preventing test suite conflicts.
