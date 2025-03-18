#!/bin/bash

# Exit on error
set -e

echo "🚀 Setting up Dream Recorder..."

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 12 ]; then
    echo "📌 Python 3.12+ detected. Will use gevent for WebSocket support."
    PYTHON_312_COMPAT=true
else
    echo "📌 Python version: $PYTHON_VERSION"
    PYTHON_312_COMPAT=false
fi

# Create scripts directory if it doesn't exist
mkdir -p scripts

# Make scripts executable
if [ -f "scripts/install_pyaudio.sh" ]; then
    chmod +x scripts/install_pyaudio.sh
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade basic packages first to ensure compatibility
echo "📚 Upgrading pip and setuptools for compatibility..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "📚 Installing Python dependencies..."
# Try to install requirements, with error handling
if ! pip install -r requirements.txt; then
    echo "⚠️ Error installing some packages. Attempting individual installation..."
    
    # Read requirements line by line and install individually
    while read -r requirement; do
        # Skip comments and empty lines
        if [[ ! $requirement =~ ^#.* ]] && [ -n "$requirement" ]; then
            echo "Installing: $requirement"
            pip install "$requirement" || echo "Failed to install: $requirement"
        fi
    done < requirements.txt
    
    echo "⚠️ Some packages might not have been installed correctly."
    echo "⚠️ You might need to install them manually."
fi

# Install additional dependencies for Python 3.12
if [ "$PYTHON_312_COMPAT" = true ]; then
    echo "📦 Installing additional dependencies for Python 3.12 compatibility..."
    pip install gevent==23.9.1 gevent-websocket==0.10.1
fi

# Install Node.js dependencies if not already installed
if ! command -v node &> /dev/null; then
    echo "🟢 Installing Node.js (required for frontend development)..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Install npm packages for frontend
echo "🌐 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Install FFmpeg if not already installed
if ! command -v ffmpeg &> /dev/null; then
    echo "🎬 Installing FFmpeg..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔑 Creating .env file for API keys..."
    echo "OPENAI_API_KEY=your_openai_api_key" > .env
    echo "LUMALABS_API_KEY=your_lumalabs_api_key" >> .env
    
    # Add server configuration
    echo "" >> .env
    echo "# Server configuration" >> .env
    echo "PORT=5010" >> .env
    echo "HOST=0.0.0.0" >> .env
    
    # Add TEST_MODE flag - set to true by default on non-Raspberry Pi devices
    if [ "$(uname -m)" = "armv7l" ] || [ "$(uname -m)" = "aarch64" ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        echo "TEST_MODE=false" >> .env
        echo "ENABLE_GPIO=true" >> .env
    else
        echo "TEST_MODE=true  # Set to false on Raspberry Pi" >> .env
        echo "ENABLE_GPIO=false  # Set to true on Raspberry Pi" >> .env
    fi
    
    echo "⚠️ Please edit .env file with your actual API keys before running the application."
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/audio data/videos data/processed_videos

# Build the frontend
echo "🏗️ Building frontend..."
cd frontend
npm run build || echo "⚠️ Frontend build failed, but we'll continue setup"
cd ..

echo "✅ Setup complete! You can now run the application with './run.sh'"
echo "✳️ Note: If you encountered any errors, you might need to fix them manually before running the application."
echo "🎤 If you need to install PyAudio, you can run: ./scripts/install_pyaudio.sh" 