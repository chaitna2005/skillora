#!/bin/bash

echo "Starting TestMyKnowledge Frontend..."
echo ""

cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "Starting React development server..."
echo "Frontend will be available at: http://localhost:3000"
echo ""

npm start

