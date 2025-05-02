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

def convert_enex_to_html(enex_file, output_dir):
    """Convert a single enex file to HTML."""
    print(f"\nConverting: {enex_file}")
    try:
        # Use the existing conversion script
        cmd = [sys.executable, "convert_evernote_to_onenote.py", enex_file, "--output_dir", output_dir]

        convert_result = subprocess.run(
            cmd,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting {enex_file}:")
        print(f"Command failed with exit code {e.returncode}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error converting {enex_file}: {str(e)}")
        return False

def import_html_to_onenote(html_dir, clean_temp=False, archive_dir=None):
    """Import HTML files to OneNote."""
    print(f"\nImporting HTML files from: {html_dir}")
    try:
        cmd = [sys.executable, "import_html_to_onenote.py", "--html_dir", html_dir]
        if clean_temp:
            cmd.append("--clean-temp")
        if archive_dir:
            cmd.extend(["--archive-dir", archive_dir])
        import_result = subprocess.run(
            cmd,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error importing from {html_dir}:")
        print(f"Command failed with exit code {e.returncode}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error importing from {html_dir}: {str(e)}")
        return False

def process_single_enex(enex_file, temp_dir, clean_temp=False, archive_dir=None):
    """Process a single enex file: convert to HTML and import to OneNote."""
    print(f"\nProcessing: {enex_file}")
    
    # Create a unique subdirectory for this enex file
    file_basename = os.path.splitext(os.path.basename(enex_file))[0]
    work_dir = os.path.join(temp_dir, file_basename)
    os.makedirs(work_dir, exist_ok=True)
    
    # Copy enex file to work directory
    enex_copy = os.path.join(work_dir, os.path.basename(enex_file))
    shutil.copy2(enex_file, enex_copy)
    
    # Convert and import
    if convert_enex_to_html(enex_copy, work_dir):
        return import_html_to_onenote(work_dir, clean_temp=clean_temp, archive_dir=archive_dir)
    return False

def batch_process(enex_dir, keep_temp=False, archive_dir=None):
    """Process all enex files in a directory."""
    # Validate input directory
    if not os.path.isdir(enex_dir):
        print(f"Error: {enex_dir} is not a directory")
        return False
    
    # Create temporary directory
    temp_dir = create_temp_dir()
    print(f"Created temporary directory: {temp_dir}")
    
    try:
        # Function to get sorted list of enex files
        def get_sorted_enex_files():
            files = [
                (os.path.join(enex_dir, f), os.path.getctime(os.path.join(enex_dir, f)))
                for f in os.listdir(enex_dir)
                if f.endswith('.enex')
            ]
            return [f[0] for f in sorted(files, key=lambda x: x[1])]
        
        # Get initial list of files
        enex_files = get_sorted_enex_files()
        
        if not enex_files:
            print(f"No enex files found in {enex_dir}")
            return False
        
        print(f"Found {len(enex_files)} enex files to process")
        
        # Process each enex file
        successful = 0
        failed = 0
        processed_files = set()
        
        while True:
            # Get current list of files
            current_files = get_sorted_enex_files()
            
            # Find new files that haven't been processed
            new_files = [f for f in current_files if f not in processed_files]
            
            if not new_files:
                if not processed_files:
                    print("No files to process")
                    return False
                break  # No new files, exit the loop
            
            # Process the oldest new file
            enex_file = new_files[0]
            print(f"\nProcessing file: {os.path.basename(enex_file)}")
            
            if process_single_enex(enex_file, temp_dir, clean_temp=True, archive_dir=archive_dir):
                successful += 1
            else:
                failed += 1
            
            processed_files.add(enex_file)
        
        # Print summary
        print("\nProcessing Summary:")
        print(f"Total files processed: {len(processed_files)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        return successful > 0
        
    finally:
        # Clean up temporary directory unless --keep-temp was specified
        if not keep_temp and os.path.exists(temp_dir):
            print(f"\nCleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
        elif keep_temp:
            print(f"\nTemporary directory preserved: {temp_dir}")

def main():
    parser = argparse.ArgumentParser(description='Convert and import Evernote files to OneNote')
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # Convert mode
    convert_parser = subparsers.add_parser('convert', help='Convert enex file to HTML')
    convert_parser.add_argument('enex_file', help='Path to the enex file to convert')
    convert_parser.add_argument('--output_dir', default=os.getcwd(), help='Directory to save HTML files')
    convert_parser.add_argument('--clean-temp', action='store_true', help='Automatically clean up temporary files without prompting')
    
    # Import mode
    import_parser = subparsers.add_parser('import', help='Import HTML files to OneNote')
    import_parser.add_argument('html_dir', help='Directory containing HTML files to import')
    import_parser.add_argument('--clean-temp', action='store_true', help='Automatically clean up temporary files without prompting')
    import_parser.add_argument('--archive-dir', default='./evernote export completed', help='Directory to move processed .enex files to')
    
    # Batch mode
    batch_parser = subparsers.add_parser('batch', help='Batch process enex files')
    batch_parser.add_argument('enex_dir', help='Directory containing enex files to process')
    batch_parser.add_argument('--keep-temp', action='store_true', help='Keep temporary files after processing')
    batch_parser.add_argument('--archive-dir', default='./evernote export completed', help='Directory to move processed .enex files to')
    
    args = parser.parse_args()
    
    if args.mode == 'convert':
        success = convert_enex_to_html(args.enex_file, args.output_dir)
        sys.exit(0 if success else 1)
    
    elif args.mode == 'import':
        success = import_html_to_onenote(args.html_dir, clean_temp=args.clean_temp, archive_dir=args.archive_dir)
        sys.exit(0 if success else 1)
    
    elif args.mode == 'batch':
        success = batch_process(args.enex_dir, args.keep_temp, archive_dir=args.archive_dir)
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 