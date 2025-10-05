To run:
git clone
venv/bin/activate
python3 run.py

Running the FastAPI server (for Charts & Insights)

The `demo.html` and `charts.html` dashboard needs a JSON API that serves candidate data.
This API is powered by FastAPI, which runs separately from the Flask app used for `run.py`.

Navigate to the backend directory:
From the project root:
```bash
cd flask_app

Start the FastAPI server:
You can run it with Uvicorn (the built-in FastAPI dev server):
uvicorn openballot_server.api:app --host 127.0.0.1 --port 8000 --reload
openballot_server.api → the module where your FastAPI app instance (app = FastAPI()) lives
--reload → automatically restarts on code changes
The server will start at http://127.0.0.1:8000


Run the visualization
Now that the API is live, open the charts page from your Flask app:
http://127.0.0.1:5500/flask_app/graph/openballot_server/charts.html
