# Football Predictor

Full-stack football analytics starter using Next.js/React + Tailwind, FastAPI, PostgreSQL and XGBoost. It is designed around a dark prediction-card UI and supports Winner/Double Chance, Over/Under 2.5 Goals and Corner projection.

## Run
1. Copy `.env.example` to `.env` and set `API_FOOTBALL_KEY` and a strong `ADMIN_TOKEN`.
2. `docker compose up --build`
3. API: http://localhost:8000/docs
4. Frontend: http://localhost:3000
5. Ingest today's fixtures: `docker compose exec backend python scripts/ingest.py`
6. Train after enough completed matches: `curl -X POST -H "Authorization: Bearer change-me" http://localhost:8000/api/admin/retrain`

## Architecture
- `backend/app/ml/features.py`: feature engineering.
- `backend/app/ml/train.py`: XGBoost training and model versioning.
- `backend/app/services/predictor.py`: inference.
- `backend/app/services/insights.py`: deterministic, data-driven insight generation.
- `backend/app/services/scheduler.py`: Monday/Thursday 05:00 UTC retraining.
- `backend/app/services/provider.py`: API-Football adapter.
- `frontend/app/components/PredictionCard.tsx`: reusable UI card.

## Production notes
The supplied ingestion script is intentionally small. For production, add paginated historical ingestion, API rate-limit handling, fixture statistics endpoints for corners/xG, validation splits/time-series cross-validation, Optuna studies persisted to PostgreSQL, feature-store/version metadata, and authentication/authorization around admin actions.
