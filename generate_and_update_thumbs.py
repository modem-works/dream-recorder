import os
import sqlite3
import subprocess
from datetime import datetime

def generate_thumbnail(video_path, output_path):
    try:
        # Create the thumbnails directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate thumbnail using ffmpeg
        # First get video dimensions
        probe_cmd = [
            'ffprobe', 
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            video_path
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        if probe_result.returncode != 0:
            print(f"Error probing video dimensions for {video_path}:")
            print(probe_result.stderr)
            return False
            
        width, height = map(int, probe_result.stdout.strip().split(','))
        
        # Calculate crop dimensions
        if width > height:
            crop_size = height
            x_offset = (width - height) // 2
            y_offset = 0
        else:
            crop_size = width
            x_offset = 0
            y_offset = (height - width) // 2
            
        # Generate thumbnail with center crop
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ss', '00:00:01',  # Take frame at 1 second
            '-vframes', '1',
            '-vf', f'crop={crop_size}:{crop_size}:{x_offset}:{y_offset},scale=540:540',
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error generating thumbnail for {video_path}:")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"Exception generating thumbnail for {video_path}: {str(e)}")
        return False

def update_database():
    # Connect to the database
    conn = sqlite3.connect('dreams.db')
    cursor = conn.cursor()
    
    # Get all dreams that need thumbnails
    cursor.execute("SELECT id, video_filename FROM dreams")  # Changed to regenerate all thumbnails
    dreams = cursor.fetchall()
    
    for dream_id, video_filename in dreams:
        if not video_filename:
            continue
            
        video_path = os.path.join('media/video', video_filename)
        thumb_filename = f"thumb_{video_filename.replace('.mp4', '.jpg')}"
        thumb_path = os.path.join('media/thumbs', thumb_filename)
        
        if os.path.exists(video_path):
            print(f"Generating thumbnail for dream {dream_id}: {video_filename}")
            if generate_thumbnail(video_path, thumb_path):
                # Update the database with the thumbnail filename
                cursor.execute(
                    "UPDATE dreams SET thumb_filename = ? WHERE id = ?",
                    (thumb_filename, dream_id)
                )
                print(f"Updated database with thumbnail: {thumb_filename}")
            else:
                print(f"Failed to generate thumbnail for {video_filename}")
        else:
            print(f"Video file not found: {video_path}")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Starting thumbnail generation and database update...")
    update_database()
    print("Thumbnail generation and database update completed.") 