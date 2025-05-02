# evernote2onenote

Convert your EverNote Notebooks into OneNote Sections.

## Background
In ~2010, Evernote was way ahead of its time, and I stored everything there for work and home. Now, Evernote is almost $20/month and OneNote has most, if not all of the functionality. My Evernote notes contained images, PDF attachments, tables, todo lists, HTML pages and I wanted all of this to be brought into OneNote.

I wrote this over a weekend, as my first project using Cursor.AI. As such, the code is pretty awful, but it works, and I was able to import ~1300 notes from 36 notebooks of 1.2GB overnight. 

There seem to be other solutions for converting from Endnote to Onenote that seemed to be retired, to work only on a PC, or didn't work. This software is not affiliated with any other software.

### Versions
I developed this in May 2025, using 
* Evernote 10.136.4-mac-ddl-public (20250425130902), Editor: v182.7.2, Service: v2.42.1
* OneNote for Mac Version 16.96 (25041326)
* MacOS 14.3.1 (23D60)
* Python 3.13.1
* pip 24.3.1

I doubt this will work on Windows and have no idea if it will work on any other version of Evernote, OneNote or Python.

## Workflow for one Notebook
1. in Evernote, export your Notebook to an ENEX format file, and have all the export note attributes selected, called my_notebook.enex
2. convert the enex file to individual html files: convert_evernote_to_onenote.py `./my_notebook.enex . --html_dir .` This will create lots of HTML files and attachment files.
3. Open OneNote and select the Notebook where you want the notes to be imported
4. import those html files into this Notebook using `./import_html_to_onenote.py --html_dir . --clean-temp`

## Workflow for many Notebooks
1. export all your notebooks from Evernote as ENEX files. Save them all in a folder, called './queue'
2. run evernote2onenote batch ./queue --archive-dir ./completed

## Features
* tables, lists and formatting looks great
* PDF attachments are imported (as Print Outs)
* inline imagems are imported
* HTML attachments are imported, but formatting can be a bit wonky
* Notes are imported in their chronological age order, so sort by None or sort by Date Created will order the notes from old to new
* A header is added to indicate that the note was imported from EverNote and its orgiinal created and modified date
* Pasting anything into OneNote often results in a paste error, but the script will keep trying and seems to work well
* It pauses longer when attaching larger PDF attachments

## Limitations
1. This does not set the notes created and modified times
