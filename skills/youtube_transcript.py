import youtube_transcript_api
from urllib.parse import urlparse, parse_qs

def get_youtube_transcript(uri):
    video_id = parse_qs(urlparse(uri).query).get("v", [None])[0]

    if video_id is None:
        video_id = urlparse(uri).path.split("/")[-1]
    
    transcript = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(video_id)
    
    text = ""

    for line in transcript:
        text += line["text"] + " "

    return text