import streamlit as st
import pandas as pd
import re
import time
import json
import pytube
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/|embed/)([\w-]{11})", url)
    return match.group(1) if match else None

def get_video_info(video_id):
    try:
        yt = pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}")
        return {
            "title": yt.title,
            "author": yt.author,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/0.jpg",
            "length": yt.length,
        }
    except:
        return {
            "title": f"Video {video_id}",
            "author": "Unknown",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/0.jpg",
            "length": 0
        }

def get_transcript(video_id):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    except:
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            return transcripts.find_transcript(['en']).fetch()
        except:
            return None

def show_youtube_downloader():
    st.header("📝 YouTube Transcript Downloader")
    url = st.text_input("YouTube Video URL")

    if st.button("Get Transcript"):
        video_id = extract_video_id(url)
        if not video_id:
            st.error("⚠️ Invalid YouTube URL.")
        else:
            info = get_video_info(video_id)
            st.image(info['thumbnail_url'], width=320)
            st.markdown(f"**Title:** {info['title']}")
            st.markdown(f"**Channel:** {info['author']}")
            st.markdown(f"**Length:** {info['length']//60}m {info['length']%60}s")
            st.markdown("---")

            transcript = get_transcript(video_id)
            if not transcript:
                st.error("❌ Transcript not available.")
            else:
                df = pd.DataFrame(transcript)
                st.markdown("### Transcript Preview")
                st.dataframe(df.head(10))

                txt = "\n".join([item['text'] for item in transcript])
                json_data = json.dumps(transcript, indent=2)
                srt_data = ""
                for i, item in enumerate(transcript):
                    start = time.strftime('%H:%M:%S,', time.gmtime(item['start'])) + f"{int((item['start'] % 1)*1000):03d}"
                    end = time.strftime('%H:%M:%S,', time.gmtime(item['start'] + item['duration'])) + f"{int(((item['start'] + item['duration']) % 1)*1000):03d}"
                    srt_data += f"{i+1}\n{start} --> {end}\n{item['text']}\n\n"

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("📥 Download TXT", txt, file_name=f"{info['title']}.txt")
                with col2:
                    st.download_button("📥 Download JSON", json_data, file_name=f"{info['title']}.json")
                with col3:
                    st.download_button("📥 Download SRT", srt_data, file_name=f"{info['title']}.srt")