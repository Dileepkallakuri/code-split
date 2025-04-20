import streamlit as st
import pandas as pd
import re
import time
import json
import pytube
from pytube import YouTube
import random
import os
import requests
import webbrowser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# Create a cache directory if it doesn't exist
if not os.path.exists('cache'):
    os.makedirs('cache')

# List of free proxies - you can update this list with working proxies
# Format: "http://ip:port"
PROXIES = [
    # Add your proxies here, example:
    # "http://202.131.153.146:1111",
    # "http://27.124.20.41:3128",
]

def get_random_proxy():
    """Return a random proxy from the list or None if list is empty"""
    return random.choice(PROXIES) if PROXIES else None

def extract_video_id(url):
    """Extract the video ID from a YouTube URL"""
    match = re.search(r"(?:v=|youtu\.be/|embed/)([\w-]{11})", url)
    return match.group(1) if match else None

def get_video_info(video_id):
    """Get video information using pytube"""
    try:
        cache_file = f'cache/{video_id}_info.json'
        
        # Check if info is cached
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
                
        # Get fresh info
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        info = {
            "title": yt.title,
            "author": yt.author,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/0.jpg",
            "length": yt.length,
            "description": yt.description
        }
        
        # Cache the info
        with open(cache_file, 'w') as f:
            json.dump(info, f)
            
        return info
    except Exception as e:
        st.warning(f"Could not get complete video info: {str(e)}")
        return {
            "title": f"Video {video_id}",
            "author": "Unknown",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/0.jpg",
            "length": 0,
            "description": ""
        }

def get_transcript_with_api(video_id):
    """Get transcript using youtube_transcript_api with proxy support"""
    cache_file = f'cache/{video_id}_transcript.json'
    
    # Check if transcript is cached
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    # Try with proxy if available
    proxy = get_random_proxy()
    try:
        if proxy:
            # Set up proxy for requests
            os.environ["HTTP_PROXY"] = proxy
            os.environ["HTTPS_PROXY"] = proxy
        
        # Try getting English transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        
        # Cache the result
        with open(cache_file, 'w') as f:
            json.dump(transcript, f)
            
        return transcript
    except (TranscriptsDisabled, NoTranscriptFound):
        # Try listing available transcripts
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            available_transcript = transcripts.find_generated_transcript(['en', 'en-US'])
            transcript = available_transcript.fetch()
            
            # Cache the result
            with open(cache_file, 'w') as f:
                json.dump(transcript, f)
                
            return transcript
        except Exception as e:
            st.warning(f"Could not find any English transcripts: {str(e)}")
            return None
    except Exception as e:
        st.warning(f"Error getting transcript with API: {str(e)}")
        return None
    finally:
        # Clean up environment variables
        if proxy:
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)

def get_transcript_with_pytube(video_id):
    """Fallback method to get captions using pytube directly"""
    try:
        cache_file = f'cache/{video_id}_pytube_transcript.json'
        
        # Check if transcript is cached
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        caption_tracks = yt.captions
        
        if not caption_tracks:
            return None
            
        # Try to get English captions first
        caption = None
        for c in caption_tracks.keys():
            if 'en' in c.lower():
                caption = caption_tracks[c]
                break
        
        # If no English caption found, use the first available
        if not caption and caption_tracks:
            caption = caption_tracks[list(caption_tracks.keys())[0]]
            
        if not caption:
            return None
            
        # Process captions into transcript format
        xml_captions = caption.xml_captions
        lines = []
        
        # Basic XML parsing (simplified - might need improvement for complex captions)
        pattern = r'<text start="([\d\.]+)" dur="([\d\.]+)".*?>(.*?)</text>'
        matches = re.finditer(pattern, xml_captions, re.DOTALL)
        
        for match in matches:
            start = float(match.group(1))
            duration = float(match.group(2))
            text = match.group(3).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            
            lines.append({
                'text': text,
                'start': start,
                'duration': duration
            })
        
        # Cache the result
        with open(cache_file, 'w') as f:
            json.dump(lines, f)
            
        return lines
    except Exception as e:
        st.warning(f"Error getting transcript with pytube: {str(e)}")
        return None

