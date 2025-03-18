"""
OpenAI Client for Dream Recorder
Handles audio transcription and prompt enhancement using OpenAI APIs
"""

import os
import logging
import tempfile
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for interacting with OpenAI APIs"""
    
    def __init__(self, api_key=None):
        """
        Initialize the OpenAI client
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
            self.client = None
            return
        
        # Set the API key for the openai module
        openai.api_key = self.api_key
        self.client = openai
        logger.info("OpenAI client initialized with v0.28.1 API")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file using OpenAI Whisper API
        
        Args:
            audio_file_path: Path to the audio file to transcribe
            
        Returns:
            str: Transcribed text
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return "Error: OpenAI API key not configured"
        
        try:
            logger.info(f"Transcribing audio file: {audio_file_path}")
            
            with open(audio_file_path, "rb") as audio_file:
                # Using v0.28.1 API for transcription
                transcription = self.client.Audio.transcribe("whisper-1", audio_file)
            
            logger.info("Audio transcription complete")
            return transcription["text"]
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return f"Error transcribing audio: {str(e)}"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def enhance_prompt(self, transcription):
        """
        Enhance the transcribed dream into a better prompt for video generation
        
        Args:
            transcription: Transcribed text of the dream
            
        Returns:
            str: Enhanced prompt for video generation
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return "Error: OpenAI API key not configured"
        
        try:
            logger.info("Enhancing prompt for video generation")
            
            system_prompt = """
            You are a creative dream interpreter who converts dream descriptions into vivid, 
            detailed prompts for video generation. Take the user's dream description and transform 
            it into a prompt that will create a visually stunning and meaningful video representation. 
            Focus on visual elements, mood, colors, and composition. Be specific and descriptive.
            
            Guidelines:
            - Be highly detailed and visual
            - Use evocative language
            - Maintain the core essence of the original dream
            - Focus on imagery that would work well in a video
            - Include camera movements, transitions, or scene changes if appropriate
            - Keep the prompt length to 100-150 words
            
            Return ONLY the enhanced prompt, nothing else.
            """
            
            # Using v0.28.1 API for chat completion
            response = self.client.ChatCompletion.create(
                model="gpt-4",  # Changed from gpt-4-turbo which might not be available in older API
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcription}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            enhanced_prompt = response["choices"][0]["message"]["content"].strip()
            logger.info("Prompt enhancement complete")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing prompt: {e}")
            return f"Error enhancing prompt: {str(e)}" 