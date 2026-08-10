<div align="center">
  
  <h1>💳 DepositGuide</h1>
  <p><strong>An Autonomous Multi-Agent System for Credit Card Debt Optimization</strong></p>

  <img alt="GitHub code size in bytes" src="https://img.shields.io/github/languages/code-size/SadeeshaJayaweera/DepositGuide?color=indigo">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Tech" src="https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20Gemini-blue">

</div>

<br />

DepositGuide is a cutting-edge, **multi-agent financial intelligence system** designed to solve a ubiquitous problem: sub-optimal credit card repayment. By intelligently breaking down minimum payments, forecasting cash flow, and generating hyper-personalized deposit schedules, DepositGuide can mathematically reduce accrued interest by up to **33% per billing cycle**.

---

## 🎯 What Problem Does This Solve?

Credit card statements are notoriously opaque, and the concept of "daily compounding interest" is widely misunderstood. Most consumers either pay the "Minimum Due" (which maximizes bank profits through interest) or they attempt to pay off the entire balance on the due date (which can still accrue massive interest if they carried a balance from the previous month).

DepositGuide solves this by identifying that **depositing funds earlier in the billing cycle strictly reduces the average daily balance**, thereby minimizing interest charges. The system autonomously reads your statement, analyzes your spending habits, and mathematically computes the perfect time to make partial deposits based on your actual liquidity constraints.

## 🧠 The 10-Agent Architecture

DepositGuide is powered by a sophisticated multi-agent pipeline mirroring modern AI research architectures:

1. **📄 Statement Parsing Agent**: Ingests opaque PDF or CSV statements from banks and extracts structured financial schemas (balances, APRs, dates).
2. **👤 Behavioral Profiling Agent**: Analyzes historical transaction velocity to infer salary cycles and discretionary spending habits.
3. **🛒 Spending Insights & Bill Prediction Agent**: Categorizes transactions, flags low-value "zombie" subscriptions, and forecasts recurring bills.
4. **📈 Cash-Flow Forecast Agent**: Merges behavioral profiles and bill predictions to project daily available liquidity limits.
5. **🧮 Interest Computation Engine**: A deterministic mathematical simulator calculating exact daily interest accruals based on the *Average Daily Balance* method.
6. **🤖 Deposit Recommendation Agent**: The optimization core. It executes a discrete search over feasible repayment schedules, constrained by the Cash-Flow Forecast, to find the exact two-installment schedule that minimizes interest.
7. **📝 Statement Explainability Agent**: Translates complex credit card legalese into plain-language summaries using Large Language Models (LLMs).
8. **💬 Conversational Query Agent**: A deeply grounded AI advisor that strictly answers user queries based on their internal financial context, refusing to hallucinate outside knowledge.
9. **💾 Semantic Memory Agent (RAG)**: Automatically extracts user facts from chat and stores them in a vector database, enabling the AI advisor to remember personal context continuously.
10. **✨ Interactive Dashboard**: A glassmorphic, modern React interface displaying actionable insights, interactive Recharts comparisons, and the conversational AI.

---

## 💻 Tech Stack

### Frontend
- **React 19 & Vite**: Lightning-fast modern SPA development.
- **Tailwind CSS**: Utility-first styling for a sleek, dark-mode glassmorphic aesthetic.
- **Recharts**: Beautiful, responsive charting to visualize interest savings.
- **Lucide-React**: Clean, consistent SVG iconography.

### Backend
- **FastAPI**: High-performance, async Python web framework.
- **SQLModel & Alembic**: Elegant ORM combining SQLAlchemy and Pydantic, with automated migrations.
- **Google Gemini 2.5 (Flash)**: Ultra-fast LLM driving the Explainability and Conversational agents.
- **Pytest**: Rigorous end-to-end integration testing proving the mathematical models.

### Infrastructure
- **PostgreSQL**: Production-grade relational database.
- **Docker Compose**: Seamless local container orchestration.
- **GitHub Actions**: Automated CI pipeline running linting, builds, and Pytest suites.

---

## 🚀 Quickstart (Local Development)

The easiest way to run the entire system is via Docker Compose.

### Prerequisites
- [Docker](https://www.docker.com/) installed on your machine.
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey).

### Running the Stack
1. Clone the repository:
   ```bash
   git clone https://github.com/SadeeshaJayaweera/DepositGuide.git
   cd DepositGuide
   ```
2. Export your Gemini API key:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```
3. Boot the stack:
   ```bash
   docker compose up --build
   ```
4. Access the beautiful React dashboard at **`http://localhost:3000`** and the backend API at **`http://localhost:8000`**.

---

## 🌐 Production Deployment

DepositGuide is built for modern cloud platforms:

- **Backend (Render / Fly.io)**: We provide a `render.yaml` blueprint to easily provision a managed PostgreSQL instance alongside the FastAPI web service.
- **Frontend (Vercel)**: A `vercel.json` configuration is included to effortlessly deploy the Vite SPA with proper client-side routing.

*For detailed instructions, refer to the [DEPLOYMENT.md](./DEPLOYMENT.md) guide.*

---

## 🔮 Limitations & Future Work

While the mathematical engine (Equation 2) has been rigorously tested in CI/CD to prove the ~33% interest reduction, the system currently operates on simulated user data.

**Next Steps:**
1. **User Studies**: Conduct empirical validation through large-scale user studies to measure actual adherence to the recommended two-installment schedules.
2. **Deep Learning Profiling**: Upgrade the Behavioral Profiling Agent with advanced time-series models to predict non-linear spending habits more accurately.
3. **Plaid Integration**: Connect directly to live bank APIs (e.g., via Plaid) to synchronize real-time cash flow instead of relying solely on uploaded credit card histories.
