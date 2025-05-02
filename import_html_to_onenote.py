#!/usr/bin/env python3

import os
import pyautogui
import time
import argparse
import subprocess
from AppKit import NSPasteboard, NSHTMLPboardType, NSPasteboardTypePNG
from Foundation import NSData
import re
import pyperclip
import sys
import shutil
from datetime import datetime

# Function to read HTML file content
def read_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Function to read image file content
def read_image_file(file_path):
    with open(file_path, 'rb') as file:
        return file.read()

# Function to set HTML and image content to clipboard
def set_html_clipboard(html_content, image_files):
    pb = NSPasteboard.generalPasteboard()
    pb.declareTypes_owner_([NSHTMLPboardType, NSPasteboardTypePNG], None)
    pb.setString_forType_(html_content, NSHTMLPboardType)
    
    for image_file in image_files:
        image_data = NSData.dataWithContentsOfFile_(image_file)
        pb.setData_forType_(image_data, NSPasteboardTypePNG)

def attach_pdf_with_applescript(pdf_path, delay=1):
    folder, filename = os.path.split(pdf_path)
    print(f"[DEBUG] PDF path: {pdf_path}")
    print(f"[DEBUG] Opening File Dialog")
    print(f"[DEBUG] PDF folder: {folder}")
    print(f"[DEBUG] PDF filename: {filename}")
    applescript = f'''
    tell application "System Events"
        tell process "OneNote"
            # Wait for file dialog to be ready
            repeat until exists window 1
                delay 0.1
            end repeat
            keystroke "G" using {{command down, shift down}}
            delay {delay}
            keystroke "{folder}"
            keystroke return
            delay {delay}
            keystroke "{filename}"
            keystroke return
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript])

def open_file_attachment_dialog():
    applescript = '''
    tell application "System Events"
        tell process "OneNote"
            click menu item "Printout..." of menu "Insert" of menu bar 1
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript])

def create_new_section(section_name):
    # Use AppleScript to open File > New Section
    applescript = '''
    tell application "System Events"
        tell process "OneNote"
            click menu item "New Section" of menu "File" of menu bar 1
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript])
    time.sleep(1)
    pyperclip.copy(section_name)
    applescript_paste_title = '''
    tell application "System Events"
        tell process "OneNote"
            click menu item "Paste" of menu "Edit" of menu bar 1
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript_paste_title])
    time.sleep(0.5)
    import pyautogui
    pyautogui.press('enter')
    time.sleep(1)
    # Check for modal after section creation
    if wait_for_onenote_dialog_clear_with_flag():
        print("[ERROR] Modal detected after section creation. Section may already exist. Exiting.")
        sys.exit(1)

