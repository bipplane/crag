# CRAG: Educational RAG System

This project is a decoupled microservices application designed for scalable machine learning workloads and RAG (Retrieval-Augmented Generation) constrained to specific multi-tenant modules. 

## Prerequisites
* **Node.js** (v18+)
* **Python** (3.10+)
* A **Google Gemini API Key** (for the LLM & Embeddings)

---

## 1. Running the Backend (FastAPI + LlamaIndex)

The backend handles the RAG ingestion, querying, and LLM processing.

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   * **Windows:**
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * **Mac/Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   *(If you haven't already, the environment is pre-configured with requirements in the previous steps)*
   ```bash
   pip install fastapi uvicorn celery redis psycopg2-binary SQLAlchemy pydantic llama-index llama-parse openai-whisper pylti1p3 python-multipart python-jose[cryptography] python-dotenv llama-index-llms-gemini llama-index-embeddings-gemini
   ```

4. **Configure your Environment Variables:**
   Create a `.env` file in the `backend` folder (you can copy `.env.example`):
   ```env
   GOOGLE_API_KEY=your_actual_gemini_api_key_here
   ```

5. **Start the Development Server:**
   ```bash
   uvicorn main:app --reload
   ```
   *The backend will be running at `http://127.0.0.1:8000`.*
   *(You can access the API Swagger docs at `http://127.0.0.1:8000/docs`)*

---

## 2. Running the Frontend (React + Vite)

The frontend provides a test-bed UI to upload documents (`.txt`, `.md`) to a specific Tenant/Module ID and query them.

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   *(If running for the first time or if you wiped node_modules)*
   ```bash
   npm install --legacy-peer-deps
   ```

3. **Start the Vite Development Server:**
   ```bash
   npm run dev
   ```
   *The frontend will be running at `http://localhost:5173`.*

---

## 3. Running Automated Tests

**Backend Tests (pytest):**
```bash
cd backend
.\venv\Scripts\activate
pytest
```

**Frontend Tests (vitest):**
```bash
cd frontend
npx vitest run
```