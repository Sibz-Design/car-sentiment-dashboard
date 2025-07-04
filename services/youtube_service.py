import requests
import json
from datetime import datetime

class YouTubeService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    def get_latest_videos(self, channel_id, max_results=50):
        """Get latest videos from a channel"""
        url = f"{self.base_url}/search"
        params = {
            'key': self.api_key,
            'channelId': channel_id,
            'part': 'snippet,id',
            'order': 'date',
            'maxResults': max_results,
            'type': 'video'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get('items', []):
            if item['id'].get('videoId'):
                video = {
                    'videoId': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'publishedAt': item['snippet']['publishedAt'],
                    'thumbnail': item['snippet']['thumbnails']['medium']['url']
                }
                videos.append(video)
        
        return videos
    
    def get_video_comments(self, video_id, max_results=50):
        """Get comments for a specific video"""
        url = f"{self.base_url}/commentThreads"
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'videoId': video_id,
            'maxResults': max_results,
            'order': 'time'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        comments = []
        for item in data.get('items', []):
            comment_data = item['snippet']['topLevelComment']['snippet']
            comment = {
                'author': comment_data['authorDisplayName'],
                'comment': comment_data['textDisplay'],
                'date': comment_data['publishedAt'],
                'likeCount': comment_data.get('likeCount', 0),
                'authorProfileImageUrl': comment_data.get('authorProfileImageUrl', '')
            }
            comments.append(comment)
        
        return comments
