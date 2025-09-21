#!/bin/bash
cd backend
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000 --reload
