import wave
import os
import tempfile
import ffmpeg
import wave

from datetime import datetime
from functions.video import generate_video
from functions.config_loader import get_config
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(
    api_key=get_config()["OPENAI_API_KEY"],
    http_client=None
)

def create_wav_file(audio_buffer):
    """Create a new WAV file in the audio buffer with the correct format."""
    wav_file = wave.open(audio_buffer, 'wb')
    wav_file.setnchannels(int(get_config()['AUDIO_CHANNELS']))
    wav_file.setsampwidth(int(get_config()['AUDIO_SAMPLE_WIDTH']))
    wav_file.setframerate(int(get_config()['AUDIO_FRAME_RATE']))
    return wav_file

def save_wav_file(audio_data, filename=None, logger=None):
    """Save the WAV file locally for debugging. Converts WebM to WAV using ffmpeg."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
    # Ensure the recordings directory exists
    os.makedirs(get_config()['RECORDINGS_DIR'], exist_ok=True)
    filepath = os.path.join(get_config()['RECORDINGS_DIR'], filename)
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
        return filename
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_webm_path)
        except:
            pass

def generate_video_prompt(transcription, luma_extend=False, logger=None, config=None):
    """Generate an enhanced video prompt from the transcription using GPT."""
    try:
        system_prompt = get_config()['GPT_SYSTEM_PROMPT_EXTEND'] if luma_extend else get_config()['GPT_SYSTEM_PROMPT']
        response = client.chat.completions.create(
            model=get_config()['GPT_MODEL'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{transcription}"}
            ],
            temperature=float(get_config()['GPT_TEMPERATURE']),
            max_tokens=int(get_config()['GPT_MAX_TOKENS'])
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        if logger:
            logger.error(f"Error generating video prompt: {str(e)}")
        return None

def process_audio(sid, socketio, dream_db, recording_state, audio_chunks, logger = None):
    """Process the recorded audio and generate video, then update state and emit events."""
    try:
        audio_data = b''.join(audio_chunks)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_filename = f"recording_{timestamp}.wav"
        wav_filename = save_wav_file(audio_data, wav_filename, logger)
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        # Transcribe the audio using OpenAI's Whisper API
        with open(temp_file_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model=get_config()['WHISPER_MODEL'],
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
        luma_extend = str(get_config()['LUMA_EXTEND']).lower() in ('1', 'true', 'yes')
        # Generate video prompt
        video_prompt = generate_video_prompt(transcription=transcription.text, luma_extend=luma_extend, logger=logger, config=get_config())
        if not video_prompt:
            raise Exception("Failed to generate video prompt")
        recording_state['video_prompt'] = video_prompt
        if sid:
            socketio.emit('video_prompt_update', {'text': video_prompt}, room=sid)
        else:
            socketio.emit('video_prompt_update', {'text': video_prompt})
        video_filename, thumb_filename = generate_video(prompt=video_prompt, luma_extend=luma_extend, logger=logger)
        # Save to database
        DreamData = None
        try:
            from functions.dream_db import DreamData
        except ImportError:
            pass
        dream_data = DreamData(
            user_prompt=recording_state['transcription'],
            generated_prompt=recording_state['video_prompt'],
            audio_filename=wav_filename,
            video_filename=video_filename,
            thumb_filename=thumb_filename,
            status='completed',
        )
        dream_db.save_dream(dream_data.model_dump())
        recording_state['status'] = 'complete'
        recording_state['video_url'] = f"/media/video/{video_filename}"
        # Emit the video ready event to trigger playback
        if sid:
            socketio.emit('video_ready', {'url': recording_state['video_url']}, room=sid)
        else:
            socketio.emit('video_ready', {'url': recording_state['video_url']})
        if logger:
            logger.info(f"Audio processed and video generated for SID: {sid}")
    except Exception as e:
        recording_state['status'] = 'error'
        socketio.emit('error', {'message': str(e)})
        if logger:
            logger.error(f"Error processing audio: {str(e)}")
    finally:
        # Clean up
        audio_chunks = []
        # Remove temporary file if it exists
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass