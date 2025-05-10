import os
import sys
import shutil

# Ensure parent directory is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from functions.dream_db import DreamDB, DreamData

# Paths
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'dream_samples')
VIDEO_DEST = os.path.join(os.path.dirname(__file__), '..', 'media', 'video')
THUMB_DEST = os.path.join(os.path.dirname(__file__), '..', 'media', 'thumbs')

# Sample files and DB records
SAMPLES = [
    {'video': 'video_1.mp4', 'thumb': 'thumb_1.png', 'video_dest': 'dream_1.mp4', 'thumb_dest': 'dream_1.png'},
    {'video': 'video_2.mp4', 'thumb': 'thumb_2.png', 'video_dest': 'dream_2.mp4', 'thumb_dest': 'dream_2.png'},
    {'video': 'video_3.mp4', 'thumb': 'thumb_3.png', 'video_dest': 'dream_3.mp4', 'thumb_dest': 'dream_3.png'},
    {'video': 'video_4.mp4', 'thumb': 'thumb_4.png', 'video_dest': 'dream_4.mp4', 'thumb_dest': 'dream_4.png'},
]

def main():
    db = DreamDB()
    existing = db.get_all_dreams()
    existing_videos = {d['video_filename'] for d in existing}

    for i, sample in enumerate(SAMPLES, 1):
        # Copy video
        src_video = os.path.join(SAMPLES_DIR, sample['video'])
        dst_video = os.path.join(VIDEO_DEST, sample['video_dest'])
        if not os.path.exists(dst_video):
            shutil.copy2(src_video, dst_video)

        # Copy thumb
        src_thumb = os.path.join(SAMPLES_DIR, sample['thumb'])
        dst_thumb = os.path.join(THUMB_DEST, sample['thumb_dest'])
        if not os.path.exists(dst_thumb):
            shutil.copy2(src_thumb, dst_thumb)

        # Insert into DB if not present
        if sample['video_dest'] not in existing_videos:
            dream_data = DreamData(
                user_prompt='',
                generated_prompt='',
                audio_filename='',
                video_filename=sample['video_dest'],
                thumb_filename=sample['thumb_dest'],
                status='completed',
            )
            db.save_dream(dream_data.model_dump())
            print(f"Inserted sample dream {i}")
        else:
            print(f"Sample dream {i} already exists in DB")

if __name__ == '__main__':
    main() 