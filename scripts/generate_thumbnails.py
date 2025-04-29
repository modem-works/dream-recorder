import os
from dotenv import load_dotenv
from dream_db import DreamDB
from app import process_thumbnail
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

def generate_thumbnails_for_existing_videos():
    """Generate thumbnails for all existing videos in the database."""
    try:
        # Initialize database connection
        dream_db = DreamDB()
        
        # Get all dreams
        dreams = dream_db.get_all_dreams()
        logger.info(f"Found {len(dreams)} dreams in the database")
        
        # Verify environment variables
        videos_dir = os.getenv('VIDEOS_DIR')
        thumbs_dir = os.getenv('THUMBS_DIR')
        logger.info(f"Videos directory: {videos_dir}")
        logger.info(f"Thumbs directory: {thumbs_dir}")
        
        # Verify directories exist
        if not os.path.exists(videos_dir):
            logger.error(f"Videos directory does not exist: {videos_dir}")
            return
        if not os.path.exists(thumbs_dir):
            logger.info(f"Creating thumbs directory: {thumbs_dir}")
            os.makedirs(thumbs_dir, exist_ok=True)
        
        # Process each dream
        for dream in dreams:
            try:
                # Skip if video filename is not available
                if not dream.get('video_filename'):
                    logger.warning(f"Skipping dream {dream.get('id')} - no video filename")
                    continue
                
                # Skip if thumbnail already exists
                if dream.get('thumb_filename'):
                    logger.info(f"Skipping dream {dream.get('id')} - thumbnail already exists")
                    continue
                
                # Construct video path
                video_path = os.path.join(videos_dir, dream['video_filename'])
                
                # Check if video file exists
                if not os.path.exists(video_path):
                    logger.warning(f"Video file not found: {video_path}")
                    continue
                
                # Verify video file is readable
                if not os.access(video_path, os.R_OK):
                    logger.error(f"Video file is not readable: {video_path}")
                    continue
                
                # Get file size
                file_size = os.path.getsize(video_path)
                logger.info(f"Processing video: {video_path} (size: {file_size} bytes)")
                
                # Generate thumbnail
                logger.info(f"Generating thumbnail for dream {dream.get('id')}")
                thumb_filename = process_thumbnail(video_path)
                
                # Update database with thumbnail filename
                if thumb_filename:
                    dream_db.update_dream(dream['id'], {'thumb_filename': thumb_filename})
                    logger.info(f"Updated dream {dream.get('id')} with thumbnail {thumb_filename}")
                else:
                    logger.error(f"Failed to generate thumbnail for dream {dream.get('id')}")
                
            except Exception as e:
                logger.error(f"Error processing dream {dream.get('id')}: {str(e)}")
                continue
        
        logger.info("Thumbnail generation completed")
        
    except Exception as e:
        logger.error(f"Error in thumbnail generation process: {str(e)}")
        raise

if __name__ == '__main__':
    generate_thumbnails_for_existing_videos() 