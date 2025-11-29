@echo off
cd /d "C:\Users\wayfa\PycharmProjects\RSS Feed Project"
call venv\Scripts\activate.bat
python RSS_feed.py > feed_output.txt 2>&1