# DepositGuide: Multi-Agent Financial Optimizer

DepositGuide is a multi-agent system designed to optimize credit card repayment schedules and minimize interest accrual through personalized behavioral profiling and cash-flow forecasting.

## Architecture

The system is built on a 9-component multi-agent architecture (mirroring Figure 1 of the foundational research paper):

1. **Statement Parsing Agent**: Extracts financial data from uploaded PDFs/CSVs using an adapter pattern.
2. **Behavioral Profiling Agent**: Analyzes historical transactions to infer salary cycles and discretionary spend.
3. **Spending Insights & Bill Prediction Agent**: Categorizes transactions and forecasts upcoming recurring bills.
4. **Cash-Flow Forecast Agent**: Combines behavioral profiles and bill predictions to estimate daily available liquidity.
5. **Interest Computation Engine**: A mathematical simulator that calculates exact daily interest accrual.
6. **Deposit Recommendation Agent**: The optimization core (Equation 2). It performs a discrete grid search over feasible candidate schedules, constrained by the Cash-Flow Forecast, to find the schedule that strictly minimizes projected interest.
7. **Statement Explainability Agent**: Translates complex credit card terminology into plain-language summaries using LLMs.
8. **Conversational Query Agent**: A grounded AI advisor that strictly answers user queries based solely on their internal financial context.
9. **Dashboard / Interactive Interface**: A React-based glassmorphic UI displaying the optimized insights and charts.

## Setup & Local Development

### Prerequisites
- Node.js (v20+)
- Python 3.11+
- Gemini API Key

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set API Key
export GEMINI_API_KEY="your-key-here"

# Run tests
pytest tests/ -v

# Run server
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker Compose (Full Stack)
```bash
export GEMINI_API_KEY="your-key-here"
docker compose up --build
```
Access the dashboard at `http://localhost:3000`.

## Deployment
See [DEPLOYMENT.md](./DEPLOYMENT.md) for automated instructions for Render (Backend/Postgres) and Vercel (Frontend).

## Limitations & Future Work
While the underlying mathematics (Equation 2) and agent coordination have been rigorously integration-tested to prove the ~33% interest reduction described in the research, the system currently lacks empirical validation against real-world user data. 

**Future Work (Section V):**
- Conduct a large-scale user study to measure actual adherence to the recommended two-installment schedules.
- Expand the Behavioral Profiling Agent with deep learning models to predict non-linear spending habits more accurately.
- Introduce Plaid integration for live bank account cash-flow syncing instead of relying solely on credit card transaction histories.
