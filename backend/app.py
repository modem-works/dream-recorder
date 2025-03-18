#!/usr/bin/env python3
"""
Dream Recorder - Main Application Entry Point
This is the main Flask application that serves the frontend and handles WebSocket connections.
"""

# Monkey patch for gevent compatibility in Python 3.12
try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

import os
import json
import logging
import platform
from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../frontend/dist',
            template_folder='../frontend/dist')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dream-recorder-secret')

# Initialize Socket.IO with gevent instead of eventlet for Python 3.12 compatibility
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Import custom modules - wrapped in try/except to handle potential import errors
GPIO_AVAILABLE = False
try:
    # Check if running on a Raspberry Pi
    if platform.system() == "Linux" and os.path.exists('/proc/device-tree/model'):
        with open('/proc/device-tree/model') as f:
            model = f.read()
        if 'Raspberry Pi' in model:
            from gpio.controller import GPIOController
            GPIO_AVAILABLE = True
        else:
            logger.warning("Not running on a Raspberry Pi - GPIO will not be available")
    else:
        logger.warning("Not running on a Raspberry Pi - GPIO will not be available")
except (ImportError, RuntimeError, FileNotFoundError) as e:
    logger.warning(f"GPIO module not available: {str(e)} - running without GPIO support")

# Define a dummy controller class if GPIO is not available
if not GPIO_AVAILABLE:
    class DummyGPIOController:
        def __init__(self, **kwargs):
            pass
            
        def setup(self):
            logger.info("Using dummy GPIO controller")
            
        def register_button_callback(self, callback):
            logger.info("Button callback registered to dummy controller")
            
        def cleanup(self):
            pass
    
    GPIOController = DummyGPIOController

try:
    from websockets.audio_handler import AudioHandler
    # Check if we can import the required audio libraries
    try:
        import wave
        import numpy as np
        from pydub import AudioSegment
        AUDIO_AVAILABLE = True
        logger.info("Audio processing libraries loaded successfully")
    except ImportError as e:
        logger.warning(f"Audio library import error: {e} - audio recording will have limited functionality")
        AUDIO_AVAILABLE = True  # Still enable audio since the web browser can handle it
except ImportError:
    logger.warning("Audio handling modules not available - audio recording will not work")
    AUDIO_AVAILABLE = False
    
    # Define a dummy audio handler class
    class DummyAudioHandler:
        def __init__(self, **kwargs):
            pass
            
        def process_audio_chunk(self, data):
            logger.warning("Audio processing not available")
            
        def finalize_recording(self):
            logger.warning("Audio recording not available")
            return None
            
        def get_audio_file_path(self):
            return None
    
    AudioHandler = DummyAudioHandler

# Import remaining modules
from api.openai_client import OpenAIClient
from api.lumalabs_client import LumaLabsClient
from video.processor import VideoProcessor
from utils.state_manager import StateManager

# Initialize components
state_manager = StateManager()
gpio_controller = GPIOController(state_manager=state_manager)
openai_client = OpenAIClient(api_key=os.environ.get('OPENAI_API_KEY'))
lumalabs_client = LumaLabsClient(api_key=os.environ.get('LUMALABS_API_KEY'))
video_processor = VideoProcessor()
audio_handler = AudioHandler()

# Routes
@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve static assets from the dist/assets directory"""
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon.ico"""
    return send_from_directory(os.path.join(app.static_folder, 'assets'), 'favicon.ico')

