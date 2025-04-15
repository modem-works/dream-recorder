import os
from PIL import Image
import shutil

def resize_and_save_image(input_path, output_path, target_size=(1280, 400)):
    """Resize an image and save it to the output path."""
    print(f"Processing image: {input_path}")
    with Image.open(input_path) as img:
        resized = img.resize(target_size, Image.Resampling.LANCZOS)
        resized.save(output_path, 'PNG', quality=95)
        print(f"Saved to: {output_path}")

def process_sequence(input_dir, output_dir, input_prefix, output_prefix, start_num=0, end_num=150):
    """Process a sequence of images from start_num to end_num."""
    print(f"\nProcessing sequence: {input_dir}")
    print(f"Looking for files in: {os.path.abspath(input_dir)}")
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory does not exist: {input_dir}")
        return
        
    # List contents of input directory
    print("Contents of input directory:")
    for item in os.listdir(input_dir):
        print(f"  - {item}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(start_num, end_num + 1):
        # Use the correct prefix for input files
        input_filename = f"ICON-{input_prefix}_{i:05d}.png"
        output_filename = f"{output_prefix}-{i:03d}.png"
        
        input_path = os.path.join(input_dir, input_filename)
        output_path = os.path.join(output_dir, output_filename)
        
        if os.path.exists(input_path):
            resize_and_save_image(input_path, output_path)
            print(f"Processed: {input_filename} -> {output_filename}")
        else:
            print(f"File not found: {input_path}")

def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")
    
    # Create output directory
    output_base = os.path.join(script_dir, "static/images/icons")
    print(f"Output base directory: {output_base}")
    os.makedirs(output_base, exist_ok=True)
    
    # Process each sequence with correct prefixes
    sequences = [
        ("LISTEN", "rec", "LISTEN", 0, 150),
        ("GEN", "gen", "GEN", 0, 150),
        ("ERRORSTATE", "error", "ERROR", 0, 71)
    ]
    
    for input_dir, output_prefix, input_prefix, start, end in sequences:
        # Use absolute path for input directory
        input_dir_abs = os.path.join(script_dir, input_dir)
        output_dir = os.path.join(output_base, output_prefix)
        process_sequence(input_dir_abs, output_dir, input_prefix, output_prefix, start, end)

if __name__ == "__main__":
    main()
