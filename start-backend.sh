#!/bin/bash

echo "Starting TestMyKnowledge Backend Server..."
echo ""

cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/Updating dependencies..."
pip install -r requirements.txt

echo ""
echo "Starting FastAPI server..."
echo "Backend will be available at: http://localhost:8000"
echo "API Documentation at: http://localhost:8000/docs"
echo ""

python run.py

