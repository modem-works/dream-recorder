from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import os
import logging
import gevent
import tempfile
import wave
import io
from openai import OpenAI
import numpy as np
from datetime import datetime
import requests
import time
from dotenv import load_dotenv
import argparse
from scripts.env_check import check_required_env_vars
from dream_db import DreamDB
from pydub import AudioSegment
import ffmpeg

# Load environment variables and check they're all set
load_dotenv()
check_required_env_vars()

# Configure logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL')))
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.update(
    DEBUG=os.getenv('FLASK_ENV') == 'development',
    HOST=os.getenv('HOST'),
    PORT=int(os.getenv('PORT').split('#')[0].strip())  # Strip any comments from the value
)

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    http_client=None  # This prevents the client from creating its own HTTP client
)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Global state
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
audio_chunks = []

# Initialize DreamDB
dream_db = DreamDB()

def create_wav_file():
    global wav_file
    wav_file = wave.open(audio_buffer, 'wb')
    wav_file.setnchannels(int(os.getenv('AUDIO_CHANNELS')))
    wav_file.setsampwidth(int(os.getenv('AUDIO_SAMPLE_WIDTH')))
    wav_file.setframerate(int(os.getenv('AUDIO_FRAME_RATE')))

def save_wav_file(audio_data, filename=None):
    """Save the WAV file locally for debugging."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
    
    # Ensure the recordings directory exists
    os.makedirs(os.getenv('RECORDINGS_DIR'), exist_ok=True)
    filepath = os.path.join(os.getenv('RECORDINGS_DIR'), filename)
    
    # Create a temporary file for the WebM data
    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_webm:
        temp_webm.write(audio_data)
        temp_webm_path = temp_webm.name
    
    try:
        # Convert WebM to WAV using ffmpeg
        stream = ffmpeg.input(temp_webm_path)
        stream = ffmpeg.output(stream, filepath, acodec='pcm_s16le', ac=1, ar=44100)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        logger.info(f"Saved WAV file to {filepath}")
        return filename  # Return only the filename
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_webm_path)
        except:
            pass

def generate_video_prompt(transcription, luma_extend=False):
    """Generate an enhanced video prompt from the transcription using GPT."""
    try:
        system_prompt = os.getenv('GPT_SYSTEM_PROMPT_EXTEND') if luma_extend else os.getenv('GPT_SYSTEM_PROMPT')
        response = client.chat.completions.create(
            model=os.getenv('GPT_MODEL'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{transcription}"}
            ],
            temperature=float(os.getenv('GPT_TEMPERATURE')),
            max_tokens=int(os.getenv('GPT_MAX_TOKENS'))
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating video prompt: {str(e)}")
        return None

def process_video(input_path):
    """Process the video using FFmpeg with specific filters."""
    try:
        # Create a temporary file for the processed video
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name

        # Apply FFmpeg filters using environment variables
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.filter(stream, 'eq', brightness=float(os.getenv('FFMPEG_BRIGHTNESS')))
        stream = ffmpeg.filter(stream, 'vibrance', intensity=float(os.getenv('FFMPEG_VIBRANCE')))
        stream = ffmpeg.filter(stream, 'vaguedenoiser', threshold=float(os.getenv('FFMPEG_DENOISE_THRESHOLD')))
        stream = ffmpeg.filter(stream, 'bilateral', sigmaS=float(os.getenv('FFMPEG_BILATERAL_SIGMA')))
        stream = ffmpeg.filter(stream, 'noise', all_strength=float(os.getenv('FFMPEG_NOISE_STRENGTH')))
        stream = ffmpeg.output(stream, temp_path)
        
        # Run FFmpeg
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        # Replace the original file with the processed one
        os.replace(temp_path, input_path)
        
        logger.info(f"Processed video saved to {input_path}")
        return input_path
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise

def process_thumbnail(video_path):
    """Create a square thumbnail from the video at 1 second in."""
    try:
        # Get video dimensions using ffprobe
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        width = int(video_info['width'])
        height = int(video_info['height'])
        
        # Calculate square crop dimensions based on the smaller dimension
        crop_size = min(width, height)
        
        # Calculate offsets to center the crop
        x_offset = (width - crop_size) // 2
        y_offset = (height - crop_size) // 2
        
        # Create output directory if it doesn't exist
        thumbs_dir = os.getenv('THUMBS_DIR')
        os.makedirs(thumbs_dir, exist_ok=True)
        
        # Generate simple timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        thumb_filename = f"thumb_{timestamp}.png"
        thumb_path = os.path.join(thumbs_dir, thumb_filename)
        
        # Log the FFmpeg command for debugging
        logger.info(f"Generating thumbnail for video: {video_path}")
        logger.info(f"Video dimensions: {width}x{height}")
        logger.info(f"Output path: {thumb_path}")
        logger.info(f"Crop dimensions: {crop_size}x{crop_size} at offset ({x_offset}, {y_offset})")
        
        # Use FFmpeg to extract frame at 1 second and crop to square
        stream = ffmpeg.input(video_path, ss=1)  # Seek to 1 second
        stream = ffmpeg.filter(stream, 'crop', crop_size, crop_size, x_offset, y_offset)
        stream = ffmpeg.output(stream, thumb_path, vframes=1)  # Only extract one frame
        
        # Run FFmpeg with stderr capture
        try:
            ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
        
        logger.info(f"Generated thumbnail saved to {thumb_path}")
        return thumb_filename
        
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        raise

def generate_video(prompt, filename=None, luma_extend=False):
    """Generate a video using Luma Labs API, with optional extension if LUMA_EXTEND is set."""
    try:
        # If luma_extend, split the prompt into two parts
        if luma_extend and '*****' in prompt:
            initial_prompt, extension_prompt = [p.strip() for p in prompt.split('*****', 1)]
        else:
            initial_prompt = prompt
            extension_prompt = 'Continue on with this video'  # fallback
        # Step 1: Create the initial generation request
        response = requests.post(
            os.getenv('LUMA_GENERATIONS_ENDPOINT'),
            headers={
                'accept': 'application/json',
                'authorization': f'Bearer {os.getenv("LUMALABS_API_KEY")}',
                'content-type': 'application/json'
            },
            json={
                'prompt': initial_prompt,
                'model': os.getenv('LUMA_MODEL'),
                'resolution': os.getenv('LUMA_RESOLUTION'),
                'duration': os.getenv('LUMA_DURATION'),
                "aspect_ratio": os.getenv('LUMA_ASPECT_RATIO'),
            }
        )
        if response.status_code not in [200, 201]:
            raise Exception(f"Luma API error: {response.text}")
        response_data = response.json()
        logger.info(f"API response: {response_data}")
        generation_id = response_data.get('id')
        if not generation_id:
            raise Exception("Failed to get generation ID from response")
        logger.info(f"Started video generation with ID: {generation_id}")
        def poll_for_completion(generation_id):
            max_attempts = int(os.getenv('LUMA_MAX_POLL_ATTEMPTS'))
            poll_interval = float(os.getenv('LUMA_POLL_INTERVAL'))
            for attempt in range(max_attempts):
                status_response = requests.get(
                    f'{os.getenv("LUMA_API_URL")}/generations/{generation_id}',
                    headers={
                        'accept': 'application/json',
                        'authorization': f'Bearer {os.getenv("LUMALABS_API_KEY")}'
                    }
                )
                if status_response.status_code not in [200, 201]:
                    logger.error(f"Status check failed with code {status_response.status_code}: {status_response.text}")
                    time.sleep(poll_interval)
                    continue
                status_data = status_response.json()
                if attempt == 0 or attempt % 10 == 0:
                    logger.info(f"Full status response: {status_data}")
                state = status_data.get('state')
                logger.info(f"Generation state: {state} (attempt {attempt+1}/{max_attempts})")
                if state in ['completed', 'succeeded']:
                    assets = status_data.get('assets') or {}
                    video_url = None
                    if isinstance(assets, dict):
                        video_url = (assets.get('video') or 
                                   assets.get('url') or 
                                   (assets.get('videos', {}) or {}).get('url'))
                    if not video_url and 'result' in status_data:
                        result = status_data.get('result', {})
                        if isinstance(result, dict):
                            video_url = result.get('url')
                    if not video_url:
                        raise Exception("Video URL not found in completed response")
                    logger.info(f"Video generation completed: {video_url}")
                    return video_url
                elif state in ['failed', 'error']:
                    error_msg = status_data.get('failure_reason') or status_data.get('error') or "Unknown error"
                    raise Exception(f"Video generation failed: {error_msg}")
                time.sleep(poll_interval)
            raise Exception(f"Timed out waiting for video generation after {max_attempts} attempts")
        # Step 2: If luma_extend is set, extend the video
        if luma_extend:
            logger.info("LUMA_EXTEND is set. Requesting video extension.")
            _ = poll_for_completion(generation_id)  # Wait for completion
            extend_response = requests.post(
                os.getenv('LUMA_GENERATIONS_ENDPOINT'),
                headers={
                    'accept': 'application/json',
                    'authorization': f'Bearer {os.getenv("LUMALABS_API_KEY")}',
                    'content-type': 'application/json'
                },
                json={
                    'prompt': extension_prompt,
                    'keyframes': {
                        'frame0': {
                            'type': 'generation',
                            'id': generation_id
                        }
                    }
                }
            )
            if extend_response.status_code not in [200, 201]:
                raise Exception(f"Luma API error (extend): {extend_response.text}")
            extend_data = extend_response.json()
            logger.info(f"Extend API response: {extend_data}")
            extend_id = extend_data.get('id')
            if not extend_id:
                raise Exception("Failed to get extend generation ID from response")
            logger.info(f"Started video extension with ID: {extend_id}")
            video_url = poll_for_completion(extend_id)
        else:
            video_url = poll_for_completion(generation_id)
        video_response = requests.get(video_url, stream=True)
        video_response.raise_for_status()
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.mp4"
        os.makedirs(os.getenv('VIDEOS_DIR'), exist_ok=True)
        video_path = os.path.join(os.getenv('VIDEOS_DIR'), filename)
        with open(video_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Saved video to {video_path}")
        processed_video_path = process_video(video_path)
        logger.info(f"Processed video saved to {processed_video_path}")
        thumb_filename = process_thumbnail(processed_video_path)
        return filename, thumb_filename
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        raise

def process_audio(sid):
    """Process the recorded audio and generate video."""
    try:
        global recording_state, audio_buffer, wav_file, audio_chunks
        # Save the WAV file
        audio_data = b''.join(audio_chunks)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_filename = f"recording_{timestamp}.wav"
        wav_filename = save_wav_file(audio_data, wav_filename)
        # Get duration of the audio
        wav_path = os.path.join(os.getenv('RECORDINGS_DIR'), wav_filename)
        with wave.open(wav_path, 'rb') as wf:
            duration = wf.getnframes() / wf.getframerate()
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        # Transcribe the audio using OpenAI's Whisper API
        with open(temp_file_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model=os.getenv('WHISPER_MODEL'),
                file=audio_file
            )
        # Update the transcription in the global state
        recording_state['transcription'] = transcription.text
        # Emit the transcription
        if sid:
            socketio.emit('transcription_update', {'text': transcription.text}, room=sid)
        else:
            socketio.emit('transcription_update', {'text': transcription.text})
        # Check if LUMA_EXTEND is set
        luma_extend = os.getenv('LUMA_EXTEND', 'False').lower() in ('1', 'true', 'yes')
        # Generate video prompt
        video_prompt = generate_video_prompt(transcription.text, luma_extend=luma_extend)
        if not video_prompt:
            raise Exception("Failed to generate video prompt")
        recording_state['video_prompt'] = video_prompt
        if sid:
            socketio.emit('video_prompt_update', {'text': video_prompt}, room=sid)
        else:
            socketio.emit('video_prompt_update', {'text': video_prompt})
        # Generate video and get the processed video path and thumbnail filename
        video_filename, thumb_filename = generate_video(video_prompt, luma_extend=luma_extend)
        # Save to database
        dream_data = {
            'user_prompt': recording_state['transcription'],
            'generated_prompt': recording_state['video_prompt'],
            'audio_filename': wav_filename,
            'video_filename': video_filename,
            'thumb_filename': thumb_filename,
            'duration': int(duration),
            'status': 'completed',
            'metadata': {
                'sid': sid,
                'timestamp': timestamp
            }
        }
        dream_db.save_dream(dream_data)
        recording_state['status'] = 'complete'
        recording_state['video_url'] = f"/media/video/{video_filename}"
        # Emit the video ready event to trigger playback
        if sid:
            socketio.emit('video_ready', {'url': recording_state['video_url']}, room=sid)
        else:
            socketio.emit('video_ready', {'url': recording_state['video_url']})
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        recording_state['status'] = 'error'
        socketio.emit('error', {'message': str(e)})
    finally:
        # Clean up
        audio_buffer = io.BytesIO()
        audio_chunks = []
        wav_file = None
        # Remove temporary file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass

@socketio.on('audio_data')
def handle_audio_data(data):
    if recording_state['is_recording']:
        try:
            # Convert the received data to bytes
            audio_bytes = bytes(data['data'])
            # Store the chunk
            audio_chunks.append(audio_bytes)
        except Exception as e:
            logger.error(f"Error handling audio data: {str(e)}")
            emit('error', {'message': f"Error handling audio data: {str(e)}"})

@app.route('/')
def index():
    return render_template('index.html', 
                         is_development=app.config['DEBUG'],
                         total_background_images=int(os.getenv('TOTAL_BACKGROUND_IMAGES', 1119)))

@app.route('/api/config')
def get_config():
    """Get application configuration"""
    return jsonify({
        'is_development': app.config['DEBUG'],
        'playback_duration': int(os.getenv('PLAYBACK_DURATION')),
        'logo_fade_in_duration': int(os.getenv('LOGO_FADE_IN_DURATION')),
        'logo_fade_out_duration': int(os.getenv('LOGO_FADE_OUT_DURATION')),
        'clock_fade_in_duration': int(os.getenv('CLOCK_FADE_IN_DURATION')),
        'clock_fade_out_duration': int(os.getenv('CLOCK_FADE_OUT_DURATION')),
        'transition_delay': int(os.getenv('TRANSITION_DELAY'))
    })

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('state_update', recording_state)

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('start_recording')
def handle_start_recording():
    if not recording_state['is_recording']:
        recording_state['is_recording'] = True
        recording_state['status'] = 'recording'
        recording_state['transcription'] = ''
        recording_state['video_prompt'] = ''
        emit('state_update', recording_state)
        logger.info('Started recording')
        # Initialize WAV file
        create_wav_file()
        # Clear any previous audio chunks
        audio_chunks.clear()

@socketio.on('stop_recording')
def handle_stop_recording():
    if recording_state['is_recording']:
        recording_state['is_recording'] = False
        recording_state['status'] = 'processing'
        emit('state_update', recording_state)
        logger.info('Stopped recording')
        
        # Get the current session ID
        sid = request.sid
        
        # Process the audio in a background task
        gevent.spawn(process_audio, sid)

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
        return send_file(os.path.join(os.getenv('THUMBS_DIR'), filename))
    except FileNotFoundError:
        return "Thumbnail not found", 404

@app.route('/api/trigger_recording', methods=['POST'])
def trigger_recording():
    """API endpoint to trigger recording from GPIO controller (double tap)."""
    try:
        if recording_state['status'] == 'ready':
            # Start recording
            recording_state['is_recording'] = True
            recording_state['status'] = 'recording'
            
            # Reset the audio buffer
            global audio_buffer, wav_file, audio_chunks
            audio_buffer = io.BytesIO()
            audio_chunks = []
            create_wav_file()
            
            # Broadcast the recording state change to all clients
            socketio.emit('recording_state', {'status': 'recording'})
            logger.info("Recording triggered via GPIO double tap")
            return jsonify({'success': True, 'message': 'Recording started'})
        else:
            return jsonify({'success': False, 'message': f'Cannot start recording in current state: {recording_state["status"]}'})
    except Exception as e:
        logger.error(f"Error triggering recording: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

def _cycle_and_play_dream():
    """Fetches dreams, cycles to the next one, and emits play_video event."""
    # Get the most recent dreams
    dreams = dream_db.get_all_dreams()
    if not dreams:
        logger.warning("No dreams found to cycle through.")
        return None  # Indicate no dreams found

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
    
    logger.info(f"Emitted play_video for dream index {video_playback_state['current_index']}: {dream['video_filename']}")
    return dream  # Return the selected dream object

@app.route('/api/show_previous_dream', methods=['POST'])
def show_previous_dream():
    """Handle single tap to show previous dream (API endpoint)."""
    try:
        dream = _cycle_and_play_dream()
        if dream:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'No dreams found'}), 404

    except Exception as e:
        logger.error(f"Error in API show_previous_dream: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dreams')
def dreams():
    """Display the dreams library page."""
    dreams = dream_db.get_all_dreams()
    return render_template('dreams.html', dreams=dreams)

@socketio.on('play_dream')
def handle_play_dream(data):
    """Handle when a dream video finishes playing."""
    # Reset the playback state when a video finishes
    video_playback_state['is_playing'] = False
    video_playback_state['current_index'] = 0

@socketio.on('show_previous_dream')
def handle_show_previous_dream():
    """Socket event handler for showing previous dream."""
    try:
        dream = _cycle_and_play_dream()
        if not dream:
            socketio.emit('error', {'message': 'No dreams found'})

    except Exception as e:
        logger.error(f"Error in socket handle_show_previous_dream: {str(e)}")
        socketio.emit('error', {'message': str(e)})

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
                video_path = os.path.join(os.getenv('VIDEOS_DIR'), dream['video_filename'])
                if os.path.exists(video_path):
                    os.remove(video_path)

                # Delete thumbnail file
                thumb_path = os.path.join(os.getenv('THUMBS_DIR'), dream['thumb_filename'])
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)

                # Delete audio file
                audio_path = os.path.join(os.getenv('RECORDINGS_DIR'), dream['audio_filename'])
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception as e:
                logger.error(f"Error deleting files for dream {dream_id}: {str(e)}")
                # Continue even if file deletion fails

            return jsonify({'success': True, 'message': 'Dream deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete dream'}), 500
    except Exception as e:
        logger.error(f"Error deleting dream {dream_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/clock-config-path')
def clock_config_path():
    """Return the clock configuration path from environment."""
    config_path = os.getenv('CLOCK_CONFIG_PATH')
    if not config_path:
        return jsonify({'error': 'CLOCK_CONFIG_PATH not set in environment'}), 500
    return jsonify({'configPath': config_path})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reload', action='store_true', help='Enable auto-reloader')
    args = parser.parse_args()
    
    socketio.run(
        app, 
        host=app.config['HOST'], 
        port=app.config['PORT'], 
        debug=app.config['DEBUG'],
        use_reloader=args.reload
    ) 