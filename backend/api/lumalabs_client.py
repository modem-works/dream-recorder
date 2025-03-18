"""
LumaLabs Client for Dream Recorder
Handles video generation using LumaLabs API and video downloading
"""

import os
import logging
import time
import requests
import json
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class LumaLabsClient:
    """Client for interacting with LumaLabs API"""
    
    # Updated API URL based on the latest documentation
    API_BASE_URL = "https://api.lumalabs.ai/dream-machine/v1"
    
    def __init__(self, api_key=None):
        """
        Initialize the LumaLabs client
        
        Args:
            api_key: LumaLabs API key (defaults to LUMALABS_API_KEY environment variable)
        """
        self.api_key = api_key or os.environ.get('LUMALABS_API_KEY')
        if not self.api_key:
            logger.warning("LumaLabs API key not provided")
        else:
            logger.info("LumaLabs client initialized")
        
        # Create directory for storing videos if it doesn't exist
        self.video_dir = Path('data/videos')
        self.video_dir.mkdir(parents=True, exist_ok=True)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_video(self, prompt):
        """
        Generate a video using LumaLabs API
        
        Args:
            prompt: Text prompt for video generation
            
        Returns:
            str: URL of the generated video or None if unsuccessful
        """
        if not self.api_key:
            logger.error("LumaLabs API key not configured")
            return None
        
        try:
            logger.info(f"Generating video with prompt: {prompt[:50]}...")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Updated payload based on the latest API documentation
            payload = {
                "prompt": prompt,
                "model": "ray-2",
                "resolution": "540p",
                "duration": "5s"
            }
            
            logger.info(f"Sending request to {self.API_BASE_URL}/generations")
            
            response = requests.post(
                f"{self.API_BASE_URL}/generations",
                headers=headers,
                json=payload
            )
            
            # Status 201 Created is a success response, indicating the generation was created
            if response.status_code not in [200, 201]:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return None
                
            # Parse the response
            try:
                response_data = response.json()
                logger.info(f"API response: {json.dumps(response_data, indent=2)}")
                
                # Extract generation ID and poll for completion
                generation_id = response_data.get("id")
                
                if not generation_id:
                    logger.error("Failed to get generation ID from response")
                    return None
                
                logger.info(f"Video generation started with ID: {generation_id}")
                
                # Poll for completion
                video_url = self._poll_generation_status(generation_id)
                return video_url
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse API response: {response.text}")
                return None
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            return None
    
    def _poll_generation_status(self, generation_id, max_attempts=60, poll_interval=5):
        """
        Poll the generation status until the video is ready
        
        Args:
            generation_id: Generation ID to poll
            max_attempts: Maximum number of polling attempts
            poll_interval: Interval between polling attempts in seconds
            
        Returns:
            str: Video URL if successful, None otherwise
        """
        logger.info(f"Polling generation status for ID: {generation_id}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        for attempt in range(max_attempts):
            try:
                # Updated endpoint for status checking
                response = requests.get(
                    f"{self.API_BASE_URL}/generations/{generation_id}",
                    headers=headers
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"Status check failed with code {response.status_code}: {response.text}")
                    time.sleep(poll_interval)
                    continue
                
                status_data = response.json()
                
                # Log the full response for debugging
                if attempt == 0 or attempt % 10 == 0:
                    logger.info(f"Full status response: {json.dumps(status_data, indent=2)}")
                
                # The API uses 'state' instead of 'status'
                state = status_data.get("state")
                logger.info(f"Generation state: {state} (attempt {attempt+1}/{max_attempts})")
                
                if state == "completed" or state == "succeeded":
                    # Try to extract the video URL from the assets field
                    assets = status_data.get("assets") or {}
                    
                    # Check if assets is a dictionary with a video URL
                    video_url = None
                    if isinstance(assets, dict):
                        # Try different possible locations for the video URL
                        video_url = (assets.get("video") or 
                                    assets.get("url") or 
                                    (assets.get("videos", {}) or {}).get("url"))
                    
                    # Also check the result field for backward compatibility
                    if not video_url and "result" in status_data:
                        result = status_data.get("result", {})
                        if isinstance(result, dict):
                            video_url = result.get("url")
                    
                    if not video_url:
                        logger.error("Video URL not found in completed response")
                        logger.error(f"Response structure: {json.dumps(status_data, indent=2)}")
                        return None
                        
                    logger.info(f"Video generation completed: {video_url}")
                    return video_url
                    
                elif state == "failed" or state == "error":
                    error_msg = status_data.get("failure_reason") or status_data.get("error") or "Unknown error"
                    logger.error(f"Video generation failed: {error_msg}")
                    return None
                
                # If state is processing, pending, queued, or another intermediate state, continue polling
                
                # Wait before next poll
                time.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error polling generation status: {e}")
                time.sleep(poll_interval)
        
        logger.error(f"Timed out waiting for video generation after {max_attempts} attempts")
        return None
    
    def download_video(self, video_url):
        """
        Download a video from the provided URL
        
        Args:
            video_url: URL of the video to download
            
        Returns:
            str: Path to the downloaded video file
        """
        if not video_url:
            logger.error("No video URL provided")
            return None
        
        try:
            logger.info(f"Downloading video from: {video_url}")
            
            # Generate a filename based on timestamp
            timestamp = int(time.time())
            video_path = self.video_dir / f"dream_video_{timestamp}.mp4"
            
            # Download the video
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded to: {video_path}")
            return str(video_path)
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None 