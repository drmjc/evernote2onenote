# evernote2onenote

Convert EverNote Notebooks into OneNote notes.

## Background
In ~2010, Evernote was way ahead of its time, and I stored everything there for work and home. Now, Evernote is almost $20/month and OneNote has most, if not all of the functionality. My Evernote notes contained images, PDF attachments, tables, todo lists, HTML pages and I wanted all of this to be brought into OneNote, using my Mac.

I wrote this over a weekend, as my first project using Cursor.AI. As such, the code is pretty awful, but it works, and I was able to import ~1300 notes from 36 notebooks of 1.2GB overnight. 

There are other solutions for converting from Endnote to Onenote that seemed to be retired, to work only on a PC, or didn't work for me. This software is not affiliated with any of these other software packages.

## Usage
`evernote2onenote.py -h`

### Workflow for one Notebook
1. in Evernote, export your Notebook to an ENEX format file, and have all the export note attributes selected, called my_notebook.enex
2. convert the enex file to individual html files: `evernote2onenote.py convert ./my_notebook.enex --html_dir .`. This will create lots of HTML files and attachment files.
3. Open OneNote and select the Notebook where you want the notes to be imported
4. import those html files into this Notebook using `evernote2onenote.py import . --clean-temp`. This will create a new 'Section' called my_notebook and import each note, from oldest to newest.

### Workflow for many Notebooks
1. export all your notebooks from Evernote as ENEX files. Save them all in a folder, called './queue'
2. run `evernote2onenote batch ./queue --archive-dir ./completed`. This will import each ENEX file at a time.

## Features
* tables, lists and formatting are imported
* PDF attachments are imported (as Print Outs)
* inline imagems are imported
* HTML attachments are imported, but formatting can be a bit wonky
* Notes are imported in their chronological age order, so sort by None or sort by Date Created will order the notes from old to new
* A header is added to indicate that the note was imported from EverNote and its orgiinal created and modified date
* In my experience, pasting anything into OneNote on Mac results in a paste error about 20-40% of the time. This script dismisses the dialog box and will keep trying & rarely has to try more than once to paste the contents
* It pauses longer when attaching larger PDF attachments
* Notebooks and Notes can have spaces and some special characters in it. Unsafe characters will be replaced.

## Limitations
1. This does not set the notes created and modified times
2. This ignores tags
3. The note's source URL is not imported
4. todo lists are imported as bullet lists with ticks and squares as icons
5. You can't use your computer while this is running, as OneNote needs to have the focus
6. I could have used the Microsoft Graph API but that seemed more complex to complete in a weekend
7. I've left all the debugging statements on

## TODO
1. convert into a python package
2. work out how to edit onenote craeted/modified dates
3. add the ability to pause the processing of notes
4. simple GUI

## Versions
I developed this in May 2025, using 
* Evernote 10.136.4-mac-ddl-public (20250425130902), Editor: v182.7.2, Service: v2.42.1
* OneNote for Mac Version 16.96 (25041326)
* MacOS 14.3.1 (23D60)
* Python 3.13.1
* pip 24.3.1

I doubt this will work on Windows and have no idea if it will work on any other version of Evernote, OneNote or Python.

# WARRANTY
This code comes with no warranty. You should backup your OneNote notebook before using. I share this software in the hope that it is useful to you. I will be turning off my Evernote subscription and I don't expect i'll be actively supporting this.

# MIT LICENSE

drmjc, May 2025
