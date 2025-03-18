"""
Audio Handler for Dream Recorder
Handles WebSocket audio streaming and processing
"""

import os
import logging
import time
import tempfile
from pathlib import Path
import wave
import base64
from io import BytesIO
import numpy as np
from pydub import AudioSegment
import subprocess
import shutil
from datetime import datetime
import contextlib
import threading
import sys

logger = logging.getLogger(__name__)

# Create a context manager to suppress the thread initialization warnings
@contextlib.contextmanager
def suppress_thread_exception():
    """Context manager to suppress thread initialization warnings from subprocess calls."""
    original_threading_excepthook = threading.excepthook
    
    def _suppress_thread_init_warning(args):
        # Only suppress the specific AssertionError about Thread.__init__
        if isinstance(args.exc_value, AssertionError) and "Thread.__init__() not called" in str(args.exc_value):
            return
        original_threading_excepthook(args)
        
    threading.excepthook = _suppress_thread_init_warning
    try:
        yield
    finally:
        threading.excepthook = original_threading_excepthook

class AudioHandler:
    """Handles audio data from WebSockets"""
    
    def __init__(self):
        self.audio_chunks = []
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.audio_dir = os.path.join(self.base_path, 'data', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)
        self.recording_id = None
        self.output_path = None
        self.recording_start_time = None
        self.current_audio_file = None
        logger.info(f"AudioHandler initialized. Audio directory: {self.audio_dir}")
        
        # Check for ffmpeg
        try:
            with suppress_thread_exception():
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=False)
                logger.info("FFmpeg found and working")
        except FileNotFoundError:
            logger.warning("FFmpeg not found. Audio conversion may fail.")
        except Exception as e:
            logger.warning(f"Error checking FFmpeg: {e}")
        
    def reset_buffer(self):
        """Reset the audio buffer"""
        self.audio_chunks = []
        self.current_audio_file = None
        self.recording_start_time = None
        logger.info("Audio buffer reset")
    
    def start_new_recording(self):
        """Initialize a new recording session with a unique ID."""
        self.recording_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = os.path.join(self.audio_dir, f"recording_{self.recording_id}.wav")
        self.audio_chunks = []  # Clear any existing chunks
        self.recording_start_time = time.time()  # Record when we started
        logger.info(f"Starting new recording: {self.recording_id}")
        return self.recording_id

    def process_audio_chunk(self, base64_audio):
        """Process a single chunk of base64-encoded audio data."""
        try:
            # Decode base64 data
            audio_data = base64.b64decode(base64_audio)
            
            # Log info about the received chunk
            logger.debug(f"Received audio chunk: {len(audio_data)} bytes")
            
            # Verify that we have actual audio data (not empty)
            if len(audio_data) > 0:
                # Add to chunks list
                self.audio_chunks.append(audio_data)
                return True
            else:
                logger.warning("Received empty audio chunk, ignoring")
                return False
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return False

    def finalize_recording(self):
        """Combine all audio chunks and save to a file."""
        if not self.recording_id or not self.output_path:
            logger.error("Cannot finalize recording: No recording_id or output_path")
            return None

        if not self.audio_chunks:
            logger.warning("No audio chunks received, creating silent WAV file")
            self._create_dummy_wav()
            return self.output_path

        # Calculate recording duration
        duration = 0
        if self.recording_start_time:
            duration = time.time() - self.recording_start_time
            logger.info(f"Recording duration: {duration:.2f} seconds")

        logger.info(f"Finalizing recording {self.recording_id} with {len(self.audio_chunks)} chunks")
        
        # Try different approaches in order of reliability
        success = False
        
        # 1. First try the combined WebM approach
        success = self._save_combined_webm()
        if success:
            logger.info(f"Successfully saved audio using combined WebM approach")
            return self.output_path
            
        # 2. Try the individual chunk conversion approach if the first method failed
        if not success:
            logger.info("Combined WebM approach failed, trying individual chunk conversion")
            success = self._save_individual_chunks()
            if success:
                logger.info(f"Successfully saved audio using individual chunk conversion")
                return self.output_path
        
        # 3. Try the raw PCM concatenation approach as a last resort
        if not success:
            logger.info("Individual chunk conversion failed, trying raw PCM concatenation")
            success = self._save_pcm_concatenation()
            if success:
                logger.info(f"Successfully saved audio using PCM concatenation")
                return self.output_path
        
        # If all methods failed, create a dummy WAV
        if not success:
            logger.warning("All audio conversion methods failed, creating dummy WAV")
            self._create_dummy_wav()
        
        return self.output_path

    def _save_combined_webm(self):
        """Save all audio chunks as a single WebM file and then convert to WAV."""
        if not self.audio_chunks:
            return False
            
        # Calculate total size of all chunks for logging
        total_size = sum(len(chunk) for chunk in self.audio_chunks)
        if total_size == 0:
            logger.warning("Total audio data size is 0 bytes, cannot create valid audio file")
            return False
        
        logger.info(f"Saving audio data: total size {total_size} bytes across {len(self.audio_chunks)} chunks")

        # Use a unique temp directory for this conversion
        with tempfile.TemporaryDirectory(prefix=f"audio_{self.recording_id}_") as temp_dir:
            # Save all chunks to a single file
            combined_webm_path = os.path.join(temp_dir, f"combined_{self.recording_id}.webm")
            
            try:
                # Write all chunks to a single file
                with open(combined_webm_path, 'wb') as f:
                    for i, chunk in enumerate(self.audio_chunks):
                        f.write(chunk)
                        
                logger.info(f"Wrote combined WebM file: {os.path.getsize(combined_webm_path)} bytes")
                
                # Now run FFmpeg to fix any issues with the WebM headers and convert to WAV
                clean_webm_path = os.path.join(temp_dir, f"clean_{self.recording_id}.webm")
                fix_cmd = [
                    'ffmpeg', '-y',
                    '-i', combined_webm_path,
                    '-c:a', 'copy',  # Copy audio without re-encoding
                    clean_webm_path
                ]
                
                logger.info(f"Running FFmpeg to fix WebM: {' '.join(fix_cmd)}")
                with suppress_thread_exception():
                    fix_result = subprocess.run(fix_cmd, capture_output=True, text=True)
                
                if fix_result.returncode != 0:
                    logger.warning(f"FFmpeg WebM fix failed: {fix_result.stderr}")
                    return False
                
                # Convert the fixed WebM to WAV
                wav_cmd = [
                    'ffmpeg', '-y',
                    '-i', clean_webm_path,
                    '-vn',  # No video
                    '-acodec', 'pcm_s16le',  # Simple PCM codec
                    '-ar', '44100',         # Standard sample rate
                    '-ac', '1',             # Mono
                    '-f', 'wav',            # Force WAV format
                    self.output_path
                ]
                
                logger.info(f"Running FFmpeg WAV conversion: {' '.join(wav_cmd)}")
                with suppress_thread_exception():
                    wav_result = subprocess.run(wav_cmd, capture_output=True, text=True)
                
                if wav_result.returncode != 0:
                    logger.warning(f"FFmpeg WAV conversion failed: {wav_result.stderr}")
                    return False
                    
                # Verify the output file
                if os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 1000:
                    # Check duration
                    try:
                        duration_cmd = [
                            'ffprobe', '-v', 'error',
                            '-show_entries', 'format=duration',
                            '-of', 'default=noprint_wrappers=1:nokey=1',
                            self.output_path
                        ]
                        with suppress_thread_exception():
                            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                        if duration_result.returncode == 0:
                            file_duration = float(duration_result.stdout.strip())
                            logger.info(f"Generated WAV duration: {file_duration:.2f} seconds")
                            
                            # Check if duration is reasonable
                            expected_duration = time.time() - self.recording_start_time
                            if file_duration < 0.5 * expected_duration and expected_duration > 2.0:
                                logger.warning(f"WAV duration ({file_duration:.2f}s) much shorter than expected ({expected_duration:.2f}s)")
                                return False
                    except Exception as e:
                        logger.error(f"Error checking duration: {e}")
                        
                    return True
                else:
                    logger.warning(f"Output file missing or too small: {self.output_path}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error in combined WebM approach: {e}")
                return False
                
        return False

    def _save_individual_chunks(self):
        """Convert each WebM chunk to WAV individually, then concatenate the WAV files."""
        try:
            with tempfile.TemporaryDirectory(prefix=f"chunks_{self.recording_id}_") as temp_dir:
                wav_files = []
                
                # Convert each chunk to WAV
                for i, chunk in enumerate(self.audio_chunks):
                    # Save the chunk
                    chunk_path = os.path.join(temp_dir, f"chunk_{i}.webm")
                    with open(chunk_path, 'wb') as f:
                        f.write(chunk)
                    
                    # Convert to WAV
                    wav_path = os.path.join(temp_dir, f"chunk_{i}.wav")
                    convert_cmd = [
                        'ffmpeg', '-y',
                        '-i', chunk_path,
                        '-vn',  # No video
                        '-acodec', 'pcm_s16le',  # PCM codec
                        '-ar', '44100',          # Standard sample rate
                        '-ac', '1',              # Mono
                        wav_path
                    ]
                    
                    try:
                        with suppress_thread_exception():
                            result = subprocess.run(convert_cmd, capture_output=True, text=True)
                        if result.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 100:
                            wav_files.append(wav_path)
                        else:
                            logger.warning(f"Failed to convert chunk {i} to WAV")
                    except Exception as e:
                        logger.warning(f"Error converting chunk {i}: {e}")
                
                if not wav_files:
                    logger.warning("No chunks could be converted to WAV")
                    return False
                
                # Create a list file for FFmpeg concat
                list_path = os.path.join(temp_dir, "wav_list.txt")
                with open(list_path, 'w') as f:
                    for wav_file in wav_files:
                        f.write(f"file '{wav_file}'\n")
                
                # Concatenate WAV files
                concat_cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', list_path,
                    '-c:a', 'pcm_s16le',
                    '-ar', '44100',
                    '-ac', '1',
                    self.output_path
                ]
                
                logger.info(f"Running FFmpeg to concatenate {len(wav_files)} WAV files: {' '.join(concat_cmd)}")
                with suppress_thread_exception():
                    concat_result = subprocess.run(concat_cmd, capture_output=True, text=True)
                
                if concat_result.returncode == 0 and os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 1000:
                    logger.info(f"Successfully concatenated {len(wav_files)} WAV files")
                    return True
                else:
                    logger.warning(f"Failed to concatenate WAV files: {concat_result.stderr}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error in individual chunks approach: {e}")
            return False
            
        return False
        
    def _save_pcm_concatenation(self):
        """Extract raw PCM audio from each chunk and concatenate them."""
        try:
            with tempfile.TemporaryDirectory(prefix=f"pcm_{self.recording_id}_") as temp_dir:
                pcm_path = os.path.join(temp_dir, "combined.pcm")
                
                # Extract PCM from each chunk and append to a single file
                with open(pcm_path, 'wb') as pcm_file:
                    for i, chunk in enumerate(self.audio_chunks):
                        # Save the chunk
                        chunk_path = os.path.join(temp_dir, f"chunk_{i}.webm")
                        with open(chunk_path, 'wb') as f:
                            f.write(chunk)
                        
                        # Extract PCM data
                        extract_cmd = [
                            'ffmpeg', '-y',
                            '-i', chunk_path,
                            '-vn',  # No video
                            '-f', 's16le',  # PCM format
                            '-acodec', 'pcm_s16le',
                            '-ar', '44100',
                            '-ac', '1',
                            '-'     # Output to stdout
                        ]
                        
                        try:
                            with suppress_thread_exception():
                                result = subprocess.run(extract_cmd, capture_output=True)
                            if result.returncode == 0 and result.stdout:
                                pcm_file.write(result.stdout)
                            else:
                                logger.warning(f"Failed to extract PCM from chunk {i}: {result.stderr.decode()}")
                        except Exception as e:
                            logger.warning(f"Error extracting PCM from chunk {i}: {e}")
                
                # Check if we got any PCM data
                if os.path.getsize(pcm_path) == 0:
                    logger.warning("No PCM data extracted")
                    return False
                
                # Create a WAV file from the PCM data
                wav_cmd = [
                    'ffmpeg', '-y',
                    '-f', 's16le',  # PCM format
                    '-ar', '44100',  # Sample rate
                    '-ac', '1',      # Mono
                    '-i', pcm_path,
                    self.output_path
                ]
                
                logger.info(f"Creating WAV from PCM data: {' '.join(wav_cmd)}")
                with suppress_thread_exception():
                    result = subprocess.run(wav_cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 1000:
                    logger.info(f"Successfully created WAV from PCM data: {os.path.getsize(self.output_path)} bytes")
                    return True
                else:
                    logger.warning(f"Failed to create WAV from PCM data: {result.stderr}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error in PCM concatenation approach: {e}")
            return False
            
        return False

    def _try_alternative_ffmpeg_conversion(self, input_file):
        """Try an alternative FFmpeg conversion with different parameters"""
        try:
            logger.info("Attempting alternative FFmpeg conversion")
            alt_output = os.path.join(self.audio_dir, f"alt_wav_{self.recording_id}.wav")
            
            # Try with different codec parameters
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-i', input_file,
                '-acodec', 'pcm_s16le',  # Use a simple PCM codec
                '-ar', '16000',          # Lower sample rate
                '-ac', '1',              # Mono
                alt_output
            ]
            
            logger.info(f"Running alternative FFmpeg command: {' '.join(ffmpeg_cmd)}")
            
            with suppress_thread_exception():
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(alt_output) and os.path.getsize(alt_output) > 100:
                # Copy to final destination
                shutil.copy(alt_output, self.output_path)
                logger.info(f"Alternative FFmpeg conversion successful: {os.path.getsize(self.output_path)} bytes")
                
                # Clean up
                try:
                    os.remove(alt_output)
                except:
                    pass
                
                return True
            else:
                logger.error(f"Alternative FFmpeg conversion failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error in alternative FFmpeg conversion: {e}")
            return False

    def _create_dummy_wav(self):
        """Create a 1-second silent WAV file as a fallback."""
        try:
            # Create 1 second of silence
            silence = AudioSegment.silent(duration=1000)  # 1000ms = 1 second
            silence.export(self.output_path, format="wav")
            logger.info(f"Created 1-second silent WAV file at {self.output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create dummy WAV file: {e}")
            try:
                # Even more basic fallback using direct write of a minimal WAV header
                logger.info("Attempting to create minimal WAV file directly")
                with open(self.output_path, 'wb') as f:
                    # Basic WAV header for 1 second of silence (44100Hz, 16-bit, mono)
                    sample_rate = 44100
                    duration_sec = 1
                    channels = 1
                    bits_per_sample = 16
                    
                    # Calculate data size
                    data_size = int(sample_rate * duration_sec * channels * bits_per_sample / 8)
                    
                    # RIFF header
                    f.write(b'RIFF')
                    f.write((data_size + 36).to_bytes(4, byteorder='little'))  # File size - 8
                    f.write(b'WAVE')
                    
                    # Format chunk
                    f.write(b'fmt ')
                    f.write((16).to_bytes(4, byteorder='little'))  # Chunk size
                    f.write((1).to_bytes(2, byteorder='little'))   # Audio format (PCM)
                    f.write((channels).to_bytes(2, byteorder='little'))  # Channels
                    f.write((sample_rate).to_bytes(4, byteorder='little'))  # Sample rate
                    
                    # Bytes per second and block align
                    byte_rate = sample_rate * channels * bits_per_sample // 8
                    block_align = channels * bits_per_sample // 8
                    f.write((byte_rate).to_bytes(4, byteorder='little'))
                    f.write((block_align).to_bytes(2, byteorder='little'))
                    f.write((bits_per_sample).to_bytes(2, byteorder='little'))
                    
                    # Data chunk
                    f.write(b'data')
                    f.write((data_size).to_bytes(4, byteorder='little'))
                    
                    # Write silence (all zeros)
                    f.write(b'\x00' * data_size)
                
                logger.info(f"Successfully created minimal WAV file: {os.path.getsize(self.output_path)} bytes")
                return True
            except Exception as e:
                logger.error(f"Failed to create minimal WAV file: {e}")
                return False
    
    def get_audio_file_path(self):
        """
        Get the path to the current audio file
        
        Returns:
            str: Path to the current audio file
        """
        return self.output_path 