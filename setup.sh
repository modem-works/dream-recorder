#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/audio data/videos

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
OPENAI_API_KEY="your-openai-api-key"
LUMALABS_API_KEY="your-lumalabs-api-key"
PORT=5010
HOST=0.0.0.0
FLASK_ENV=development
EOL
    echo "Please update the .env file with your API keys"
fi

echo "Setup complete! To run the application:"
echo "1. Update the .env file with your API keys"
echo "2. Run: source venv/bin/activate && python app.py"
echo "3. Open http://localhost:5010 in your browser" 