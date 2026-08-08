# DepositGuide

DepositGuide is a full-stack application that provides intelligent recommendations for optimizing your finances. 

## Architecture

The project consists of 9 core components (as specified in the Rules file):
1. statement_parsing
2. statement_explainability
3. behavioral_profiling
4. interest_engine
5. spending_insights
6. cash_flow_forecast
7. deposit_recommendation
8. conversational_query
9. Orchestrator (Implicit)

### Setup Instructions

1. Start the backend and database:
```bash
docker compose up -d
```
2. Run database migrations:
```bash
docker compose exec api alembic upgrade head
```
3. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```
