#!/bin/bash

# Exit on error
set -e

echo "🧪 Starting Dream Recorder in development mode..."

# Activate virtual environment first
if [ -d "venv" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found. Please run './setup.sh' first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 12 ]; then
    echo "📌 Python 3.12+ detected. Using gevent for WebSocket support."
    
    # Check if gevent is already installed
    if ! python3 -c "import gevent" 2>/dev/null; then
        echo "📦 Installing gevent for WebSocket support..."
        pip install gevent==23.9.1 gevent-websocket==0.10.1
    else
        echo "✅ gevent already installed."
    fi
else
    echo "📌 Python version: $PYTHON_VERSION"
fi

# Export environment variables
export FLASK_APP=backend/app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "📦 Installing tmux for split terminal development..."
    sudo apt-get update
    sudo apt-get install -y tmux
fi

# Create a new tmux session
tmux new-session -d -s dream-recorder

# Split window horizontally and start the backend server in the top pane
tmux send-keys -t dream-recorder:0.0 "source venv/bin/activate && python backend/app.py" C-m

# Split the window vertically and start the frontend dev server in the bottom right pane
tmux split-window -v -t dream-recorder:0.0
tmux send-keys -t dream-recorder:0.1 "cd frontend && npm run dev" C-m

# Attach to the tmux session
tmux attach-session -t dream-recorder

# The script won't reach here unless the tmux session is closed
echo "💤 Dream Recorder development session has ended." 