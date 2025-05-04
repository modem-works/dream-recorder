# =============================
# Imports & Initial Setup
# =============================
from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import os
import logging
import gevent
import io
from openai import OpenAI
import argparse
from dream_db import DreamDB
from functions.audio import create_wav_file, process_audio
from config_loader import load_config

# =============================
# Load Configuration
# =============================
config = load_config()

# Configure logging
logging.basicConfig(level=getattr(logging, config["LOG_LEVEL"]))
logger = logging.getLogger(__name__)

# =============================
# Global Variables & Constants
# =============================

# Global state for recording
recording_state = {
    'is_recording': False,
    'status': 'ready',  # ready, recording, processing, generating, complete
    'transcription': '',
    'video_prompt': '',
    'video_url': None
}

# Video playback state
video_playback_state = {
    'current_index': 0,  # Index of the current video being played
    'is_playing': False  # Whether a video is currently playing
}

# Audio buffer for storing chunks
audio_buffer = io.BytesIO()
wav_file = None

# List to store incoming audio chunks
audio_chunks = []

# =============================
# Flask App & Extensions Initialization
# =============================

# Initialize Flask app
app = Flask(__name__)
app.config.update(
    DEBUG=os.environ.get("FLASK_ENV", "production") == "development",
    HOST=config["HOST"],
    PORT=int(config["PORT"])
)

# Initialize OpenAI client
client = OpenAI(
    api_key=config["OPENAI_API_KEY"],
    http_client=None
)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Initialize DreamDB
dream_db = DreamDB()

# =============================
# Core Logic / Helper Functions
# =============================

def initiate_recording():
    """Handles the common state changes and buffer resets for starting recording."""
    global audio_buffer, wav_file, audio_chunks
    recording_state['is_recording'] = True
    recording_state['status'] = 'recording'
    recording_state['transcription'] = '' # Reset transcription
    recording_state['video_prompt'] = ''  # Reset video prompt
    # Reset audio storage
    audio_buffer = io.BytesIO() 
    audio_chunks = []
    wav_file = None # Ensure wav_file is reset before creating a new one
    wav_file = create_wav_file(audio_buffer)
    if logger:
        logger.debug("Initiated recording: state set, buffers reset, wav file created.")

# =============================
# SocketIO Event Handlers
# =============================

@socketio.on('connect')
def handle_connect():
    """Handle new client connection."""
    if logger:
        logger.info('Client connected')
    emit('state_update', recording_state)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    if logger:
        logger.info('Client disconnected')

@socketio.on('start_recording')
def handle_start_recording():
    """Socket event to start recording."""
    if not recording_state['is_recording']:
        initiate_recording()
        emit('state_update', recording_state)
        if logger:
            logger.info('Started recording via socket event')
    else:
        if logger:
            logger.warning('Start recording event received, but already recording.')

@socketio.on('stream_recording')
def handle_audio_data(data):
    """Handle incoming audio data chunks from the client during recording."""
    if recording_state['is_recording']:
        try:
            # Convert the received data to bytes
            audio_bytes = bytes(data['data'])
            # Store the chunk
            audio_chunks.append(audio_bytes)
        except Exception as e:
            if logger:
                logger.error(f"Error handling audio data: {str(e)}")
            emit('error', {'message': f"Error handling audio data: {str(e)}"})

@socketio.on('stop_recording')
def handle_stop_recording():
    """Socket event to stop recording and trigger processing."""
    if recording_state['is_recording']:
        sid = request.sid # Get SID before changing state

        # Finalize the recording
        recording_state['is_recording'] = False
        recording_state['status'] = 'processing'
        if logger:
            logger.info(f"Finalizing recording. Status set to processing. Triggering process_audio for SID: {sid}")

        # Process the audio in a background task, passing all required arguments
        gevent.spawn(
            process_audio, sid, client, socketio, dream_db, recording_state, audio_chunks, logger
        )

        # Emit the comprehensive state update after finalizing
        emit('state_update', recording_state)
        if logger:
            logger.info('Stopped recording via socket event.')
    else:
        if logger:
            logger.warning('Stop recording event received, but not currently recording.')

@socketio.on('show_previous_dream')
def handle_show_previous_dream():
    """Socket event handler for showing previous dream."""
    try:
        # Get the most recent dreams
        dreams = dream_db.get_all_dreams()
        if not dreams:
            if logger:
                logger.warning("No dreams found to cycle through.")
            return None
        # If we're currently playing a video, show the next one in sequence
        if video_playback_state['is_playing']:
            video_playback_state['current_index'] += 1
            if video_playback_state['current_index'] >= len(dreams):
                video_playback_state['current_index'] = 0  # Wrap around
        else:
            # If not playing, start with the most recent dream
            video_playback_state['current_index'] = 0
            video_playback_state['is_playing'] = True
        # Get the dream at the current index
        dream = dreams[video_playback_state['current_index']]
        # Emit the video URL to the client
        socketio.emit('play_video', {
            'video_url': f"/media/video/{dream['video_filename']}",
            'loop': True  # Enable looping for the video
        })
        if logger:
            logger.info(f"Emitted play_video for dream index {video_playback_state['current_index']}: {dream['video_filename']}")

        if not dream:
            socketio.emit('error', {'message': 'No dreams found'})
    except Exception as e:
        if logger:
            logger.error(f"Error in socket handle_show_previous_dream: {str(e)}")
        socketio.emit('error', {'message': str(e)})

