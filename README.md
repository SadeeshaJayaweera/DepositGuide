<div align="center">
  <img src="https://raw.githubusercontent.com/SadeeshaJayaweera/DepositGuide/main/frontend/public/favicon.svg" alt="DepositGuide Logo" width="120" />
  <h1>DepositGuide 🚀</h1>
  <p><strong>Intelligent AI-driven financial health tracking and deposit optimization.</strong></p>

  <p>
    <a href="#about-the-project">About</a> •
    <a href="#the-problem--solution">Problem & Solution</a> •
    <a href="#architecture--stack">Architecture</a> •
    <a href="#multi-agent-system">Multi-Agent System</a> •
    <a href="#getting-started">Getting Started</a>
  </p>
</div>

---

## 📖 About the Project

**DepositGuide** is a cutting-edge, full-stack financial advisory platform designed to take the guesswork out of personal finance. By securely parsing your raw bank and credit card statements, DepositGuide builds a comprehensive profile of your spending behavior, forecasts your cash flow, and provides AI-driven, highly optimized deposit and repayment strategies.

Whether you're trying to figure out how to navigate complex statement APRs or looking for the mathematically optimal way to distribute your discretionary income into high-yield deposits, DepositGuide acts as your personal, automated financial advisor.

## ⚠️ The Problem & 💡 Solution

### The Problem
- **Data Overload**: Bank statements are dense, poorly formatted, and difficult for the average person to extract actionable insights from.
- **Hidden Fees & Complex APRs**: Understanding the true cost of minimum payments, cash advances, and rolling balances requires tedious spreadsheet calculations.
- **Suboptimal Savings**: People often leave money sitting in low-yield checking accounts or pay down the wrong debt first, missing out on thousands in potential interest savings or earnings over time.

### The Solution
DepositGuide solves this by employing a sophisticated pipeline of AI agents that automatically:
1. Parse messy, unstructured PDFs and CSVs into strict, structured data.
2. Analyze your spending patterns, risk tolerance, and salary cycles.
3. Simulate and forecast your cash flow.
4. Generate an actionable, step-by-step deposit schedule and repayment strategy to maximize your baseline interest.

## 🏗️ Architecture & Stack

DepositGuide is built as a modern, containerized **Monorepo** to ensure seamless development and deployment.

### Backend
- **Python 3.11 & FastAPI**: High-performance, asynchronous API framework.
- **PostgreSQL 16**: Robust, relational database for secure financial data storage.
- **SQLModel & Alembic**: Next-generation ORM seamlessly combining SQLAlchemy and Pydantic, with reliable schema migrations.
- **PDFPlumber & Pytest**: For robust, regex-backed heuristic extraction and comprehensive test coverage.

### Frontend
- **React 18 & TypeScript**: Strongly-typed, component-based UI.
- **Vite**: Lightning-fast build tool and development server.
- **Tailwind CSS**: Utility-first CSS framework for a stunning, responsive, and modern design system.
- **React Router**: For seamless Single-Page Application (SPA) navigation.

### DevOps
- **Docker Compose**: One-click local orchestration of the database and backend services.

## 🤖 Multi-Agent System

The core intelligence of DepositGuide relies on a pipeline of 9 specialized components working in harmony:

1. **Statement Parsing** (`statement_parsing.py`): An adapter-pattern agent that reads raw PDFs/CSVs and structures balances, APRs, and transactions.
2. **Statement Explainability** (`statement_explainability.py`): Translates complex banking jargon and hidden statement fees into plain English.
3. **Behavioral Profiling** (`behavioral_profiling.py`): Analyzes historical transactions to model your discretionary spend and risk tolerance.
4. **Interest Engine** (`interest_engine.py`): A high-precision calculator that models projected vs. baseline interest over time.
5. **Spending Insights** (`spending_insights.py`): Categorizes expenditures and identifies hidden leaks in your budget.
6. **Cash Flow Forecast** (`cash_flow_forecast.py`): Predicts your upcoming liquidity based on your salary cycle and recurring bills.
7. **Deposit Recommendation** (`deposit_recommendation.py`): The core optimizer that synthesizes your profile and cash flow into a step-by-step action plan.
8. **Conversational Query** (`conversational_query.py`): A chat interface allowing you to ask natural language questions about your finances.
9. **Orchestrator**: The implicit system that coordinates the hand-off of data between the 8 domain agents.

## 🚀 Getting Started

### Prerequisites
- [Docker](https://www.docker.com/) and Docker Compose
- [Node.js](https://nodejs.org/) (v18+)
- [Python 3.11](https://www.python.org/)

### 1. Start the Backend & Database
The backend and Postgres database are fully containerized. Spin them up with a single command:
```bash
docker compose up -d --build
```
*The API will be available at `http://localhost:8000`. You can verify it's running by visiting `http://localhost:8000/health`.*

### 2. Run Database Migrations
To initialize the SQLModel tables in Postgres:
```bash
docker compose exec api alembic upgrade head
```

### 3. Start the Frontend
In a new terminal, navigate to the frontend directory, install dependencies, and start the Vite dev server:
```bash
cd frontend
npm install
npm run dev
```
*The application will be accessible at `http://localhost:5173`.*

---

<div align="center">
  <i>Built with ❤️ for better financial health.</i>
</div>
