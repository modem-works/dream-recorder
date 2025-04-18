import os
import shutil
from pathlib import Path

def reorganize_backgrounds():
    # Define the source and destination directories
    source_dir = Path('static/images/backgrounds')
    dest_dir = Path('static/images/backgrounds_renamed')
    
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(exist_ok=True)
    
    # Define the order of folders to process
    folders = ['0000-0559', '0600-1159', '1200-1759', '1800-2359']
    
    # Counter for new filenames
    counter = 0
    
    # Process each folder in order
    for folder in folders:
        folder_path = source_dir / folder
        if not folder_path.exists():
            print(f"Warning: Folder {folder} does not exist")
            continue
            
        # Get all jpg files in the folder and sort them numerically
        files = sorted(
            [f for f in folder_path.glob('*.jpg')],
            key=lambda x: int(x.stem.split('-')[-1])
        )
        
        # Copy and rename each file
        for file in files:
            new_name = f"{counter}.jpg"
            shutil.copy2(file, dest_dir / new_name)
            print(f"Copied {file} to {new_name}")
            counter += 1
    
    # Write the total number of images to .env
    with open('.env', 'a') as f:
        f.write(f"\nTOTAL_BACKGROUND_IMAGES={counter}\n")
    
    print(f"\nProcessed {counter} images in total")
    print(f"New images are in {dest_dir}")
    print("Added TOTAL_BACKGROUND_IMAGES to .env file")

if __name__ == "__main__":
    reorganize_backgrounds() 