def create_new_page(sleep_time=0.5):
    applescript = '''
    tell application "System Events"
        tell process "OneNote"
            click menu item "New Page" of menu "File" of menu bar 1
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript])
    time.sleep(sleep_time)

def sanitize_title(title):
    # Remove newlines, tabs, and other control characters
    title = re.sub(r'[\r\n\t]', ' ', title)
    # Optionally, remove any character not in a safe set (alphanumeric, dash, dot, comma, space)
    title = re.sub(r'[^\w\- .,]', '', title)
    return title.strip()

def debug_print_onenote_windows():
    applescript = '''
    tell application "System Events"
        tell process "OneNote"
            set winInfo to {}
            repeat with w in windows
                set end of winInfo to (name of w as string) & " | " & (value of attribute \"AXSubrole\" of w as string)
            end repeat
            return winInfo
        end tell
    end tell
    '''
    result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
    print("[DEBUG] All OneNote windows and subroles:")
    for line in result.stdout.strip().replace('{', '').replace('}', '').split(','):
        print("[DEBUG]   ", line.strip())

def wait_for_onenote_dialog_clear_with_flag():
    """Wait indefinitely for error modals, only pausing for AXDialog windows that are not file dialogs. Automatically dismisses modal by pressing 'enter'."""
    import pyautogui
    dialog_was_present = False
    known_error_keywords = ['sorry', 'paste', 'error', 'couldn', 'fail', 'wrong', 'already']
    dot_printed = False
    while True:
        applescript = '''
        tell application "System Events"
            tell process "OneNote"
                set winInfo to {}
                repeat with w in windows
                    set end of winInfo to (name of w as string) & " | " & (value of attribute \"AXSubrole\" of w as string)
                end repeat
                return winInfo
            end tell
        end tell
        '''
        result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
        win_lines = result.stdout.strip().replace('{', '').replace('}', '').split(',')
        found_error_modal = False
        for line in win_lines:
            line = line.strip()
            if '| AXDialog' in line:
                name = line.split('|')[0].strip()
                # Only treat as error modal if name is empty or matches error keywords
                if name == '' or any(keyword in name.lower() for keyword in known_error_keywords):
                    found_error_modal = True
        if found_error_modal:
            print('.', end='', flush=True)
            dot_printed = True
            dialog_was_present = True
            pyautogui.press('enter')  # Automatically dismiss modal
            time.sleep(0.4)
        else:
            if dot_printed:
                print('')  # Newline after dots
            break
    return dialog_was_present

def rename_current_page(new_title, sleep_time=0.5):
    print(f"[DEBUG] Attempting to rename page to: '{new_title}'")
    # Use AppleScript to select Notebooks > Rename Page (simpler path)
    applescript_rename = '''
    tell application "System Events"
        tell process "OneNote"
            click menu item "Rename Page" of menu 1 of menu bar item "Notebooks" of menu bar 1
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript_rename])
    time.sleep(sleep_time)
    pyperclip.copy(new_title)
    applescript_paste_title = '''
    tell application "System Events"
        tell process "OneNote"
            click menu item "Paste" of menu "Edit" of menu bar 1
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript_paste_title])
    time.sleep(sleep_time)
    import pyautogui
    pyautogui.press('enter')
    print(f"[DEBUG] Renamed page to: '{new_title}'")
    time.sleep(sleep_time)

def page_title_exists(title):
    applescript = '''
    tell application "System Events"
        tell process "OneNote"
            set pageTitles to {}
            try
                repeat with t in (every static text of every row of outline 1 of scroll area 1 of splitter group 1 of window 1)
                    set end of pageTitles to (value of t as string)
                end repeat
            on error
                return pageTitles
            end try
            return pageTitles
        end tell
    end tell
    '''
    result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
    titles = [t.strip() for t in result.stdout.strip().replace('{', '').replace('}', '').split(',') if t.strip()]
    return title in titles

def sanitize_section_name(name):
    # Remove or replace all invalid OneNote section name characters
    return re.sub(r'[?*\\/:<>|&#"%]', '-', name)

def sanitize_onenote_title(title):
    # Remove only newlines and carriage returns
    return re.sub(r'[\r\n]+', '', title).strip()

def calculate_attachment_wait_time(file_path, base_time=0.2, time_per_mb=1.0):
    """Calculate wait time based on file size. Minimum 0.2 second, then 1.0s per MB."""
    try:
        size_in_mb = os.path.getsize(file_path) / (1024 * 1024)
        wait_time = base_time + (size_in_mb * time_per_mb)
        return wait_time
    except Exception as e:
        print(f"[WARNING] Could not get file size for {file_path}: {e}")
        return 4.0

def wait_for_attachment_processing(attachment_file):
    wait_time = calculate_attachment_wait_time(attachment_file)
    print(f"[DEBUG] Waiting {wait_time:.1f}s for attachment: {os.path.basename(attachment_file)}")
    return wait_time

def process_attachment(attachment_file, dialog_sleep=0.3):
    open_file_attachment_dialog()
    time.sleep(dialog_sleep)  # Wait for file dialog to open
    wait_time = wait_for_attachment_processing(attachment_file)
    attach_pdf_with_applescript(attachment_file)
    time.sleep(wait_time)
    wait_for_onenote_dialog_clear_with_flag()

def paste_note_title_and_content(full_title, content, image_files, title_sleep=0.5, enter_sleep=1.0):
    print(f"[DEBUG] Final note title to paste: '{full_title}'")
    pyperclip.copy(full_title)
    applescript_paste_title = '''
    tell application "System Events"
        tell process "OneNote"
            click menu item "Paste" of menu "Edit" of menu bar 1
        end tell
    end tell
    '''
    print(f"[DEBUG] Pasting title for note: '{full_title}'")
    subprocess.run(['osascript', '-e', applescript_paste_title])
    time.sleep(title_sleep)
    pyautogui.press('enter')
    print(f"[DEBUG] Pressed enter after pasting title for note: '{full_title}'")
    time.sleep(enter_sleep)  # Wait for title to be confirmed
    dialog_was_present = wait_for_onenote_dialog_clear_with_flag()
    if dialog_was_present:
        rename_current_page(full_title)
    applescript_paste = '''
    tell application "System Events"
        tell process "OneNote"
            click menu item "Paste" of menu "Edit" of menu bar 1
        end tell
    end tell
    '''
    while True:
        set_html_clipboard(content, image_files)
        subprocess.run(['osascript', '-e', applescript_paste])
        time.sleep(1.5)  # Wait for content to paste
        modal_after_content = wait_for_onenote_dialog_clear_with_flag()
        if modal_after_content:
            print("[DEBUG] Retrying paste of note content due to modal...")
            continue
        else:
            break

def handle_attachments(attachment_files, dialog_sleep=0.3):
    for attachment_file in attachment_files:
        process_attachment(attachment_file, dialog_sleep=dialog_sleep)

def process_html_file(html_dir, file_name, total_notes, imported_count, page_sleep=1.5, title_sleep=0.5, enter_sleep=1.0, dialog_sleep=0.3):
    print(f"\nProcessing note {imported_count}/{total_notes}...")
    create_new_page(sleep_time=page_sleep)
    file_path = os.path.join(html_dir, file_name)
    content = read_html_file(file_path)
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if title_match:
        note_title = title_match.group(1).strip()
    else:
        note_title = os.path.splitext(file_name)[0]
    full_title = note_title.replace('\r', '').replace('\n', '').strip()
    if page_title_exists(full_title):
        print(f"[DEBUG] Skipping note '{full_title}' because it already exists in the section.")
        return False, note_title
    base_name = os.path.splitext(file_name)[0]
    image_files = [os.path.join(html_dir, img) for img in os.listdir(html_dir) if img.startswith(base_name) and img.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    attachment_files = [os.path.join(html_dir, att) for att in os.listdir(html_dir) if att.startswith(base_name) and not att.endswith(('.html', '.png', '.jpg', '.jpeg', '.gif'))]
    paste_note_title_and_content(full_title, content, image_files, title_sleep=title_sleep, enter_sleep=enter_sleep)
    handle_attachments(attachment_files, dialog_sleep=dialog_sleep)
    print(f"Imported: {note_title}")
    return True, note_title

def import_to_onenote(html_dir, section_name, section_sleep_time=1, page_sleep=1.5, title_sleep=0.5, enter_sleep=1.0, dialog_sleep=0.3):
    total_notes = len([f for f in os.listdir(html_dir) if f.endswith('.html')])
    print(f"\nStarting import of {total_notes} notes to OneNote section '{section_name}'...")
    subprocess.run(['osascript', '-e', 'tell application "OneNote" to activate'])
    time.sleep(section_sleep_time)
    create_new_section(section_name)
    time.sleep(section_sleep_time)
    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
    html_file_dates = []
    for file_name in html_files:
        file_path = os.path.join(html_dir, file_name)
        try:
            created_time = os.stat(file_path).st_birthtime
        except Exception as e:
            print(f"[DEBUG] Could not get st_birthtime for {file_name}: {e}")
            created_time = 0
        html_file_dates.append((created_time, file_name))
    html_file_dates.sort()
    imported_count = 0
    skipped_count = 0
    for idx, (created_time, file_name) in enumerate(html_file_dates, 1):
        if file_name.endswith('.html'):
            imported, note_title = process_html_file(
                html_dir, file_name, total_notes, idx,
                page_sleep=page_sleep, title_sleep=title_sleep, enter_sleep=enter_sleep, dialog_sleep=dialog_sleep
            )
            if imported:
                imported_count += 1
            else:
                skipped_count += 1

    # Send final enter key to clear any remaining modal dialogs
    subprocess.run(['osascript', '-e', '''
        tell application "System Events"
            tell process "OneNote"
                keystroke return
            end tell
        end tell
    '''])

    print(f"\nImport Summary:")
    print(f"Total notes processed: {total_notes}")
    print(f"Successfully imported: {imported_count}")
    print(f"Skipped (already existed): {skipped_count}")
    


# Main function
def main():
    parser = argparse.ArgumentParser(description='Import HTML files into OneNote.')
    parser.add_argument('--html_dir', required=True, help='Directory containing HTML files to import')
    parser.add_argument('--clean-temp', action='store_true', help='Automatically clean up temporary files without prompting')
    parser.add_argument('--archive-dir', default='./evernote export completed', help='Directory to move processed .enex files to')
    args = parser.parse_args()

    # Determine the section name based on the .enex file name
    enex_files = [f for f in os.listdir(args.html_dir) if f.endswith('.enex')]
    if not enex_files:
        print("No .enex files found in the directory.")
        return
    section_name = sanitize_section_name(os.path.splitext(enex_files[0])[0])

    # Import HTML files into OneNote
    import_to_onenote(args.html_dir, section_name)

    # Handle cleanup of temp files
    if args.clean_temp:
        cleanup = 'y'
    else:
        cleanup = input("\nDo you want to delete all temp files (*.html, *.gif, *.jpg, *.jpeg, *.png, *.pdf, *.xml, *.svg+xml) in this directory? (y/N): ").strip().lower()
    
    if cleanup == 'y':
        import glob
        patterns = ['*.html', '*.gif', '*.jpg', '*.jpeg', '*.png', '*.pdf', '*.xml', '*.svg+xml']
        for pattern in patterns:
            for file in glob.glob(os.path.join(args.html_dir, pattern)):
                try:
                    os.remove(file)
                    print(f"Deleted: {file}")
                except Exception as e:
                    print(f"Could not delete {file}: {e}")
    else:
        print("Skipped cleanup of temp files.")

    # Handle archiving of processed .enex files
    if args.archive_dir:
        if not os.path.exists(args.archive_dir):
            os.makedirs(args.archive_dir)
        for enex_file in enex_files:
            src = os.path.join(args.html_dir, enex_file)
            dst = os.path.join(args.archive_dir, enex_file)
            try:
                shutil.move(src, dst)
                print(f"Moved {enex_file} to {args.archive_dir}")
            except Exception as e:
                print(f"Could not move {enex_file}: {e}")
    else:
        print("Skipped moving .enex file to archive (no archive directory specified).")

if __name__ == "__main__":
    main()