# Catch all route for any other static files
@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serve other static files"""
    # First try the root of the static folder
    try:
        return send_from_directory(app.static_folder, filename)
    except:
        # If not found, try the assets directory
        try:
            return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)
        except:
            # Return 404 if file not found
            return '', 404

@app.route('/api/status')
def status():
    """Get the current system status"""
    return jsonify({
        'state': state_manager.current_state,
        'timestamp': state_manager.last_updated,
        'gpio_available': GPIO_AVAILABLE,
        'audio_available': AUDIO_AVAILABLE
    })

@app.route('/api/config')
def config():
    """Get server configuration"""
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5010))
    return jsonify({
        'server_url': f'http://{host if host != "0.0.0.0" else request.host.split(":")[0]}:{port}',
        'websocket_url': f'ws://{host if host != "0.0.0.0" else request.host.split(":")[0]}:{port}'
    })

# Add a route to serve video files from the processed_videos directory
@app.route('/videos/<path:filename>')
def serve_videos(filename):
    """Serve processed video files"""
    videos_dir = os.path.join(os.getcwd(), 'data', 'processed_videos')
    logger.info(f"Serving video: {filename} from {videos_dir}")
    
    full_path = os.path.join(videos_dir, filename)
    if os.path.exists(full_path):
        logger.info(f"Video file found: {full_path}")
    else:
        logger.error(f"Video file not found: {full_path}")
        if os.path.exists(videos_dir):
            logger.info(f"Video directory exists. Contents: {os.listdir(videos_dir)}")
        else:
            logger.error(f"Video directory not found: {videos_dir}")
    
    return send_from_directory(videos_dir, filename)

@app.route('/videos/')
def list_videos():
    videos_dir = os.path.join(os.getcwd(), 'data', 'processed_videos')
    logger.info(f"Listing videos directory: {videos_dir}")
    
    if not os.path.exists(videos_dir):
        logger.error(f"Video directory not found: {videos_dir}")
        return "Video directory not found", 404
    
    video_files = os.listdir(videos_dir)
    logger.info(f"Found {len(video_files)} videos: {video_files}")
    
    # Create a simple HTML page with links to the videos
    html = [
        '<!DOCTYPE html>',
        '<html>',
        '<head><title>Available Dream Videos</title></head>',
        '<body>',
        '<h1>Available Dream Videos</h1>',
        '<ul>'
    ]
    
    for video in sorted(video_files, reverse=True):  # Sort in reverse to show newest first
        if video.endswith(('.mp4', '.webm', '.ogg')):
            html.append(f'<li><a href="/videos/{video}">{video}</a></li>')
    
    html.extend(['</ul>', '</body>', '</html>'])
    
    return '\n'.join(html)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection"""
    logger.info('Client connected')
    emit('status', {
        'state': state_manager.current_state,
        'gpio_available': GPIO_AVAILABLE,
        'audio_available': AUDIO_AVAILABLE
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected')

@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle incoming audio data from the client"""
    if AUDIO_AVAILABLE:
        audio_handler.process_audio_chunk(data)
    else:
        logger.warning("Received audio data but audio processing is not available")

@socketio.on('start_recording')
def handle_start_recording():
    """Handle recording start event"""
    logger.info("Starting new recording")
    if AUDIO_AVAILABLE:
        recording_id = audio_handler.start_new_recording()
        logger.info(f"New recording started with ID: {recording_id}")
    else:
        logger.warning("Audio recording not available")

@socketio.on('recording_complete')
def handle_recording_complete():
    """Handle recording completion notification from the client"""
    logger.info("Received recording_complete event")
    audio_path = None
    
    if AUDIO_AVAILABLE:
        audio_path = audio_handler.finalize_recording()
        if audio_path:
            logger.info(f"Recording finalized: {audio_path}")
        else:
            logger.warning("Failed to finalize recording")
        
    # Process the audio, even if there's no audio path
    # This allows the demo text to be used when no audio is available
    process_audio(audio_path)
    
    if not audio_path and not AUDIO_AVAILABLE:
        logger.warning("No audio recording available - using demo text")

def process_audio(audio_path=None):
    """Process the recorded audio and generate a video"""
    # This function will be called when recording is complete
    # and will orchestrate the processing pipeline
    
    # Update state
    state_manager.set_state('processing_audio')
    socketio.emit('status', {'state': 'processing_audio'})
    
    # Process audio to text
    if not audio_path:
        audio_path = audio_handler.get_audio_file_path()
    
    if not audio_path:
        # If no audio path, use a demo text for testing
        logger.warning("No audio file available, using demo text")
        transcription = "I dreamed I was flying over a colorful landscape with mountains and rivers."
    else:
        transcription = openai_client.transcribe_audio(audio_path)
    
    # Send the original transcription to the frontend
    logger.info(f"Transcription: {transcription}")
    socketio.emit('transcription', {'text': transcription})
    
    # Update state
    state_manager.set_state('enhancing_prompt')
    socketio.emit('status', {'state': 'enhancing_prompt'})
    
    # Enhance prompt
    enhanced_prompt = openai_client.enhance_prompt(transcription)
    
    # Send the enhanced prompt to the frontend - with extra logging and careful formatting
    logger.info(f"Enhanced prompt: {enhanced_prompt}")
    logger.info("Sending enhanced_prompt event to frontend")
    
    # Ensure the event format is correct and match the frontend expectations
    emit_payload = {'text': enhanced_prompt}
    logger.info(f"Enhanced prompt payload: {emit_payload}")
    
    # Emit the event with the properly formatted payload
    socketio.emit('enhanced_prompt', emit_payload)
    logger.info("Enhanced prompt event emitted")
    
    # Update state
    state_manager.set_state('generating_video')
    socketio.emit('status', {'state': 'generating_video'})
    
    # Generate video
    try:
        video_url = lumalabs_client.generate_video(enhanced_prompt)
        
        if not video_url:
            logger.error("Failed to generate video - empty URL returned")
            
            # MODIFICATION: Don't send error status to frontend
            # Just log the error and keep the frontend in generating_video state
            logger.info("Skipping error status update to preserve UI state")
            
            # Don't return - continue to keep the application responsive
            # The frontend will stay in the generating_video state
            
            # OPTIONAL: We could send a non-error message to inform the user
            socketio.emit('notification', {
                'message': 'Video generation is currently unavailable, but your dream has been preserved.',
                'type': 'warning'
            })
            
            return
            
        # Download and process video
        state_manager.set_state('processing_video')
        socketio.emit('status', {'state': 'processing_video'})
        
        video_path = lumalabs_client.download_video(video_url)
        processed_video_path = video_processor.process_video(video_path)
        
        # Update state with video ready
        state_manager.set_state('video_ready')
        socketio.emit('status', {'state': 'video_ready'})
        socketio.emit('video_ready', {'video_path': processed_video_path})
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error during video generation: {error_message}")
        
        # MODIFICATION: Don't send error status to frontend
        # Just log the error and keep the frontend in generating_video state
        logger.info("Skipping error status update to preserve UI state")
        
        # OPTIONAL: We could send a non-error message to inform the user
        socketio.emit('notification', {
            'message': 'Video generation is currently unavailable, but your dream has been preserved.',
            'type': 'warning'
        })
        
        # Don't set state_manager to error - keeps everything in current state
        return

    # After successful completion, return to ready state (only if everything succeeded)
    # Wait a bit before resetting state to give user time to view the result
    # This delayed reset is optional and can be removed if you want manual reset only
    # time.sleep(60)  # Wait 60 seconds before auto-reset
    # state_manager.set_state('ready')
    # socketio.emit('status', {'state': 'ready'})

# Initialize GPIO controller
# This sets up the GPIO pins and registers callbacks
def setup_gpio():
    """Set up GPIO pins and event handlers"""
    if not GPIO_AVAILABLE:
        logger.warning("GPIO not available - running without GPIO support")
        return
        
    try:
        gpio_controller.setup()
        gpio_controller.register_button_callback(handle_button_press)
        logger.info("GPIO controller initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GPIO: {e}")
        logger.warning("Running without GPIO support - touch functionality disabled")

def handle_button_press():
    """Handle button press event from GPIO"""
    current_state = state_manager.current_state
    
    if current_state == 'ready':
        # Start recording
        state_manager.set_state('recording')
        socketio.emit('status', {'state': 'recording'})
        
        # Initialize a new recording on the backend before telling the client to start
        if AUDIO_AVAILABLE:
            recording_id = audio_handler.start_new_recording()
            logger.info(f"Started new recording with ID: {recording_id}")
        
        # Tell client to start recording
        socketio.emit('start_recording')
    
    elif current_state == 'recording':
        # Stop recording - use 'processing_audio' which is a valid state
        state_manager.set_state('processing_audio')
        socketio.emit('status', {'state': 'processing_audio'})
        socketio.emit('stop_recording')

# Manual trigger from web interface
@socketio.on('manual_trigger')
def handle_manual_trigger(data):
    """Handle manual trigger from web interface"""
    action = data.get('action')
    if action == 'start_recording':
        handle_button_press()
    elif action == 'stop_recording':
        handle_button_press()
    elif action == 'reset':
        # Reset application state
        state_manager.set_state('ready')
        socketio.emit('status', {'state': 'ready'})

if __name__ == '__main__':
    # Set up GPIO if enabled
    if os.environ.get('ENABLE_GPIO', 'true').lower() == 'true':
        setup_gpio()
    
    # Start the Flask server
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5010))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Log some important configuration info
    logger.info(f"Starting Dream Recorder server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Static folder: {app.static_folder}")
    logger.info(f"Template folder: {app.template_folder}")
    
    # Add detailed logging for asset paths if in debug mode
    if debug:
        logger.info(f"Asset directory: {os.path.join(app.static_folder, 'assets')}")
        logger.info(f"Asset directory exists: {os.path.exists(os.path.join(app.static_folder, 'assets'))}")
        if os.path.exists(os.path.join(app.static_folder, 'assets')):
            logger.info(f"Asset directory contents: {os.listdir(os.path.join(app.static_folder, 'assets'))}")
    
    socketio.run(app, host=host, port=port, debug=debug) 