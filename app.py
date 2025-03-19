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
                'duration': '5s'
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Luma API error: {response.text}")
        
        generation_id = response.json()['id']
        logger.info(f"Started video generation with ID: {generation_id}")
        
        # Poll for completion
        while True:
            status_response = requests.get(
                f'https://api.lumalabs.ai/dream-machine/v1/generations/{generation_id}',
                headers={
                    'accept': 'application/json',
                    'authorization': f'Bearer {luma_api_key}'
                }
            )
            
            if status_response.status_code != 200:
                raise Exception(f"Luma API error: {status_response.text}")
            
            status_data = status_response.json()
            if status_data['status'] == 'completed':
                # Download the video
                video_url = status_data['output']['url']
                video_response = requests.get(video_url)
                
                if video_response.status_code != 200:
                    raise Exception("Failed to download video")
                
                # Save the video locally
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs("videos", exist_ok=True)
                video_path = os.path.join("videos", f"generated_{timestamp}.mp4")
                
                with open(video_path, 'wb') as f:
                    f.write(video_response.content)
                
                logger.info(f"Saved video to {video_path}")
                return video_path
            elif status_data['status'] == 'failed':
                raise Exception(f"Video generation failed: {status_data.get('error', 'Unknown error')}")
            
            time.sleep(5)  # Wait 5 seconds before polling again
            
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

        # Emit the transcription using the session ID
        socketio.emit('transcription_update', {'text': transcription.text}, room=sid)

        # Generate video prompt
        video_prompt = generate_video_prompt(transcription.text)
        if video_prompt:
            recording_state['video_prompt'] = video_prompt
            socketio.emit('video_prompt_update', {'text': video_prompt}, room=sid)
            
            # Generate video
            try:
                video_path = generate_video(video_prompt)
                recording_state['video_url'] = f'/videos/{os.path.basename(video_path)}'
                socketio.emit('video_ready', {'url': recording_state['video_url']}, room=sid)
            except Exception as e:
                socketio.emit('error', {'message': f"Error generating video: {str(e)}"}, room=sid)
        else:
            socketio.emit('error', {'message': "Failed to generate video prompt"}, room=sid)

        # Clean up the temporary file
        os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        socketio.emit('error', {'message': f"Error processing audio: {str(e)}"}, room=sid)
    finally:
        # Reset the buffer and chunks
        audio_buffer = io.BytesIO()
        audio_chunks = []

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
        
        # Update state to complete after processing
        recording_state['status'] = 'complete'
        emit('state_update', recording_state)

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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5010))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_ENV') == 'development'
    socketio.run(app, host=host, port=port, debug=debug) 