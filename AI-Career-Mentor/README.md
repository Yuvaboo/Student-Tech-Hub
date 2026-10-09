# AI Career & Project Mentor for Students

An intelligent, hybrid ML + LLM system that generates highly personalized project and career roadmaps for students based on their profile, skills, and available time.

## Architecture
Form (Streamlit) → FastAPI Backend → ML Engine (Sentence-Transformers) → LLM Layer (Gemini 2.5 Flash API) → SQLite + ChromaDB → Dashboard (Streamlit).

## Setup & Run Locally

### 1. Prerequisites
- Python 3.11+
- Virtual Environment recommended.

```bash
git clone <repo>
cd AI-Career-Mentor
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables
Copy `.env.example` to `.env` and fill in:
- `GEMINI_API_KEY`: Get from Google AI Studio.
- `YOUTUBE_API_KEY`: Get from Google Cloud Console.
- `SMTP_*`: Your email credentials for reminders.

### 3. Generate Data
Generate the synthetic projects and skills CSVs:
```bash
python generate_data.py
```

### 4. Start Backend
In a new terminal:
```bash
uvicorn src.backend.main:app --reload
```

### 5. Start Frontend
In a new terminal:
```bash
streamlit run src.frontend.app.py
```

## Features and Hybrid System
1. **ML Layer (Recommender):** Uses `sentence-transformers/all-MiniLM-L6-v2` to compute cosine similarity between the user's current skills + interests and the project domains. 
2. **Difficulty & Duration:** Calculated using heuristic formulas factoring in missing skills, project complexity, and user's available time.
3. **LLM Layer:** Uses the Gemini Structured Outputs API (Pydantic models) to strictly enforce JSON outputs for Roadmaps, Career paths, and tooling.
4. **AI Twin & Chatbot:** Stores user context in ChromaDB. Evaluates tasks completed vs pending to adjust pace in the system prompt.
5. **Reminders:** Uses `APScheduler` to schedule emails offset by weeks.

## Limitations & Future Scope
- **Data:** The `projects.csv` and `skills.csv` are currently synthetic (generated via script). In a production environment, this should be scraped from GitHub or Kaggle to provide thousands of diverse projects.
- **Difficulty Model:** The difficulty percentage uses a heuristic linear calculation. With real student completion data, an XGBoost regressor should be trained.
- **Security:** SQLite is used for simplicity. Migrate to PostgreSQL + Supabase/Firebase Auth for scale.

## Deployment Guide (Streamlit Cloud + Render)
1. **Backend (Render):**
   - Push code to GitHub.
   - Connect Render to the repo, select "Web Service".
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn src.backend.main:app --host 0.0.0.0 --port $PORT`
2. **Frontend (Streamlit Cloud):**
   - Connect Streamlit Cloud to the repo.
   - Set the main file path to `src/frontend/app.py`.
   - Update `API_URL` in `app.py` to point to the Render backend URL instead of localhost.
   - Add Secrets (GEMINI_API_KEY, YOUTUBE_API_KEY) in Streamlit settings.
