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
from env_check import check_required_env_vars
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

def generate_video_prompt(transcription):
    """Generate an enhanced video prompt from the transcription using GPT."""
    try:
        response = client.chat.completions.create(
            model=os.getenv('GPT_MODEL'),
            messages=[
                {"role": "system", "content": os.getenv('GPT_SYSTEM_PROMPT')},
                {"role": "user", "content": f"Transform this dream description into a detailed video prompt: {transcription}"}
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
        stream = ffmpeg.filter(stream, 'eq', brightness=float(os.getenv('FFMPEG_BRIGHTNESS', 0.2)))
        stream = ffmpeg.filter(stream, 'vibrance', intensity=float(os.getenv('FFMPEG_VIBRANCE', 2)))
        stream = ffmpeg.filter(stream, 'vaguedenoiser', threshold=float(os.getenv('FFMPEG_DENOISE_THRESHOLD', 300)))
        stream = ffmpeg.filter(stream, 'bilateral', sigmaS=float(os.getenv('FFMPEG_BILATERAL_SIGMA', 100)))
        stream = ffmpeg.filter(stream, 'noise', all_strength=float(os.getenv('FFMPEG_NOISE_STRENGTH', 40)))
        stream = ffmpeg.output(stream, temp_path)
        
        # Run FFmpeg
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        # Replace the original file with the processed one
        os.replace(temp_path, input_path)
        
        logger.info(f"Processed video saved to {input_path}")
        
        # Generate thumbnail after video processing
        process_thumbnail(input_path)
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

def generate_video(prompt, filename=None):
    """Generate a video using Luma Labs API."""
    try:
        # Create the generation request
        response = requests.post(
            os.getenv('LUMA_GENERATIONS_ENDPOINT'),
            headers={
                'accept': 'application/json',
                'authorization': f'Bearer {os.getenv("LUMALABS_API_KEY")}',
                'content-type': 'application/json'
            },
            json={
                'prompt': prompt,
                'model': os.getenv('LUMA_MODEL'),
                'resolution': os.getenv('LUMA_RESOLUTION'),
                'duration': os.getenv('LUMA_DURATION'),
                "aspect_ratio": os.getenv('LUMA_ASPECT_RATIO'),
            }
        )
        
        # Accept both 200 and 201 status codes
        if response.status_code not in [200, 201]:
            raise Exception(f"Luma API error: {response.text}")
        
        response_data = response.json()
        logger.info(f"API response: {response_data}")
        
        generation_id = response_data.get('id')
        if not generation_id:
            raise Exception("Failed to get generation ID from response")
        
        logger.info(f"Started video generation with ID: {generation_id}")
        
        # Poll for completion with more detailed status checking
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
            
            # Log the full response periodically for debugging
            if attempt == 0 or attempt % 10 == 0:
                logger.info(f"Full status response: {status_data}")
            
            # Check for different possible state values
            state = status_data.get('state')
            logger.info(f"Generation state: {state} (attempt {attempt+1}/{max_attempts})")
            
            if state in ['completed', 'succeeded']:
                # Try to extract the video URL from different possible locations
                assets = status_data.get('assets') or {}
                video_url = None
                
                if isinstance(assets, dict):
                    video_url = (assets.get('video') or 
                               assets.get('url') or 
                               (assets.get('videos', {}) or {}).get('url'))
                
                # Also check the result field for backward compatibility
                if not video_url and 'result' in status_data:
                    result = status_data.get('result', {})
                    if isinstance(result, dict):
                        video_url = result.get('url')
                
                if not video_url:
                    raise Exception("Video URL not found in completed response")
                
                logger.info(f"Video generation completed: {video_url}")
                
                # Download the video
                video_response = requests.get(video_url, stream=True)
                video_response.raise_for_status()
                
                # Save the video locally
                if filename is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"generated_{timestamp}.mp4"
                
                os.makedirs(os.getenv('VIDEOS_DIR'), exist_ok=True)
                video_path = os.path.join(os.getenv('VIDEOS_DIR'), filename)
                
                with open(video_path, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Saved video to {video_path}")
                
                # Process the video with FFmpeg
                processed_video_path = process_video(video_path)
                logger.info(f"Processed video saved to {processed_video_path}")
                
                return filename  # Return only the filename
                
            elif state in ['failed', 'error']:
                error_msg = status_data.get('failure_reason') or status_data.get('error') or "Unknown error"
                raise Exception(f"Video generation failed: {error_msg}")
            
            time.sleep(poll_interval)
        
        raise Exception(f"Timed out waiting for video generation after {max_attempts} attempts")
            
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

        # Generate video prompt
        video_prompt = generate_video_prompt(transcription.text)
        if not video_prompt:
            raise Exception("Failed to generate video prompt")
        
        recording_state['video_prompt'] = video_prompt
        if sid:
            socketio.emit('video_prompt_update', {'text': video_prompt}, room=sid)
        else:
            socketio.emit('video_prompt_update', {'text': video_prompt})
        
        # Generate video
        video_filename = generate_video(video_prompt)
        
        # Save to database
        dream_data = {
            'user_prompt': recording_state['transcription'],
            'generated_prompt': recording_state['video_prompt'],
            'audio_filename': wav_filename,
            'video_filename': video_filename,
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

@socketio.on('generate_video')
def handle_generate_video(data):
    """Handle video generation request."""
    try:
        recording_state['status'] = 'generating'
        socketio.emit('state_update', recording_state)
        
        # Generate video
        video_filename = generate_video(data['prompt'])
        recording_state['video_url'] = f'/media/video/{video_filename}'
        socketio.emit('video_ready', {'url': recording_state['video_url']})
        
        # Update state to complete
        recording_state['status'] = 'complete'
        socketio.emit('state_update', recording_state)
        
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        socketio.emit('error', {'message': f"Error generating video: {str(e)}"})
        recording_state['status'] = 'complete'
        socketio.emit('state_update', recording_state)

@app.route('/')
def index():
    return render_template('index.html', is_development=app.config['DEBUG'])

@app.route('/api/config')
def get_config():
    return jsonify({
        'is_development': app.config['DEBUG'],
        'playback_duration': int(os.getenv('PLAYBACK_DURATION')),
        'idle_timeout': int(os.getenv('IDLE_TIMEOUT'))
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
    """API endpoint to trigger recording from GPIO controller (long press)."""
    try:
        if recording_state['status'] == 'ready':
            # Simulate a start_recording event
            recording_state['is_recording'] = True
            recording_state['status'] = 'recording'
            
            # Reset the audio buffer
            global audio_buffer, wav_file, audio_chunks
            audio_buffer = io.BytesIO()
            audio_chunks = []
            create_wav_file()
            
            # Broadcast the recording state change to all clients
            socketio.emit('recording_state', {'status': 'recording'})
            logger.info("Recording triggered via GPIO long press")
            return jsonify({'success': True, 'message': 'Recording started'})
        else:
            return jsonify({'success': False, 'message': f'Cannot start recording in current state: {recording_state["status"]}'})
    except Exception as e:
        logger.error(f"Error triggering recording: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wake_device', methods=['POST'])
def wake_device():
    """API endpoint to wake the device (single tap)."""
    try:
        # If device is sleeping, wake it up by sending a wake event to clients
        socketio.emit('device_event', {'action': 'wake'})
        logger.info("Device wake triggered via GPIO single tap")
        return jsonify({'success': True, 'message': 'Device woken up'})
    except Exception as e:
        logger.error(f"Error waking device: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/show_previous_dream', methods=['POST'])
def show_previous_dream():
    """Handle double-tap to show previous dream or cycle through recent dreams."""
    try:
        # Get the most recent dreams, limited by VIDEO_HISTORY_LIMIT
        dreams = dream_db.get_all_dreams()
        if not dreams:
            return jsonify({'status': 'error', 'message': 'No dreams found'}), 404
        
        # If we're not currently playing a video, start with the most recent
        if not video_playback_state['is_playing']:
            video_playback_state['current_index'] = 0
            video_playback_state['is_playing'] = True
        else:
            # Move to the next video in the sequence
            video_playback_state['current_index'] += 1
            
            # If we've reached the limit, wrap around to the most recent
            if video_playback_state['current_index'] >= int(os.getenv('VIDEO_HISTORY_LIMIT')):
                video_playback_state['current_index'] = 0
        
        # Get the video at the current index
        dream = dreams[video_playback_state['current_index']]
        
        # Emit the video URL to the client
        socketio.emit('play_video', {
            'video_url': f"/media/video/{dream['video_filename']}",
            'loop': True  # Enable looping for the video
        })
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error showing previous dream: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop_recording', methods=['POST'])
def stop_recording_api():
    """API endpoint to stop recording from GPIO controller (long press release)."""
    try:
        if recording_state['is_recording'] and recording_state['status'] == 'recording':
            # Set recording state to processing
            recording_state['is_recording'] = False
            recording_state['status'] = 'processing'
            
            # Broadcast the state change to all clients
            socketio.emit('recording_state', {'status': 'processing'})
            logger.info("Recording stopped via GPIO long press release")
            
            # Get the first available client session ID
            sessions = list(socketio.server.environ.keys())
            if sessions:
                sid = sessions[0]
                # Process the audio in a background task
                gevent.spawn(process_audio, sid)
            else:
                logger.warning("No active sessions found for audio processing")
                # Process audio without a session
                gevent.spawn(process_audio, None)
            
            return jsonify({'success': True, 'message': 'Recording stopped and processing started'})
        else:
            return jsonify({'success': False, 'message': f'Cannot stop recording in current state: {recording_state["status"]}'})
    except Exception as e:
        logger.error(f"Error stopping recording: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

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
        # Get the most recent dreams, limited by VIDEO_HISTORY_LIMIT
        dreams = dream_db.get_all_dreams()
        if not dreams:
            socketio.emit('error', {'message': 'No dreams found'})
            return
        
        # If we're not currently playing a video, start with the most recent
        if not video_playback_state['is_playing']:
            video_playback_state['current_index'] = 0
            video_playback_state['is_playing'] = True
        else:
            # Move to the next video in the sequence
            video_playback_state['current_index'] += 1
            
            # If we've reached the limit, wrap around to the most recent
            if video_playback_state['current_index'] >= int(os.getenv('VIDEO_HISTORY_LIMIT')):
                video_playback_state['current_index'] = 0
        
        # Get the video at the current index
        dream = dreams[video_playback_state['current_index']]
        
        # Emit the video URL to the client
        socketio.emit('play_video', {
            'video_url': f"/media/video/{dream['video_filename']}",
            'loop': True  # Enable looping for the video
        })
        
    except Exception as e:
        logger.error(f"Error showing previous dream: {str(e)}")
        socketio.emit('error', {'message': str(e)})

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