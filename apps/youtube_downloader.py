import streamlit as st
import pytube
from youtube_transcript_api import YouTubeTranscriptApi
import re
import pandas as pd
import time
import json

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    # Regular expression patterns for different YouTube URL formats
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard and shortened URLs
        r'(?:embed\/)([0-9A-Za-z_-]{11})',  # Embedded URLs
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})' # Watch URLs
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(video_id):
    """Get video title and other info using pytube"""
    try:
        # Add retry logic and better error handling
        max_retries = 3
        for attempt in range(max_retries):
            try:
                youtube = pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}")
                return {
                    "title": youtube.title or f"Video {video_id}",
                    "author": youtube.author or "Unknown author",
                    "thumbnail_url": youtube.thumbnail_url or f"https://img.youtube.com/vi/{video_id}/0.jpg",
                    "length": youtube.length or 0,
                }
            except Exception as retry_error:
                if attempt == max_retries - 1:
                    raise retry_error
                time.sleep(1)  # Wait before retrying

    except Exception as e:
        st.error(f"Error fetching video info: {str(e)}")
        # Return fallback info instead of None to avoid breaking the app
        return {
            "title": f"Video {video_id}",
            "author": "Unknown author",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/0.jpg",
            "length": 0,
        }

def get_transcript(video_id):
    """Get transcript from YouTube video ID"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript_list
    except Exception as e:
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            return transcripts.find_transcript(['en']).fetch()
        except Exception as e2:
            st.error(f"Error fetching transcript: {str(e)}")
            return None

def show_youtube_downloader():
    st.header("📝 YouTube Transcript Downloader")

    # User instructions
    st.markdown("""
    ### How to use:
    1. Paste a YouTube video URL in the input field below
    2. Click 'Get Transcript' to fetch the video transcript
    3. Download the transcript in your preferred format
    """)

    # URL input
    url = st.text_input(
        "Enter YouTube video URL", 
        placeholder="https://www.youtube.com/watch?v=..."
    )

    if st.button("Get Transcript", type="primary"):
        if not url:
            st.error("Please enter a YouTube video URL")
            return

        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL. Please enter a valid YouTube video link.")
            return

        # Show progress
        with st.spinner("Fetching transcript..."):
            # Get video info
            video_info = get_video_info(video_id)

            if not video_info:
                st.error("Could not retrieve video information")
                return

            # Get transcript
            transcript_data = get_transcript(video_id)

            if not transcript_data:
                st.error("No transcript available for this video. The video might not have captions or subtitles.")
                return

            # Display video info
            st.markdown("<div style='padding:10px; border:1px solid black;'>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 2])

            with col1:
                st.image(video_info["thumbnail_url"], use_container_width=True)

            with col2:
                st.subheader(video_info["title"])
                st.markdown(f"**Channel:** {video_info['author']}")

                # Convert length to minutes and seconds
                minutes, seconds = divmod(video_info["length"], 60)
                st.markdown(f"**Length:** {minutes} minutes, {seconds} seconds")
            st.markdown("</div>", unsafe_allow_html=True)

            # Add spacing
            st.markdown("<br>", unsafe_allow_html=True)

            # Create a DataFrame from transcript data
            df = pd.DataFrame(transcript_data)

            # Display transcript preview
            st.subheader("Transcript Preview")
            st.dataframe(df.head(10), use_container_width=True)

            # Full transcript display (collapsible)
            with st.expander("View Full Transcript"):
                st.dataframe(df, use_container_width=True)
            
            # Chunked transcript display
            st.subheader("Chunked Transcript")
            chunk_size = st.slider("Words per chunk", min_value=500, max_value=4000, value=2000, step=500)
            
            # Process transcript into chunks
            all_text = " ".join([item['text'] for item in transcript_data])
            words = all_text.split()
            chunks = []
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                chunks.append({
                    'chunk_number': len(chunks) + 1,
                    'text': chunk
                })
            
            # Display chunks
            for chunk in chunks:
                with st.expander(f"Chunk {chunk['chunk_number']}"):
                    st.write(chunk['text'])

            # Download options
            st.subheader("Download Options")

            # Prepare download data
            csv = df.to_csv(index=False).encode('utf-8')
            txt = "\n".join([f"[{item['start']:.2f}s - {item['start'] + item['duration']:.2f}s] {item['text']}" for item in transcript_data])

            # Text-only version for simple download
            simple_txt = "\n".join([item['text'] for item in transcript_data])

            # JSON format
            json_data = json.dumps(transcript_data, indent=2).encode('utf-8')

            # SRT (SubRip) format
            srt_content = ""
            for i, item in enumerate(transcript_data):
                start_time = item['start']
                end_time = start_time + item['duration']

                # Format time as HH:MM:SS,mmm
                start_formatted = time.strftime('%H:%M:%S,', time.gmtime(start_time)) + f"{int((start_time % 1) * 1000):03d}"
                end_formatted = time.strftime('%H:%M:%S,', time.gmtime(end_time)) + f"{int((end_time % 1) * 1000):03d}"

                srt_content += f"{i+1}\n{start_formatted} --> {end_formatted}\n{item['text']}\n\n"

            # Download buttons - first row
            col1, col2, col3 = st.columns(3)

            with col1:
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name=f"{video_info['title']}_transcript.csv",
                    mime="text/csv"
                )

            with col2:
                st.download_button(
                    label="Download as TXT (with timestamps)",
                    data=txt,
                    file_name=f"{video_info['title']}_transcript.txt",
                    mime="text/plain"
                )

            with col3:
                st.download_button(
                    label="Download as TXT (text only)",
                    data=simple_txt,
                    file_name=f"{video_info['title']}_transcript_text_only.txt",
                    mime="text/plain"
                )

            # Second row of download buttons
            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label="Download as JSON",
                    data=json_data,
                    file_name=f"{video_info['title']}_transcript.json",
                    mime="application/json"
                )

            with col2:
                st.download_button(
                    label="Download as SRT (Subtitle)",
                    data=srt_content,
                    file_name=f"{video_info['title']}_transcript.srt",
                    mime="text/plain"
                )
            
            # Add chunked transcript download
            chunked_text = "\n\n".join([f"Chunk {chunk['chunk_number']}:\n{chunk['text']}" for chunk in chunks])
            st.download_button(
                label="Download Chunked Transcript",
                data=chunked_text,
                file_name=f"{video_info['title']}_chunked_transcript.txt",
                mime="text/plain"
            )