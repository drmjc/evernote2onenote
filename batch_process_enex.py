#!/usr/bin/env python3

import os
import sys
import argparse
import tempfile
import shutil
import subprocess
from datetime import datetime

def create_temp_dir(prefix="enex_conversion_"):
    """Create a temporary directory with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = os.path.join(tempfile.gettempdir(), f"{prefix}{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def process_single_enex(enex_file, temp_dir, convert_script, import_script, archive_dir=None):
    """Process a single enex file: convert to HTML and import to OneNote."""
    print(f"\nProcessing: {enex_file}")
    
    # Create a unique subdirectory for this enex file
    file_basename = os.path.splitext(os.path.basename(enex_file))[0]
    work_dir = os.path.join(temp_dir, file_basename)
    os.makedirs(work_dir, exist_ok=True)
    
    # Copy enex file to work directory
    enex_copy = os.path.join(work_dir, os.path.basename(enex_file))
    shutil.copy2(enex_file, enex_copy)
    
    try:
        # Convert enex to HTML
        print(f"Converting {enex_file} to HTML...")
        convert_result = subprocess.run(
            [sys.executable, convert_script, enex_copy, '--output_dir', work_dir],
            check=True
        )
        
        # Import HTML files to OneNote
        print(f"Importing HTML files to OneNote...")
        import_cmd = [sys.executable, import_script, '--html_dir', work_dir, '--clean-temp']
        if archive_dir:
            import_cmd.extend(['--archive-dir', archive_dir])
        
        import_result = subprocess.run(import_cmd, check=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {enex_file}:")
        print(f"Command failed with exit code {e.returncode}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error processing {enex_file}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Batch process enex files: convert to HTML and import to OneNote')
    parser.add_argument('enex_dir', help='Directory containing enex files to process')
    parser.add_argument('--keep-temp', action='store_true', help='Keep temporary files after processing')
    parser.add_argument('--clean-temp', action='store_true', help='Automatically clean up temporary files without prompting')
    parser.add_argument('--archive-dir', default='./evernote export completed', help='Directory to move processed .enex files to')
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.enex_dir):
        print(f"Error: {args.enex_dir} is not a directory")
        sys.exit(1)
    
    # Set up archive directory
    archive_dir = args.archive_dir
    
    # Find the conversion scripts in the same directory as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    convert_script = os.path.join(script_dir, "convert_evernote_to_onenote.py")
    import_script = os.path.join(script_dir, "import_html_to_onenote.py")
    
    # Verify scripts exist
    for script in [convert_script, import_script]:
        if not os.path.isfile(script):
            print(f"Error: Required script not found: {script}")
            sys.exit(1)
    
    # Create temporary directory
    temp_dir = create_temp_dir()
    print(f"Created temporary directory: {temp_dir}")
    
    try:
        # Find all enex files
        enex_files = [
            os.path.join(args.enex_dir, f) 
            for f in os.listdir(args.enex_dir) 
            if f.endswith('.enex')
        ]
        
        if not enex_files:
            print(f"No enex files found in {args.enex_dir}")
            sys.exit(1)
        
        print(f"Found {len(enex_files)} enex files to process")
        
        # Process each enex file
        successful = 0
        failed = 0
        for enex_file in enex_files:
            if process_single_enex(enex_file, temp_dir, convert_script, import_script, archive_dir):
                successful += 1
            else:
                failed += 1
        
        # Print summary
        print("\nProcessing Summary:")
        print(f"Total files processed: {len(enex_files)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
    finally:
        # Clean up temporary directory unless --keep-temp was specified
        if not args.keep_temp and os.path.exists(temp_dir):
            print(f"\nCleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
        elif args.keep_temp:
            print(f"\nTemporary directory preserved: {temp_dir}")

if __name__ == "__main__":
    main() 