"""
Video Processor for Dream Recorder
Handles post-processing of videos using FFmpeg
"""

import os
import logging
import subprocess
import tempfile
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Processes videos using FFmpeg"""
    
    def __init__(self, output_dir=None):
        """
        Initialize the video processor
        
        Args:
            output_dir: Directory for processed video output (defaults to data/processed_videos)
        """
        self.output_dir = Path(output_dir) if output_dir else Path('data/processed_videos')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if FFmpeg is installed
        try:
            subprocess.run(['ffmpeg', '-version'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=True)
            logger.info("FFmpeg found and working")
            self.ffmpeg_available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("FFmpeg not found or not working")
            self.ffmpeg_available = False
    
    def process_video(self, video_path, processing_type='enhance'):
        """
        Process a video using FFmpeg
        
        Args:
            video_path: Path to the input video file
            processing_type: Type of processing to apply (enhance, stylize, etc.)
            
        Returns:
            str: Path to the processed video file
        """
        if not self.ffmpeg_available:
            logger.error("FFmpeg not available, returning original video")
            return video_path
        
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return None
            
            # Generate output filename
            timestamp = int(time.time())
            output_filename = f"processed_{video_path.stem}_{timestamp}.mp4"
            output_path = self.output_dir / output_filename
            
            logger.info(f"Processing video: {video_path} -> {output_path}")
            
            # Apply processing based on type
            if processing_type == 'enhance':
                self._enhance_video(video_path, output_path)
            elif processing_type == 'stylize':
                self._stylize_video(video_path, output_path)
            else:
                logger.warning(f"Unknown processing type: {processing_type}, using enhance instead")
                self._enhance_video(video_path, output_path)
            
            # Check if output file was created
            if not output_path.exists():
                logger.error("Processing failed, output file not created")
                return str(video_path)  # Return original video path
            
            logger.info(f"Video processing complete: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return str(video_path)  # Return original video path
    
    def _enhance_video(self, input_path, output_path):
        """
        Enhance video quality and colors
        
        Args:
            input_path: Path to input video
            output_path: Path for output video
        """
        try:
            # Command to enhance video quality and colors
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vf', 'eq=brightness=0.05:saturation=1.3:gamma=1.1,unsharp=5:5:1.0:5:5:0.0',
                '-c:v', 'libx264',
                '-preset', 'slow',
                '-crf', '18',
                '-c:a', 'aac',
                '-b:a', '192k',
                str(output_path)
            ]
            
            subprocess.run(cmd, check=True, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
            
        except subprocess.SubprocessError as e:
            logger.error(f"FFmpeg enhance error: {e}")
            raise
    
    def _stylize_video(self, input_path, output_path):
        """
        Apply artistic style to video
        
        Args:
            input_path: Path to input video
            output_path: Path for output video
        """
        try:
            # Command to apply a dreamy/surreal style
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vf', 'eq=brightness=0.1:saturation=1.5:contrast=1.1,hue=h=0.1,gblur=sigma=0.8:steps=1',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '20',
                '-c:a', 'aac',
                '-b:a', '192k',
                str(output_path)
            ]
            
            subprocess.run(cmd, check=True, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
            
        except subprocess.SubprocessError as e:
            logger.error(f"FFmpeg stylize error: {e}")
            raise
    
    def create_preview(self, video_path, duration=10):
        """
        Create a short preview from the video
        
        Args:
            video_path: Path to the input video
            duration: Duration of the preview in seconds
            
        Returns:
            str: Path to the preview video
        """
        if not self.ffmpeg_available:
            logger.error("FFmpeg not available, cannot create preview")
            return video_path
        
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return None
            
            # Generate output filename
            preview_path = self.output_dir / f"preview_{video_path.stem}.mp4"
            
            # Create a short preview
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-t', str(duration),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:a', '128k',
                str(preview_path)
            ]
            
            subprocess.run(cmd, check=True, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
            
            logger.info(f"Preview created: {preview_path}")
            return str(preview_path)
            
        except Exception as e:
            logger.error(f"Error creating preview: {e}")
            return str(video_path) 