def show_youtube_downloader():
    st.header("📝 YouTube Transcript Downloader")
    
    # CSS for better presentation
    st.markdown("""
    <style>
    .info-box {
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .options-container {
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 5px;
        margin-top: 20px;
        margin-bottom: 20px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # New session state variable to track if redirect is needed
    if 'redirect_clicked' not in st.session_state:
        st.session_state.redirect_clicked = False
    
    # Function to set redirect flag
    def set_redirect():
        st.session_state.redirect_clicked = True
    
    # Define the redirect URL
    redirect_url = "https://093e6c49-4e56-41d3-aeab-98d3379ab34d-00-rykhxqi1xadr.worf.replit.dev/"
        
    url = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
    
    advanced_options = st.expander("Advanced Options")
    with advanced_options:
        use_proxies = st.checkbox("Use Proxy Rotation (if available)", value=PROXIES != [])
        use_fallback = st.checkbox("Use Pytube fallback if transcript API fails", value=True)
        clear_cache = st.checkbox("Clear cache for this video", value=False)
    
    # Check if redirect was clicked in previous run
    if st.session_state.redirect_clicked:
        # This creates a more reliable redirect approach
        st.markdown(f"""
        <meta http-equiv="refresh" content="0;URL='{redirect_url}'" />
        <p>Redirecting to alternative service...</p>
        <a href="{redirect_url}" target="_blank">Click here if not redirected automatically</a>
        """, unsafe_allow_html=True)
        st.stop()
    
    if st.button("Get Transcript"):
        if not url:
            st.warning("Please enter a YouTube URL")
            st.stop()
            
        video_id = extract_video_id(url)
        if not video_id:
            st.error("⚠️ Invalid YouTube URL. Please enter a valid YouTube video URL.")
            st.stop()
        
        # Clear cache if requested
        if clear_cache:
            for cache_file in [
                f'cache/{video_id}_info.json',
                f'cache/{video_id}_transcript.json',
                f'cache/{video_id}_pytube_transcript.json'
            ]:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    st.success(f"Cleared cache for {video_id}")
        
        # Display loading indicator
        with st.spinner("Fetching video information..."):
            info = get_video_info(video_id)
            
        # Show video info
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(info['thumbnail_url'], width=320)
        with col2:
            st.markdown(f"### {info['title']}")
            st.markdown(f"**Channel:** {info['author']}")
            st.markdown(f"**Length:** {info['length']//60}m {info['length']%60}s")
        
        st.markdown("---")
        
        # Always show custom error message and redirect button regardless of what happens
        st.markdown("""
        <div class="error-message">
        Dileep's data center IPs are blocked due to excessive requests. In the event of critical priority, I can attempt connection via his personal private networks or Home VPNs, which requires authorized access. Direct communication with Dileep is needed to grant network traversal permissions.
        </div>
        """, unsafe_allow_html=True)
        
        # Add a proceed button with more descriptive text, using on_click to set state
        st.button("Proceed to Alternative Service", on_click=set_redirect)
        
        # Direct link as backup in case button doesn't work
        st.markdown(f"<a href='{redirect_url}' target='_blank'>Alternative: Open service in new tab</a>", unsafe_allow_html=True)
        
        # Now try to get the transcript - this code will still run but the error message
        # and redirect button will always appear above
        try:
            # Get transcript with loading indicator
            with st.spinner("Fetching transcript... This may take a moment"):
                # Try the API method first
                transcript = get_transcript_with_api(video_id)
                
                # If API method fails and fallback is enabled, try pytube
                if not transcript and use_fallback:
                    st.info("Trying alternative method to fetch subtitles...")
                    transcript = get_transcript_with_pytube(video_id)
            
            if not transcript:
                st.error("""
                ❌ Transcript not available. This could be due to:
                
                1. The video doesn't have any captions/subtitles
                2. The captions are disabled for this video
                3. YouTube API restrictions (try using the advanced options)
                
                Try another video or check if captions are available on YouTube.
                """)
            else:
                # Show success and transcript preview
                st.success(f"✅ Successfully retrieved transcript with {len(transcript)} segments")
                
                st.markdown("### Transcript Preview")
                df = pd.DataFrame(transcript)
                st.dataframe(df.head(10))
                
                st.markdown("### Download Options")
                
                # Convert to different formats
                txt = "\n".join([item.get('text', '') for item in transcript])
                json_data = json.dumps(transcript, indent=2)
                
                # Create SRT format
                srt_data = ""
                for i, item in enumerate(transcript):
                    start_seconds = item.get('start', 0)
                    duration = item.get('duration', 0)
                    
                    start = time.strftime('%H:%M:%S,', time.gmtime(start_seconds)) + f"{int((start_seconds % 1)*1000):03d}"
                    end = time.strftime('%H:%M:%S,', time.gmtime(start_seconds + duration)) + f"{int(((start_seconds + duration) % 1)*1000):03d}"
                    
                    srt_data += f"{i+1}\n{start} --> {end}\n{item.get('text', '')}\n\n"
                
                # Download buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button("📥 Download TXT", txt, file_name=f"{info['title']}.txt")
                with col2:
                    st.download_button("📥 Download JSON", json_data, file_name=f"{info['title']}.json")
                with col3:
                    st.download_button("📥 Download SRT", srt_data, file_name=f"{info['title']}.srt")
                    
        except Exception as e:
            # Still display the error for debugging, but the custom message will already be shown above
            st.error(f"Error processing transcript: {str(e)}")

if __name__ == "__main__":
    show_youtube_downloader()