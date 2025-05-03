import tempfile
import requests
import time
import os
import ffmpeg
import shutil
from datetime import datetime
from config_loader import load_config

config = load_config()

def process_video(input_path, logger=None):
    """Process the video using FFmpeg with specific filters from environment variables."""
    try:
        # Create a temporary file for the processed video
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
        # Apply FFmpeg filters using environment variables
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.filter(stream, 'eq', brightness=float(config['FFMPEG_BRIGHTNESS']))
        stream = ffmpeg.filter(stream, 'vibrance', intensity=float(config['FFMPEG_VIBRANCE']))
        stream = ffmpeg.filter(stream, 'vaguedenoiser', threshold=float(config['FFMPEG_DENOISE_THRESHOLD']))
        stream = ffmpeg.filter(stream, 'bilateral', sigmaS=float(config['FFMPEG_BILATERAL_SIGMA']))
        stream = ffmpeg.filter(stream, 'noise', all_strength=float(config['FFMPEG_NOISE_STRENGTH']))
        stream = ffmpeg.output(stream, temp_path)
        # Run FFmpeg
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        # Replace the original file with the processed one
        shutil.move(temp_path, input_path)
        if logger:
            logger.info(f"Processed video saved to {input_path}")
        return input_path
    except Exception as e:
        if logger:
            logger.error(f"Error processing video: {str(e)}")
        raise

def process_thumbnail(video_path, logger=None):
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
        thumbs_dir = config['THUMBS_DIR']
        os.makedirs(thumbs_dir, exist_ok=True)
        # Generate simple timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        thumb_filename = f"thumb_{timestamp}.png"
        thumb_path = os.path.join(thumbs_dir, thumb_filename)
        # Log the FFmpeg command for debugging
        if logger:
            logger.info(f"Generating thumbnail for video: {video_path}")
            logger.info(f"Video dimensions: {width}x{height}")
            logger.info(f"Output path: {thumb_path}")
            logger.info(f"Crop dimensions: {crop_size}x{crop_size} at offset ({x_offset}, {y_offset})")
        # Use FFmpeg to extract frame at 1 second and crop to square
        stream = ffmpeg.input(video_path, ss=1)
        stream = ffmpeg.filter(stream, 'crop', crop_size, crop_size, x_offset, y_offset)
        stream = ffmpeg.output(stream, thumb_path, vframes=1)
        # Run FFmpeg with stderr capture
        try:
            ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
        except ffmpeg.Error as e:
            if logger:
                logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
        if logger:
            logger.info(f"Generated thumbnail saved to {thumb_path}")
        return thumb_filename
    except Exception as e:
        if logger:
            logger.error(f"Error generating thumbnail: {str(e)}")
        raise

def generate_video_prompt(transcription, luma_extend=False, client=None, logger=None, config=config):
    """Generate an enhanced video prompt from the transcription using GPT."""
    try:
        system_prompt = config['GPT_SYSTEM_PROMPT_EXTEND'] if luma_extend else config['GPT_SYSTEM_PROMPT']
        response = client.chat.completions.create(
            model=config['GPT_MODEL'],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{transcription}"}
            ],
            temperature=float(config['GPT_TEMPERATURE']),
            max_tokens=int(config['GPT_MAX_TOKENS'])
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        if logger:
            logger.error(f"Error generating video prompt: {str(e)}")
        return None

def generate_video(prompt, filename=None, luma_extend=False, logger=None, config=config):
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
            config['LUMA_GENERATIONS_ENDPOINT'],
            headers={
                'accept': 'application/json',
                'authorization': f"Bearer {config['LUMALABS_API_KEY']}",
                'content-type': 'application/json'
            },
            json={
                'prompt': initial_prompt,
                'model': config['LUMA_MODEL'],
                'resolution': config['LUMA_RESOLUTION'],
                'duration': config['LUMA_DURATION'],
                "aspect_ratio": config['LUMA_ASPECT_RATIO'],
            }
        )
        if response.status_code not in [200, 201]:
            raise Exception(f"Luma API error: {response.text}")
        response_data = response.json()
        if logger:
            logger.info(f"API response: {response_data}")
        generation_id = response_data.get('id')
        if not generation_id:
            raise Exception("Failed to get generation ID from response")
        if logger:
            logger.info(f"Started video generation with ID: {generation_id}")
        def poll_for_completion(generation_id):
            """Poll the Luma API for video generation completion."""
            max_attempts = int(config['LUMA_MAX_POLL_ATTEMPTS'])
            poll_interval = float(config['LUMA_POLL_INTERVAL'])
            for attempt in range(max_attempts):
                status_response = requests.get(
                    f"{config['LUMA_API_URL']}/generations/{generation_id}",
                    headers={
                        'accept': 'application/json',
                        'authorization': f"Bearer {config['LUMALABS_API_KEY']}"
                    }
                )
                if status_response.status_code not in [200, 201]:
                    if logger:
                        logger.error(f"Status check failed with code {status_response.status_code}: {status_response.text}")
                    time.sleep(poll_interval)
                    continue
                status_data = status_response.json()
                if attempt == 0 or attempt % 10 == 0:
                    if logger:
                        logger.info(f"Full status response: {status_data}")
                state = status_data.get('state')
                if logger:
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
                    if logger:
                        logger.info(f"Video generation completed: {video_url}")
                    return video_url
                elif state in ['failed', 'error']:
                    error_msg = status_data.get('failure_reason') or status_data.get('error') or "Unknown error"
                    raise Exception(f"Video generation failed: {error_msg}")
                time.sleep(poll_interval)
            raise Exception(f"Timed out waiting for video generation after {max_attempts} attempts")
        # Step 2: If luma_extend is set, extend the video
        if luma_extend:
            if logger:
                logger.info("LUMA_EXTEND is set. Requesting video extension.")
            _ = poll_for_completion(generation_id)  # Wait for completion
            extend_response = requests.post(
                config['LUMA_GENERATIONS_ENDPOINT'],
                headers={
                    'accept': 'application/json',
                    'authorization': f"Bearer {config['LUMALABS_API_KEY']}",
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
            if logger:
                logger.info(f"Extend API response: {extend_data}")
            extend_id = extend_data.get('id')
            if not extend_id:
                raise Exception("Failed to get extend generation ID from response")
            if logger:
                logger.info(f"Started video extension with ID: {extend_id}")
            video_url = poll_for_completion(extend_id)
        else:
            video_url = poll_for_completion(generation_id)
        # Download the generated video
        video_response = requests.get(video_url, stream=True)
        video_response.raise_for_status()
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.mp4"
        os.makedirs(config['VIDEOS_DIR'], exist_ok=True)
        video_path = os.path.join(config['VIDEOS_DIR'], filename)
        with open(video_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)
        if logger:
            logger.info(f"Saved video to {video_path}")
        # Post-process the video and generate a thumbnail
        processed_video_path = process_video(video_path, logger)
        if logger:
            logger.info(f"Processed video saved to {processed_video_path}")
        thumb_filename = process_thumbnail(processed_video_path, logger)
        return filename, thumb_filename
    except Exception as e:
        if logger:
            logger.error(f"Error generating video: {str(e)}")
        raise
