#!/usr/bin/env python3
"""
Script to resize ALL game images by half (50%) for 240x240 base resolution.
Handles PNG, JPG, and animated GIF files.
Creates backups before modifying originals.
"""

from PIL import Image
import os
import shutil

def create_backup(img_dir):
    """Create a backup of the img directory"""
    backup_dir = img_dir + "_backup"
    
    if os.path.exists(backup_dir):
        print(f"Backup already exists at {backup_dir}")
        response = input("Overwrite existing backup? (y/n): ")
        if response.lower() != 'y':
            print("Skipping backup creation")
            return False
        shutil.rmtree(backup_dir)
    
    print(f"Creating backup at {backup_dir}...")
    shutil.copytree(img_dir, backup_dir)
    print("✓ Backup created successfully!")
    return True

def resize_static_image(filepath, scale_factor=0.5):
    """Resize a static image (PNG, JPG) by scale_factor"""
    try:
        img = Image.open(filepath)
        original_size = img.size
        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
        
        # Use LANCZOS for high-quality downsampling
        resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
        resized_img.save(filepath)
        
        print(f"  ✓ {os.path.basename(filepath)}: {original_size[0]}x{original_size[1]} -> {new_size[0]}x{new_size[1]}")
        return True
    except Exception as e:
        print(f"  ✗ Error resizing {filepath}: {e}")
        return False

def resize_animated_gif(filepath, scale_factor=0.5):
    """Resize an animated GIF by resizing each frame while preserving transparency"""
    try:
        gif = Image.open(filepath)
        original_size = gif.size
        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
        
        frames = []
        durations = []
        
        # Extract all frames
        try:
            frame_index = 0
            while True:
                # Get frame duration (default to 100ms if not specified)
                duration = gif.info.get('duration', 100)
                durations.append(duration)
                
                # Convert frame to RGBA to preserve transparency
                frame = gif.copy().convert('RGBA')
                
                # Resize frame with high-quality resampling
                resized_frame = frame.resize(new_size, Image.Resampling.LANCZOS)
                frames.append(resized_frame)
                
                # Move to next frame
                frame_index += 1
                gif.seek(frame_index)
        except EOFError:
            pass  # End of frames
        
        # Save resized GIF with transparency preserved
        if frames:
            # Convert RGBA frames to P mode with transparency using PIL's quantize
            frames_p = []
            
            for frame in frames:
                # Use PIL's quantize method which properly handles alpha
                # Method 2 (FASTOCTREE) for RGBA images
                frame_p = frame.quantize(method=2, colors=256, dither=1)
                frames_p.append(frame_p)
            
            # Save with proper transparency settings
            # Get the transparency info from the quantized frames
            frames_p[0].save(
                filepath,
                save_all=True,
                append_images=frames_p[1:],
                duration=durations,
                loop=gif.info.get('loop', 0),
                disposal=2,  # Clear frame (dispose to background) before rendering next
                optimize=False
            )
            print(f"  ✓ {os.path.basename(filepath)}: {original_size[0]}x{original_size[1]} -> {new_size[0]}x{new_size[1]} ({len(frames)} frames)")
            return True
        else:
            print(f"  ✗ No frames found in {filepath}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error resizing animated GIF {filepath}: {e}")
        return False

def resize_all_images(img_dir, scale_factor=0.5, create_backup_first=True, folders_to_process=None):
    """Resize all images in the img directory by scale_factor
    
    Args:
        img_dir: Path to img directory
        scale_factor: Scale factor (0.5 = 50%)
        create_backup_first: Whether to create backup
        folders_to_process: List of folder names to process (e.g., ['bg', 'intro', 'outro'])
                          If None, processes all folders
    """
    
    if not os.path.exists(img_dir):
        print(f"Error: Directory {img_dir} not found!")
        return
    
    # Create backup
    if create_backup_first:
        if not create_backup(img_dir):
            response = input("Continue without backup? (y/n): ")
            if response.lower() != 'y':
                print("Operation cancelled")
                return
    
    print(f"\nResizing images to {int(scale_factor * 100)}% of original size...")
    if folders_to_process:
        print(f"Processing only folders: {', '.join(folders_to_process)}")
    else:
        print("Processing all folders")
    print("=" * 60)
    
    total_files = 0
    success_files = 0
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(img_dir):
        if files:
            rel_path = os.path.relpath(root, img_dir)
            
            # Skip if we're filtering folders and this isn't in the list
            if folders_to_process is not None:
                # Get the top-level folder name
                folder_name = rel_path.split(os.sep)[0] if rel_path != '.' else '.'
                if folder_name not in folders_to_process:
                    continue  # Skip this folder
            
            print(f"\nProcessing: {rel_path if rel_path != '.' else 'img/'}")
            
            for filename in sorted(files):
                filepath = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                
                # Skip non-image files
                if ext not in ['.png', '.jpg', '.jpeg', '.gif']:
                    continue
                
                total_files += 1
                
                # Handle GIF separately (animated)
                if ext == '.gif':
                    if resize_animated_gif(filepath, scale_factor):
                        success_files += 1
                else:
                    if resize_static_image(filepath, scale_factor):
                        success_files += 1
    
    print("\n" + "=" * 60)
    print(f"Resize operation complete!")
    print(f"Successfully resized: {success_files}/{total_files} files")
    
    if success_files < total_files:
        print(f"Failed: {total_files - success_files} files")

def main():
    """Main function"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(script_dir, 'img')
    
    print("=" * 60)
    print("Image Resizer for 240x240 Base Resolution")
    print("=" * 60)
    print("\nThis script will resize images in SPECIFIC FOLDERS ONLY:")
    print("  - bg/")
    print("  - Intro/")
    print("  - outro/")
    print("\nAll images will be resized by 50% (480x480 -> 240x240, etc.)")
    print("\nA backup will be created at img_backup/ before resizing.")
    print("\nPress Ctrl+C to cancel at any time.")
    print("=" * 60)
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled")
        return
    
    # Only process bg, Intro, and outro folders
    folders_to_process = ['bg', 'Intro', 'outro']
    resize_all_images(img_dir, scale_factor=0.5, create_backup_first=True, folders_to_process=folders_to_process)
    
    print("\n" + "=" * 60)
    print("IMPORTANT: Test the game after resizing!")
    print("If anything looks wrong, restore from img_backup/")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
