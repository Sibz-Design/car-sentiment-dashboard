from flask import Flask, render_template, jsonify, request
import requests
import json
from datetime import datetime, timedelta, timezone
import os
import re
from textblob import TextBlob
import logging
from jinja2.exceptions import TemplateNotFound
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube API Configuration
# Replace these with valid YouTube Data API v3 keys from Google Cloud Console
YOUTUBE_API_KEY_1 = os.getenv("")  # Replace with your first valid API key
YOUTUBE_API_KEY_2 = os.getenv("API_KEY_2")  # Replace with your second valid API key
CHANNEL_ID = "UCB-mfYAd3oJLEkoMxjRAxbg"

class YouTubeCommentsService:
    def __init__(self):
        self.api_keys = [YOUTUBE_API_KEY_1, YOUTUBE_API_KEY_2]
        self.channel_id = CHANNEL_ID
        self.current_api_key_index = 0
    
    def get_current_api_key(self):
        """Get the current API key"""
        return self.api_keys[self.current_api_key_index]
    
    def switch_api_key(self):
        """Switch to the next API key if rate limit or error occurs"""
        self.current_api_key_index = (self.current_api_key_index + 1) % len(self.api_keys)
        logger.info(f"Switched to API key {self.current_api_key_index + 1}")
        return self.get_current_api_key()
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text using TextBlob"""
        try:
            # Clean the text
            cleaned_text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
            cleaned_text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', cleaned_text)  # Remove URLs
            cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)  # Remove special characters
            
            if not cleaned_text.strip():
                return 'neutral'
            
            blob = TextBlob(cleaned_text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                return 'positive'
            elif polarity < -0.1:
                return 'negative'
            else:
                return 'neutral'
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 'neutral'
    
    def get_latest_videos(self, max_results=50):
        """Get latest videos from the YouTube channel"""
        url = "https://www.googleapis.com/youtube/v3/search"
        published_after = (datetime.now(timezone.utc) - timedelta(days=30)).replace(microsecond=0).isoformat()
        params = {
            'key': self.get_current_api_key(),
            'channelId': self.channel_id,
            'part': 'snippet,id',
            'order': 'date',
            'maxResults': min(max_results, 50),  # YouTube API limit
            'type': 'video',
            'publishedAfter': published_after
        }
        
        for attempt in range(len(self.api_keys)):
            try:
                logger.info(f"Fetching videos with params: {params}")
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'error' in data:
                    logger.error(f"YouTube API error: {data['error']}")
                    if data['error'].get('code') == 403:
                        params['key'] = self.switch_api_key()
                        continue
                    else:
                        raise Exception(data['error']['message'])
                
                videos = []
                for item in data.get('items', []):
                    if 'videoId' in item.get('id', {}):
                        videos.append({
                            'videoId': item['id']['videoId'],
                            'title': item['snippet']['title'],
                            'publishedAt': item['snippet']['publishedAt'],
                            'description': item['snippet'].get('description', '')[:200],
                            'thumbnail': item['snippet']['thumbnails'].get('default', {}).get('url', '')
                        })
                
                logger.info(f"Retrieved {len(videos)} videos")
                return videos
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching videos (attempt {attempt + 1}): {e}")
                if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 403:
                    params['key'] = self.switch_api_key()
                    continue
                return []
            except Exception as e:
                logger.error(f"Unexpected error fetching videos: {e}")
                return []
        
        logger.error("All API keys failed to fetch videos")
        return []
    
    def get_comments_for_video(self, video_id, max_results=50):
        """Get comments for a specific video"""
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            'key': self.get_current_api_key(),
            'part': 'snippet',
            'videoId': video_id,
            'maxResults': min(max_results, 100),  # YouTube API limit
            'order': 'time'
        }
        
        for attempt in range(len(self.api_keys)):
            try:
                logger.info(f"Fetching comments for video {video_id} with params: {params}")
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'error' in data:
                    logger.error(f"YouTube API error for video {video_id}: {data['error']}")
                    if data['error'].get('code') == 403:
                        params['key'] = self.switch_api_key()
                        continue
                    else:
                        raise Exception(data['error']['message'])
                
                comments = []
                for item in data.get('items', []):
                    try:
                        comment_data = item['snippet']['topLevelComment']['snippet']
                        comment_text = comment_data['textDisplay']
                        sentiment = self.analyze_sentiment(comment_text)
                        
                        comments.append({
                            'author': comment_data['authorDisplayName'],
                            'comment': comment_text[:500],  # Limit comment length
                            'date': comment_data['publishedAt'],
                            'likeCount': comment_data.get('likeCount', 0),
                            'sentiment': sentiment,
                            'authorProfileImageUrl': comment_data.get('authorProfileImageUrl', '')
                        })
                    except KeyError as e:
                        logger.warning(f"Missing key in comment data: {e}")
                        continue
                
                logger.info(f"Retrieved {len(comments)} comments for video {video_id}")
                return comments
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching comments for video {video_id} (attempt {attempt + 1}): {e}")
                if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 403:
                    params['key'] = self.switch_api_key()
                    continue
                return []
            except Exception as e:
                logger.error(f"Unexpected error fetching comments for video {video_id}: {e}")
                return []
        
        logger.error(f"All API keys failed to fetch comments for video {video_id}")
        return []
    
    def get_all_comments_data(self, max_videos=10, max_comments_per_video=50):
        """Get all comments data for analysis"""
        try:
            videos = self.get_latest_videos(max_videos)
            all_comments = []
            video_comment_counts = {}
            videos_with_comments = []
            
            for i, video in enumerate(videos[:max_videos]):
                logger.info(f"Processing video {i+1}/{max_videos}: {video['title'][:50]}...")
                comments = self.get_comments_for_video(video['videoId'], max_comments_per_video)
                
                if comments:  # Only include videos that have comments
                    video_title_short = video['title'][:30] + ('...' if len(video['title']) > 30 else '')
                    video_comment_counts[video_title_short] = len(comments)
                    videos_with_comments.append({
                        'title': video['title'],
                        'videoId': video['videoId'],
                        'publishedAt': video['publishedAt'],
                        'description': video.get('description', ''),
                        'thumbnail': video.get('thumbnail', ''),
                        'comments': comments,
                        'commentCount': len(comments)
                    })
                    all_comments.extend(comments)
            
            # Calculate sentiment statistics
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            for comment in all_comments:
                sentiment_counts[comment['sentiment']] += 1
            
            # Calculate engagement metrics
            total_likes = sum(comment['likeCount'] for comment in all_comments)
            avg_likes_per_comment = total_likes / len(all_comments) if all_comments else 0
            
            logger.info(f"Analysis complete: {len(all_comments)} comments from {len(videos_with_comments)} videos")
            
            return {
                'total_comments': len(all_comments),
                'video_comment_counts': video_comment_counts,
                'comments': all_comments,
                'videos_with_comments': videos_with_comments,
                'total_videos': len(videos_with_comments),
                'sentiment_counts': sentiment_counts,
                'total_likes': total_likes,
                'avg_likes_per_comment': round(avg_likes_per_comment, 2),
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in get_all_comments_data: {e}")
            return {
                'total_comments': 0,
                'video_comment_counts': {},
                'comments': [],
                'videos_with_comments': [],
                'total_videos': 0,
                'sentiment_counts': {'positive': 0, 'negative': 0, 'neutral': 0},
                'total_likes': 0,
                'avg_likes_per_comment': 0,
                'error': str(e)
            }

# Initialize the service
youtube_service = YouTubeCommentsService()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        return render_template('index.html')
    except TemplateNotFound:
        logger.error("Template 'index.html' not found in templates directory")
        return jsonify({'error': 'Template index.html not found'}), 500

@app.route('/sentiment')
def sentiment():
    """Sentiment analysis page"""
    try:
        return render_template('sentiment.html')
    except TemplateNotFound:
        logger.error("Template 'sentiment.html' not found in templates directory")
        return jsonify({'error': 'Template sentiment.html not found'}), 500

@app.route('/videos')
def videos():
    """Videos page"""
    try:
        return render_template('videos.html')
    except TemplateNotFound:
        logger.error("Template 'videos.html' not found in templates directory")
        return jsonify({'error': 'Template videos.html not found'}), 500

@app.route('/api/chart-data')
def get_chart_data():
    """Get data formatted for charts"""
    max_videos = request.args.get('max_videos', 10, type=int)
    max_comments = request.args.get('max_comments', 50, type=int)
    
    # Validate parameters
    max_videos = min(max(max_videos, 1), 20)  # Between 1 and 20
    max_comments = min(max(max_comments, 10), 100)  # Between 10 and 100
    
    try:
        data = youtube_service.get_all_comments_data(max_videos, max_comments)
        
        # Prepare data for pie chart (top 10 videos by comment count)
        video_counts = data['video_comment_counts']
        sorted_videos = sorted(video_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        pie_data = {
            'labels': [video[0] for video in sorted_videos],
            'values': [video[1] for video in sorted_videos],
            'colors': ['#FF0000', '#00b894', '#fdcb6e', '#54A0FF', '#5F27CD', 
                      '#FF9FF3', '#96CEB4', '#FECA57', '#45B7D1', '#FF9F43'][:len(sorted_videos)]
        }
        
        # Prepare data for bar chart (comments by date)
        comments_by_date = {}
        for comment in data['comments']:
            date = comment['date'][:10]  # Extract date part
            comments_by_date[date] = comments_by_date.get(date, 0) + 1
        
        sorted_dates = sorted(comments_by_date.items())[-30:]  # Last 30 days
        
        bar_data = {
            'labels': [item[0] for item in sorted_dates],
            'values': [item[1] for item in sorted_dates]
        }
        
        # Sentiment trend data
        sentiment_by_date = {}
        for comment in data['comments']:
            date = comment['date'][:10]
            if date not in sentiment_by_date:
                sentiment_by_date[date] = {'positive': 0, 'negative': 0, 'neutral': 0}
            sentiment_by_date[date][comment['sentiment']] += 1
        
        sentiment_trend = {
            'dates': sorted(sentiment_by_date.keys())[-14:],  # Last 14 days
            'positive': [],
            'negative': [],
            'neutral': []
        }
        
        for date in sentiment_trend['dates']:
            day_data = sentiment_by_date.get(date, {'positive': 0, 'negative': 0, 'neutral': 0})
            sentiment_trend['positive'].append(day_data['positive'])
            sentiment_trend['negative'].append(day_data['negative'])
            sentiment_trend['neutral'].append(day_data['neutral'])
        
        return jsonify({
            'pie_chart': pie_data,
            'bar_chart': bar_data,
            'sentiment_trend': sentiment_trend,
            'summary': {
                'total_comments': data['total_comments'],
                'total_videos': data['total_videos'],
                'sentiment_counts': data['sentiment_counts'],
                'total_likes': data.get('total_likes', 0),
                'avg_likes_per_comment': data.get('avg_likes_per_comment', 0)
            }
        })
    except Exception as e:
        logger.error(f"Error in get_chart_data: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/sentiment-data')
def get_sentiment_data():
    """Get detailed sentiment data with comments"""
    max_videos = request.args.get('max_videos', 5, type=int)
    max_comments = request.args.get('max_comments', 20, type=int)
    
    # Validate parameters
    max_videos = min(max(max_videos, 1), 10)  # Between 1 and 10
    max_comments = min(max(max_comments, 10), 50)  # Between 10 and 50
    
    try:
        data = youtube_service.get_all_comments_data(max_videos, max_comments)
        
        # Get sample comments for each sentiment
        sample_comments = {'positive': [], 'negative': [], 'neutral': []}
        for comment in data['comments']:
            sentiment = comment['sentiment']
            if len(sample_comments[sentiment]) < 10:  # Limit to 10 samples per sentiment
                sample_comments[sentiment].append({
                    'author': comment['author'],
                    'comment': comment['comment'][:200],  # Truncate long comments
                    'likeCount': comment['likeCount'],
                    'date': comment['date']
                })
        
        return jsonify({
            'videos_with_comments': data['videos_with_comments'],
            'sentiment_summary': data['sentiment_counts'],
            'sample_comments': sample_comments,
            'total_comments': data['total_comments'],
            'total_videos': data['total_videos'],
            'total_likes': data.get('total_likes', 0),
            'avg_likes_per_comment': data.get('avg_likes_per_comment', 0)
        })
    except Exception as e:
        logger.error(f"Error in get_sentiment_data: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/video-details/<video_id>')
def get_video_details(video_id):
    """Get detailed information about a specific video"""
    max_comments = request.args.get('max_comments', 100, type=int)
    
    try:
        comments = youtube_service.get_comments_for_video(video_id, max_comments)
        
        # Calculate sentiment for this video
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        for comment in comments:
            sentiment_counts[comment['sentiment']] += 1
        
        return jsonify({
            'video_id': video_id,
            'comments': comments,
            'comment_count': len(comments),
            'sentiment_counts': sentiment_counts,
            'total_likes': sum(comment['likeCount'] for comment in comments)
        })
    except Exception as e:
        logger.error(f"Error getting video details for {video_id}: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    try:
        return render_template('404.html'), 404
    except TemplateNotFound:
        logger.error("Template '404.html' not found in templates directory")
        return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    try:
        return render_template('500.html'), 500
    except TemplateNotFound:
        logger.error("Template '500.html' not found in templates directory")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run()