# Deployment Guide

DepositGuide is designed to be easily deployed to modern cloud platforms. The backend is a standard FastAPI application (which can run on Render, Fly.io, or Heroku), and the frontend is a Vite React SPA (ideal for Vercel, Netlify, or Cloudflare Pages).

## 1. Deploying the Backend & Database (Render)

We have provided a `render.yaml` Blueprint to fully automate the backend deployment.

1. Create an account at [Render.com](https://render.com/).
2. Connect your GitHub repository.
3. In the Render Dashboard, click **New > Blueprint**.
4. Select your DepositGuide repository. Render will automatically detect the `render.yaml` file.
5. Render will provision:
   - A managed PostgreSQL database (`depositguide-db`).
   - A Python web service (`depositguide-backend`).
6. **Important Environment Variables**:
   - `DATABASE_URL`: Automatically linked by Render.
   - `GEMINI_API_KEY`: You MUST set this manually in the Render dashboard (Environment tab of your Web Service) with your Google AI Studio key.

## 2. Deploying the Frontend (Vercel)

We have provided a `vercel.json` to handle client-side routing.

1. Create an account at [Vercel.com](https://vercel.com/).
2. Click **Add New > Project** and select your GitHub repository.
3. **IMPORTANT**: In the "Build and Output Settings" or project settings, change the **Root Directory** to `frontend`. Vercel will then automatically detect the Vite framework.
4. **Important Environment Variables**:
   - Before clicking Deploy, expand "Environment Variables".
   - Add `VITE_API_BASE_URL` and set its value to your newly deployed Render backend URL (e.g., `https://depositguide-backend.onrender.com`).
5. Click **Deploy**.

## 3. Local Deployment (Docker Compose)

To run the entire production-like stack locally (Postgres, Backend, and Nginx-served Frontend):

```bash
# Add your Gemini API key
export GEMINI_API_KEY="your-api-key"

# Build and start the stack
docker compose up --build
```

The frontend will be available at `http://localhost:3000` and the backend at `http://localhost:8000`.
