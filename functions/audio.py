import wave
import os
from datetime import datetime
import tempfile
import ffmpeg
import wave
from functions.video import generate_video_prompt, generate_video
from config_loader import load_config

config = load_config()

def create_wav_file(audio_buffer):
    """Create a new WAV file in the audio buffer with the correct format."""
    wav_file = wave.open(audio_buffer, 'wb')
    wav_file.setnchannels(int(config['AUDIO_CHANNELS']))
    wav_file.setsampwidth(int(config['AUDIO_SAMPLE_WIDTH']))
    wav_file.setframerate(int(config['AUDIO_FRAME_RATE']))
    return wav_file

def save_wav_file(audio_data, filename=None, logger=None):
    """Save the WAV file locally for debugging. Converts WebM to WAV using ffmpeg."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
    # Ensure the recordings directory exists
    os.makedirs(config['RECORDINGS_DIR'], exist_ok=True)
    filepath = os.path.join(config['RECORDINGS_DIR'], filename)
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

def process_audio(sid, client, socketio, dream_db, recording_state, audio_chunks, logger = None):
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
                model=config['WHISPER_MODEL'],
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
        luma_extend = str(config['LUMA_EXTEND']).lower() in ('1', 'true', 'yes')
        # Generate video prompt
        video_prompt = generate_video_prompt(transcription=transcription.text, luma_extend=luma_extend, client=client, logger=logger, config=config)
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
            from dream_db import DreamData
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
        dream_db.save_dream(dream_data.dict())
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