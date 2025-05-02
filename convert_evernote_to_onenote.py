#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import os
import base64
import argparse
from datetime import datetime, timezone
import re
import hashlib
import sys
import time
import platform
import calendar

# Function to parse Evernote .enex file
def parse_enex(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    notes = []
    for note in root.findall('note'):
        title = note.find('title').text
        content = note.find('content').text
        created = note.find('created').text
        updated = note.find('updated').text
        resources = note.findall('resource')
        images = []
        attachments = []
        for resource in resources:
            mime = resource.find('mime').text
            data = resource.find('data').text
            if mime.startswith('image/'):
                images.append({'mime': mime, 'data': data})
            else:
                attachments.append({'mime': mime, 'data': data})
        notes.append({'title': title, 'content': content, 'created': created, 'updated': updated, 'images': images, 'attachments': attachments})
    return notes

# Function to save notes as HTML files with embedded images and linked attachments
def save_as_html(notes, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for note in notes:
        title = note['title']
        safe_title = sanitize_filename(title)
        display_title = sanitize_title_for_display(title)
        content = note['content']
        # Convert Evernote checklists to bullet lists with icons
        content = convert_checklists_to_bullets(content)
        created = note['created']
        updated = note['updated']
        created_epoch = evernote_time_to_local_epoch(created)
        updated_epoch = evernote_time_to_local_epoch(updated)
        images = note['images']
        attachments = note['attachments']
        image_tags = ""
        attachment_links = ""
        # Format dates as DD/MM/YYYY
        created_fmt = datetime.strptime(created[:8], "%Y%m%d").strftime("%d/%m/%Y")
        updated_fmt = datetime.strptime(updated[:8], "%Y%m%d").strftime("%d/%m/%Y")
        header = f"<div><b>Note imported from Evernote<br/>Created Date: {created_fmt}<br/>Modified Date: {updated_fmt}</b></div><br/>"

        # Map for replacing Evernote resource hashes with filenames
        image_filenames = []
        hash_to_filename = {}
        for i, image in enumerate(images):
            image_data = base64.b64decode(image['data'])
            image_extension = image['mime'].split('/')[1]
            image_filename = f"{safe_title}_image_{i}.{image_extension}"
            image_path = os.path.join(output_dir, image_filename)
            with open(image_path, 'wb') as img_file:
                img_file.write(image_data)
            os.utime(image_path, (created_epoch, updated_epoch))
            set_creation_date_mac(image_path, created_epoch)
            image_filenames.append(image_filename)
            md5_hash = hashlib.md5(image_data).hexdigest()
            hash_to_filename[md5_hash] = image_filename
            print(f"[DEBUG] Saved image: {image_filename} with hash {md5_hash}")

        # Replace <en-media ... /> tags with <img src=...>
        # Use a regex that matches any whitespace (including newlines) before '/>'
        def replace_en_media(match):
            attrs = match.group(1)
            hash_match = re.search(r'hash="([a-fA-F0-9]+)"', attrs)
            alt_match = re.search(r'alt="([^"]*)"', attrs)
            alt = alt_match.group(1) if alt_match and alt_match.group(1).strip() else None
            if hash_match:
                hash_val = hash_match.group(1)
                filename = hash_to_filename.get(hash_val)
                if filename:
                    if alt:
                        return f'<img src="{filename}" alt="{alt}"/>'
                    else:
                        return f'<img src="{filename}"/>'
            # Debug: If a fragment would be returned, print a warning
            if 'alt=""/>' in attrs:
                print(f"[DEBUG] WARNING: orphaned alt attribute in en-media: {attrs}")
            return ''
        content = re.sub(r'<en-media([^>]*)\s*/>', replace_en_media, content, flags=re.DOTALL)
        # Also handle non-self-closing <en-media ...> (if any)
        content = re.sub(r'<en-media([^>]*)>', replace_en_media, content)
        # Cleanup: remove any orphaned '/>' after <img ...> tags
        content = re.sub(r'(<img[^>]+>)\s*/>', r'\1', content)

        # Replace <a href=...><img ...></a> if needed (already handled by above if <en-media> is inside <a>)
        # No extra handling needed, as <img> will be inside <a> if present in original HTML

        # Embed images as data URIs in the HTML
        def embed_img_data_uri(match):
            src = match.group(1)
            # Only replace if src is a local file we saved
            if src in image_filenames:
                image_path = os.path.join(output_dir, src)
                try:
                    with open(image_path, 'rb') as img_file:
                        img_data = img_file.read()
                    ext = src.split('.')[-1].lower()
                    mime = f'image/{"jpeg" if ext in ["jpg", "jpeg"] else ext}'
                    b64 = base64.b64encode(img_data).decode('utf-8')
                    data_uri = f'data:{mime};base64,{b64}'
                    print(f"[DEBUG] Embedding image {src} as data URI")
                    return f'<img src="{data_uri}" alt="Embedded Image"/>'
                except Exception as e:
                    print(f"[DEBUG] Failed to embed image {src}: {e}")
                    return ''
            else:
                return match.group(0)
        content = re.sub(r'<img[^>]+src=["\"](.*?)["\"]', embed_img_data_uri, content)

        # Insert original note name (no prefix) and import info at the top of the content
        original_title_html = f'<div><b>{title}</b></div>'
        import_line = f'imported from Evernote, originally created on {created_fmt}'
        if updated_fmt != created_fmt:
            import_line += f', last modified {updated_fmt}'
        import_line_html = f'<div>{import_line}</div><br/>'
        top_html = original_title_html + import_line_html
        if '<en-note>' in content:
            content = content.replace('<en-note>', f'<en-note>{top_html}', 1)
        else:
            content = top_html + content
        pdf_links = []
        for i, attachment in enumerate(attachments):
            attachment_data = base64.b64decode(attachment['data'])
            attachment_extension = attachment['mime'].split('/')[1]
            attachment_filename = f"{safe_title}_attachment_{i}.{attachment_extension}"
            attachment_filename = sanitize_filename(attachment_filename)
            attachment_path = os.path.join(output_dir, attachment_filename)
            with open(attachment_path, 'wb') as att_file:
                att_file.write(attachment_data)
            os.utime(attachment_path, (created_epoch, updated_epoch))
            set_creation_date_mac(attachment_path, created_epoch)
            # If this is a PDF and has a source-url, add a link at the top
            if attachment['mime'] == 'application/pdf' and 'source-url' in attachment:
                url = attachment['source-url']
                pdf_links.append(f'<div><a href="{url}" target="_blank">Original file link</a></div>')
            attachment_links += f'<a href="{attachment_filename}" download>Attachment {i}</a><br>'
        # Insert PDF links at the top of the content
        if pdf_links:
            content = ''.join(pdf_links) + content
        content = content.replace('</en-note>', f'{image_tags}{attachment_links}</en-note>')
        file_name = f"{safe_title}.html"
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(f"<html><head><title>{display_title}</title><meta name='created' content='{created}'/><meta name='updated' content='{updated}'/></head><body>{content}</body></html>")
        os.utime(file_path, (created_epoch, updated_epoch))
        set_creation_date_mac(file_path, created_epoch)
        print(f"Saved: {file_path}")

def sanitize_filename(filename):
    # Replace invalid characters (including space) with _
    return re.sub(r'[^\w\-_.]', '_', filename)

def sanitize_title_for_display(title):
    # Remove newlines, carriage returns, and non-breaking spaces
    title = re.sub(r'[\r\n\u00A0]', ' ', title)
    # Remove control characters
    title = re.sub(r'[\x00-\x1F\x7F]', '', title)
    # Collapse multiple spaces
    title = re.sub(r' +', ' ', title)
    return title.strip()

def convert_checklists_to_bullets(content):
    # Replace checked todos with tick
    content = re.sub(r'<en-todo\s+checked="true"\s*/>', '✓', content)
    content = re.sub(r'<en-todo\s+checked="true"\s*>', '✓', content)
    # Replace unchecked todos with open square
    content = re.sub(r'<en-todo(\s+checked="false")?\s*/>', '☐', content)
    content = re.sub(r'<en-todo(\s+checked="false")?\s*>', '☐', content)
    return content

def evernote_time_to_local_epoch(evernote_time):
    # Accepts 'YYYYMMDDTHHMMSSZ' or 'YYYYMMDDHHMMSS'
    evernote_time = evernote_time.replace('T', '').replace('Z', '')
    dt_utc = datetime.strptime(evernote_time[:14], '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
    dt_local = dt_utc.astimezone()  # Convert to local time
    return time.mktime(dt_local.timetuple())

def set_creation_date_mac(filepath, created_epoch):
    if platform.system() == 'Darwin':
        import subprocess
        from datetime import datetime
        dt = datetime.fromtimestamp(created_epoch)
        date_str = dt.strftime('%m/%d/%Y %H:%M:%S')
        try:
            subprocess.run(['SetFile', '-d', date_str, filepath], check=True)
            print(f"[DEBUG] SetFile creation date for {filepath} to {date_str}")
        except Exception as e:
            print(f"[DEBUG] Could not set creation date for {filepath}: {e}")

# Main function
def main():
    parser = argparse.ArgumentParser(description='Convert Evernote .enex file to HTML files.')
    parser.add_argument('enex_file', nargs=1, help='Path to the Evernote .enex file')
    parser.add_argument('--output_dir', default=os.getcwd(), help='Directory to save the HTML files (default: current working directory)')
    args = parser.parse_args()

    if len(args.enex_file) != 1:
        print("Error: Please specify exactly one .enex file to convert.")
        sys.exit(1)
    enex_file = args.enex_file[0]

    notes = parse_enex(enex_file)
    save_as_html(notes, args.output_dir)

if __name__ == "__main__":
    main()
