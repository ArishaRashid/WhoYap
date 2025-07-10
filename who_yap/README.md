# WhoYap Backend

## .env Example
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key
```

## Setup
1. Install requirements:
   ```
   pip install -r requirements.txt
   ```
2. Add your `.env` file in the project root.
3. Run locally:
   ```
   uvicorn app.main:app --reload
   ```

## Llama-3 via Ollama
1. [Install Ollama](https://ollama.com/download) on your machine.
2. Pull the Llama-3 model:
   ```
   ollama pull llama3
   ```
3. Start Ollama (it runs as a background service by default).
4. The backend will connect to Ollama at http://localhost:11434.

## Deploy on Vercel
- Use [Vercel Python docs](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python) for FastAPI.
- Set environment variables in Vercel dashboard.
- Connect to Supabase using the provided URL and Key.

## Supabase Setup
- Run `supabase_schema.sql` in your Supabase SQL editor.
- Enable the `pgvector` extension.

## API Endpoints
- `/upload` — Upload WhatsApp `.txt` file
- `/parse` — Parse and store chat
- `/create-session` — Create game session
- `/request-join` — Request to join session
- `/approve-join` — Approve/decline join
- `/next-question` — Get quiz question
- `/submit-answer` — Submit answer
- `/llama3-chat` — Test Llama-3 via Ollama

## CORS
- CORS is enabled for all origins for development. Restrict in production as needed. 