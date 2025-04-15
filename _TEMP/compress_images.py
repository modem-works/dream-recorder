import os
from PIL import Image

def convert_png_to_jpg(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.png'):
            # Construct full file path
            file_path = os.path.join(directory, filename)
            # Open the PNG image
            with Image.open(file_path) as img:
                # Convert the image to RGB (as JPEG does not support alpha channel)
                rgb_image = img.convert('RGB')
                
                # Define the new filename with .jpg extension
                new_file_name = filename.rsplit('.', 1)[0] + '.jpg'
                new_file_path = os.path.join(directory, new_file_name)
                
                # Save the image with quality parameter (where 85 is moderately compressed)
                rgb_image.save(new_file_path, 'JPEG', quality=85)
                
                print(f'Converted {filename} to {new_file_name} with compression.')

# Call the function on the current directory
current_directory = os.getcwd()
convert_png_to_jpg(current_directory)
