#!/usr/bin/env python3
"""
Script to resize background images from 1024x1024 to 512x512 pixels.
Converts BG1.png through BG12.png
"""

from PIL import Image
import os

def resize_backgrounds():
    """Resize BG1.png through BG12.png from 1024x1024 to 512x512"""
    
    # Define the target size
    target_size = (512, 512)
    
    # Define the directory containing the background images
    bg_dir = "img/bg"
    
    # Loop through BG1.png to BG12.png
    for i in range(1, 13):
        filename = os.path.join(bg_dir, f"BG{i}.png")
        
        # Check if file exists
        if not os.path.exists(filename):
            print(f"Warning: {filename} not found, skipping...")
            continue
        
        try:
            # Open the image
            img = Image.open(filename)
            
            # Get original size
            original_size = img.size
            print(f"Processing {filename}: {original_size[0]}x{original_size[1]} -> {target_size[0]}x{target_size[1]}")
            
            # Resize the image using high-quality Lanczos resampling
            resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # Save the resized image (overwrites original)
            resized_img.save(filename)
            print(f"✓ Successfully resized {filename}")
            
        except Exception as e:
            print(f"✗ Error processing {filename}: {e}")
    
    print("\nResize operation complete!")

if __name__ == "__main__":
    resize_backgrounds()
