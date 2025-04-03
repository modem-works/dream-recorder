from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import os
from dotenv import load_dotenv
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

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize Luma Labs API key
luma_api_key = os.getenv('LUMALABS_API_KEY')
if not luma_api_key:
    raise ValueError("LUMALABS_API_KEY environment variable is not set")

# Initialize OpenAI client with specific configuration
client = OpenAI(
    api_key=openai_api_key,
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

# Audio buffer for storing chunks
audio_buffer = io.BytesIO()
wav_file = None
audio_chunks = []

def create_wav_file():
    global wav_file
    wav_file = wave.open(audio_buffer, 'wb')
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(44100)  # 44.1kHz

def save_wav_file(audio_data, filename=None):
    """Save the WAV file locally for debugging."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
    
    # Ensure the recordings directory exists
    os.makedirs("recordings", exist_ok=True)
    filepath = os.path.join("recordings", filename)
    
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(44100)  # 44.1kHz
        wf.writeframes(audio_data)
    
    logger.info(f"Saved WAV file to {filepath}")
    return filepath

def generate_video_prompt(transcription):
    """Generate an enhanced video prompt from the transcription using GPT."""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": """You are a creative video prompt engineer. 
                Your task is to transform dream descriptions into detailed, cinematic video prompts.
                Focus on visual elements, atmosphere, and emotional tone.
                Keep the prompt concise but rich in visual detail.
                Format the response as a single paragraph."""},
                {"role": "user", "content": f"Transform this dream description into a detailed video prompt: {transcription}"}
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating video prompt: {str(e)}")
        return None

def generate_video(prompt):
    """Generate a video using Luma Labs API."""
    try:
        # Create the generation request
        response = requests.post(
            'https://api.lumalabs.ai/dream-machine/v1/generations',
            headers={
                'accept': 'application/json',
                'authorization': f'Bearer {luma_api_key}',
                'content-type': 'application/json'
            },
            json={
                'prompt': prompt,
                'model': 'ray-2',
                'resolution': '540p',
                'duration': '5s',
                "aspect_ratio": "21:9",
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
        max_attempts = 60
        poll_interval = 5
        
        for attempt in range(max_attempts):
            status_response = requests.get(
                f'https://api.lumalabs.ai/dream-machine/v1/generations/{generation_id}',
                headers={
                    'accept': 'application/json',
                    'authorization': f'Bearer {luma_api_key}'
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
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs("videos", exist_ok=True)
                video_path = os.path.join("videos", f"generated_{timestamp}.mp4")
                
                with open(video_path, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Saved video to {video_path}")
                return video_path
                
            elif state in ['failed', 'error']:
                error_msg = status_data.get('failure_reason') or status_data.get('error') or "Unknown error"
                raise Exception(f"Video generation failed: {error_msg}")
            
            time.sleep(poll_interval)
        
        raise Exception(f"Timed out waiting for video generation after {max_attempts} attempts")
            
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        raise

def process_audio(sid):
    global audio_buffer, wav_file, audio_chunks
    try:
        # Close the WAV file properly
        if wav_file:
            wav_file.close()
            wav_file = None

        # Combine all audio chunks
        combined_audio = b''.join(audio_chunks)
        
        # Save the WAV file locally for debugging
        wav_filepath = save_wav_file(combined_audio)
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(combined_audio)
            temp_file_path = temp_file.name

        # Transcribe the audio using OpenAI's Whisper API
        with open(temp_file_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        # Update the transcription in the global state
        recording_state['transcription'] = transcription.text

        # Emit the transcription using the session ID if available
        if sid:
            socketio.emit('transcription_update', {'text': transcription.text}, room=sid)
        else:
            # Broadcast to all connected clients if no specific session
            socketio.emit('transcription_update', {'text': transcription.text})

        # Generate video prompt
        video_prompt = generate_video_prompt(transcription.text)
        if video_prompt:
            recording_state['video_prompt'] = video_prompt
            if sid:
                socketio.emit('video_prompt_update', {'text': video_prompt}, room=sid)
            else:
                socketio.emit('video_prompt_update', {'text': video_prompt})
            
            # Generate video
            try:
                video_path = generate_video(video_prompt)
                recording_state['video_url'] = f'/videos/{os.path.basename(video_path)}'
                if sid:
                    socketio.emit('video_ready', {'url': recording_state['video_url']}, room=sid)
                else:
                    socketio.emit('video_ready', {'url': recording_state['video_url']})
            except Exception as e:
                if sid:
                    socketio.emit('error', {'message': f"Error generating video: {str(e)}"}, room=sid)
                else:
                    socketio.emit('error', {'message': f"Error generating video: {str(e)}"})
        else:
            error_msg = "Failed to generate video prompt"
            logger.error(error_msg)
            if sid:
                socketio.emit('error', {'message': error_msg}, room=sid)
            else:
                socketio.emit('error', {'message': error_msg})

        # Clean up the temporary file
        os.unlink(temp_file_path)

        # Set status to complete
        recording_state['status'] = 'complete'
        socketio.emit('state_update', recording_state)

    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        error_msg = f"Error processing audio: {str(e)}"
        if sid:
            socketio.emit('error', {'message': error_msg}, room=sid)
        else:
            socketio.emit('error', {'message': error_msg})
            
        # Set status to complete even on error
        recording_state['status'] = 'complete'
        socketio.emit('state_update', recording_state)
    finally:
        # Reset the buffer and chunks
        audio_buffer = io.BytesIO()
        audio_chunks = []

@socketio.on('generate_video')
def handle_generate_video(data):
    """Handle video generation request."""
    try:
        recording_state['status'] = 'generating'
        socketio.emit('state_update', recording_state)
        
        # Generate video
        video_path = generate_video(data['prompt'])
        recording_state['video_url'] = f'/videos/{os.path.basename(video_path)}'
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
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    return jsonify({
        'is_development': True,
        'api_keys_configured': bool(os.getenv('OPENAI_API_KEY') and os.getenv('LUMALABS_API_KEY'))
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
    if recording_state['is_recording'] and wav_file:
        try:
            # Convert the received data to bytes
            audio_bytes = bytes(data['data'])
            # Store the chunk
            audio_chunks.append(audio_bytes)
            # Write to the WAV file
            wav_file.writeframes(audio_bytes)
        except Exception as e:
            logger.error(f"Error writing audio data: {str(e)}")
            emit('error', {'message': f"Error writing audio data: {str(e)}"})

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_file(os.path.join('videos', filename))

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
    """API endpoint to show the most recent dream (double tap)."""
    try:
        # Find the most recent video
        videos_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
        if os.path.exists(videos_dir):
            # Get all mp4 files sorted by modification time (newest first)
            video_files = [f for f in os.listdir(videos_dir) if f.endswith('.mp4')]
            if video_files:
                video_files.sort(key=lambda x: os.path.getmtime(os.path.join(videos_dir, x)), reverse=True)
                latest_video = video_files[0]
                
                # Send the video URL to clients
                video_url = f'/videos/{latest_video}'
                socketio.emit('device_event', {
                    'action': 'show_dream',
                    'video_url': video_url
                })
                logger.info(f"Showing previous dream video: {latest_video} via GPIO double tap")
                return jsonify({'success': True, 'message': 'Showing previous dream', 'video_url': video_url})
            else:
                logger.info("No previous dreams found")
                socketio.emit('device_event', {
                    'action': 'notification',
                    'message': 'No previous dreams found'
                })
                return jsonify({'success': False, 'message': 'No previous dreams found'})
        else:
            logger.error(f"Videos directory not found: {videos_dir}")
            return jsonify({'success': False, 'message': 'Videos directory not found'}), 404
    except Exception as e:
        logger.error(f"Error showing previous dream: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_ENV') == 'development'
    socketio.run(app, host=host, port=port, debug=debug) 