ADK Guest Chat - Run Instructions

1) Copy .env.example -> .env and fill your API key / Vertex settings.
2) Create Python venv:
   python -m venv .venv
   source .venv/bin/activate   # on Windows use: .venv\Scripts\activate

3) Install deps:
   pip install -r requirements.txt

4) Start the app:
   uvicorn main:app --reload --port 8000

5) Open http://127.0.0.1:8000 in your browser.

Notes:
- This project uses google-adk's InMemoryRunner in a demo pattern; adjust model and auth per your environment.
- For production, replace InMemoryRunner/session with persistent session service and secure storage.