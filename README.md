# RupeeRadar

AI-powered personal finance assistant built to transform raw, messy bank statements into clean, structured insights.

## Project Structure

This project is structured as a monorepo containing:
- `apps/api`: Python FastAPI backend orchestrating parsing, hybrid rules/LLM categorization, recurring transaction detection, and insights.
- `apps/web`: Next.js (React) frontend featuring a glassmorphic dashboard built using Tailwind CSS.
- `Docs`: Product requirements, system architecture, and phase-wise implementation details.
- `data`: Sample bank statement files (CSV) for local testing.

---

## Getting Started

### Prerequisites
- [Node.js](https://nodejs.org/) (v18 or higher)
- [Python](https://www.python.org/) (v3.10 or higher)
- [Docker & Docker Compose](https://www.docker.com/) (Optional, for containerized run)

### Environment Configuration
1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Configure the `GROQ_API_KEY` inside `.env` with your Groq API key (used for transaction categorization and natural language insight formatting).

---

## Running with Docker Compose (Recommended)

To build and start both the backend API and Next.js frontend services:

```bash
docker compose build
docker compose up -d
```

- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **Backend Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

To stop the services:
```bash
docker compose down
```

---

## Running Locally for Development

### 1. Run the FastAPI Backend
Navigate to the api folder and install requirements:
```bash
cd apps/api
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Run the development server:
```bash
uvicorn main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`.

### 2. Run the Next.js Frontend
Navigate to the web folder and install packages:
```bash
cd apps/web
npm install
```

Start the Next.js development server:
```bash
npm run dev
```
The client dashboard will be available at `http://localhost:3000`.

---

## API Endpoints (Core)

- `GET /health`: Health status.
- `POST /api/v1/sessions`: Initialize an ephemeral session.
- `GET /api/v1/sessions/{id}/status`: Polling session pipeline status.
- `DELETE /api/v1/sessions/{id}`: Purge all session data and files.
- `GET /api/v1/sessions/{id}/summary`: Financial aggregates (income, spend, savings, savings rate, biggest transaction, top categories, monthly trends).
- `GET /api/v1/sessions/{id}/recurring`: Identified recurring payment groups (subscriptions, EMIs, rent, SIPs, insurance).
- `GET /api/v1/sessions/{id}/insights`: Ranked behavioral financial insights (rules-templated or Groq LLM polished).
- `GET /api/v1/sessions/{id}/report`: Self-contained printable HTML audit report.

---

## Production Cloud Deployment (Vercel + Railway)

### 1. Backend API (Railway)
- Deploy `apps/api` using the hardened `apps/api/Dockerfile` (runs as a non-root system user).
- **Environment Variables**:
  - `DATABASE_URL`: Connection string. Defaults to SQLite, but can connect to a managed PostgreSQL database (e.g. `postgresql://user:pass@host:port/db`) since `psycopg2-binary` is installed.
  - `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed origins (e.g., your Vercel deployment URL).
  - `GROQ_API_KEY`: Groq API key for AI categorization and insight polishing.
  - `UPLOAD_DIR`: Target path for statement file uploads (use persistent volumes on Railway to mount this directory, e.g. `/data/uploads`).

### 2. Frontend Client (Vercel)
- Deploy `apps/web` on Vercel using Next.js framework integration.
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: The domain URL of your live Railway API.

---

## Session Lifecycle & TTL (Time-To-Live)

To protect sensitive professional financial details, RupeeRadar implements a **24-hour Time-To-Live (TTL)** policy:
- Sessions, transaction ledgers, and metrics are saved with an expiration timestamp set to 24 hours after creation.
- A **lazy cleanup worker** triggers on new session requests, physically deleting statement files in `uploads/{session_id}` and deleting corresponding database entries.
- Users can click **Delete Session** in the dashboard header to trigger an immediate cascade purge.

---

## Development Milestones

- **Phase 0:** Setup foundation, SQLite ephemeral storage, Next.js branding layout, CORS health check. (Completed)
- **Phase 1:** CSV parsing heuristics, description cleaning, deduplication, transaction ingestion. (Completed)
- **Phase 2:** Hybrid rules engine & Groq LLM categorization fallback, overrides. (Completed)
- **Phase 3:** Recurring transactions classifier, metrics calculator, templated insights generator. (Completed)
- **Phase 4:** Recharts visuals, transaction list search, interactive dashboard filters, category override rule learning. (Completed)
- **Phase 5:** Standalone HTML report export, print media queries, non-root multi-stage Docker builds, lazy TTL filesystem cleanup. (Completed)