# =============================
# Flask Route Handlers
# =============================

# -- Page Routes --
@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html', 
                         is_development=app.config['DEBUG'],
                         total_background_images=int(config["TOTAL_BACKGROUND_IMAGES"]))

@app.route('/dreams')
def dreams():
    """Display the dreams library page."""
    dreams = dream_db.get_all_dreams()
    return render_template('dreams.html', dreams=dreams)

# -- API Routes --
@app.route('/api/config')
def get_config():
    """Get application configuration for the frontend."""
    return jsonify({
        'is_development': app.config['DEBUG'],
        'playback_duration': int(config['PLAYBACK_DURATION']),
        'logo_fade_in_duration': int(config['LOGO_FADE_IN_DURATION']),
        'logo_fade_out_duration': int(config['LOGO_FADE_OUT_DURATION']),
        'clock_fade_in_duration': int(config['CLOCK_FADE_IN_DURATION']),
        'clock_fade_out_duration': int(config['CLOCK_FADE_OUT_DURATION']),
        'transition_delay': int(config['TRANSITION_DELAY'])
    })

@app.route('/api/gpio_single_tap', methods=['POST'])
def gpio_single_tap():
    """API endpoint for single tap from GPIO controller."""
    try:
        # Notify all clients of a single tap event
        socketio.emit('device_event', {'eventType': 'single_tap'})
        return jsonify({'status': 'success'})
    except Exception as e:
        if logger:
            logger.error(f"Error in API gpio_single_tap: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/gpio_double_tap', methods=['POST'])
def gpio_double_tap():
    """API endpoint for double tap from GPIO controller."""
    try:
        # Notify all clients of a double tap event
        socketio.emit('device_event', {'eventType': 'double_tap'})
        return jsonify({'status': 'success'})
    except Exception as e:
        if logger:
            logger.error(f"Error in API gpio_double_tap: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/dreams/<int:dream_id>', methods=['DELETE'])
def delete_dream(dream_id):
    """Delete a dream and its associated files."""
    try:
        # Get the dream details before deletion
        dream = dream_db.get_dream(dream_id)
        if not dream:
            return jsonify({'success': False, 'message': 'Dream not found'}), 404
        # Delete the dream from the database
        if dream_db.delete_dream(dream_id):
            # Delete associated files
            try:
                # Delete video file
                video_path = os.path.join(config['VIDEOS_DIR'], dream['video_filename'])
                if os.path.exists(video_path):
                    os.remove(video_path)
                # Delete thumbnail file
                thumb_path = os.path.join(config['THUMBS_DIR'], dream['thumb_filename'])
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                # Delete audio file
                audio_path = os.path.join(config['RECORDINGS_DIR'], dream['audio_filename'])
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception as e:
                if logger:
                    logger.error(f"Error deleting files for dream {dream_id}: {str(e)}")
                # Continue even if file deletion fails
            return jsonify({'success': True, 'message': 'Dream deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete dream'}), 500
    except Exception as e:
        if logger:
            logger.error(f"Error deleting dream {dream_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clock-config-path')
def clock_config_path():
    """Return the clock configuration path from config."""
    config_path = config['CLOCK_CONFIG_PATH']
    if not config_path:
        return jsonify({'error': 'CLOCK_CONFIG_PATH not set in config'}), 500
    return jsonify({'configPath': config_path})

# -- Media Routes --
@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serve media files (audio and video) from the media directory."""
    try:
        return send_file(os.path.join('media', filename))
    except FileNotFoundError:
        return "File not found", 404

@app.route('/media/thumbs/<path:filename>')
def serve_thumbnail(filename):
    """Serve thumbnail files from the thumbs directory."""
    try:
        return send_file(os.path.join(config['THUMBS_DIR'], filename))
    except FileNotFoundError:
        return "Thumbnail not found", 404

# =============================
# Main Execution Block
# =============================

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--reload', action='store_true', help='Enable auto-reloader')
    args = parser.parse_args()
    # Start the Flask-SocketIO server
    socketio.run(
        app, 
        host=app.config['HOST'], 
        port=app.config['PORT'], 
        debug=app.config['DEBUG'],
        use_reloader=args.reload
    ) 