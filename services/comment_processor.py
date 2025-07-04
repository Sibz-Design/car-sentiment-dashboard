from textblob import TextBlob
import re

class SentimentService:
    def __init__(self):
        pass
    
    def clean_text(self, text):
        """Clean text for sentiment analysis"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text"""
        try:
            clean_text = self.clean_text(text)
            blob = TextBlob(clean_text)
            
            # Get polarity (-1 to 1)
            polarity = blob.sentiment.polarity
            
            # Classify sentiment
            if polarity > 0.1:
                return 'positive'
            elif polarity < -0.1:
                return 'negative'
            else:
                return 'neutral'
        except:
            return 'neutral'
    
    def get_sentiment_score(self, text):
        """Get detailed sentiment score"""
        try:
            clean_text = self.clean_text(text)
            blob = TextBlob(clean_text)
            
            return {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity,
                'classification': self.analyze_sentiment(text)
            }
        except:
            return {
                'polarity': 0,
                'subjectivity': 0,
                'classification': 'neutral'
            }

"""
File 6: templates/base.html
"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Cars.co.za YouTube Analytics{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-danger">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <strong>Cars.co.za Analytics</strong>
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('index') }}">Home</a>
                <a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a>
            </div>
        </div>
    </nav>

    <main class="container mt-4">
        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>

"""
File 7: templates/index.html
"""
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4">Cars.co.za YouTube Comment Sentiment Analysis</h1>
        
        <!-- Loading indicator -->
        <div id="loading" class="text-center" style="display: none;">
            <div class="spinner-border text-danger" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading videos and comments...</p>
        </div>

        <!-- Videos Container -->
        <div id="videos-container">
            <!-- Videos will be loaded here -->
        </div>
    </div>
</div>

<!-- Video Modal -->
<div class="modal fade" id="videoModal" tabindex="-1" aria-labelledby="videoModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header bg-danger text-white">
                <h5 class="modal-title" id="videoModalLabel">Video Comments</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div id="video-info" class="mb-3"></div>
                <div id="comments-container">
                    <!-- Comments will be loaded here -->
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    loadVideos();
});

function loadVideos() {
    const loading = document.getElementById('loading');
    const container = document.getElementById('videos-container');
    
    loading.style.display = 'block';
    
    fetch('/api/videos')
        .then(response => response.json())
        .then(data => {
            loading.style.display = 'none';
            
            if (data.success) {
                displayVideos(data.videos);
            } else {
                container.innerHTML = '<div class="alert alert-danger">Error loading videos: ' + data.error + '</div>';
            }
        })
        .catch(error => {
            loading.style.display = 'none';
            container.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
        });
}

function displayVideos(videos) {
    const container = document.getElementById('videos-container');
    let html = '<div class="row">';
    
    videos.forEach(video => {
        html += `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card video-card">
                    <img src="${video.thumbnail}" class="card-img-top" alt="${video.title}">
                    <div class="card-body">
                        <h5 class="card-title">${video.title}</h5>
                        <p class="card-text text-muted">${formatDate(video.publishedAt)}</p>
                        <button class="btn btn-danger" onclick="loadComments('${video.videoId}', '${video.title}', '${video.thumbnail}')">
                            View Comments
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function loadComments(videoId, title, thumbnail) {
    const modal = new bootstrap.Modal(document.getElementById('videoModal'));
    const videoInfo = document.getElementById('video-info');
    const commentsContainer = document.getElementById('comments-container');
    
    // Set video info
    videoInfo.innerHTML = `
        <div class="d-flex align-items-center mb-3">
            <img src="${thumbnail}" alt="${title}" class="me-3" style="width: 120px; height: 90px; object-fit: cover;">
            <div>
                <h6 class="mb-0">${title}</h6>
                <small class="text-muted">Video ID: ${videoId}</small>
            </div>
        </div>
    `;
    
    // Show loading
    commentsContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-danger" role="status"></div></div>';
    
    modal.show();
    
    // Load comments
    fetch(`/api/comments/${videoId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayComments(data.comments);
            } else {
                commentsContainer.innerHTML = '<div class="alert alert-danger">Error loading comments: ' + data.error + '</div>';
            }
        })
        .catch(error => {
            commentsContainer.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
        });
}

function displayComments(comments) {
    const container = document.getElementById('comments-container');
    let html = '';
    
    if (comments.length === 0) {
        html = '<div class="alert alert-info">No comments found for this video.</div>';
    } else {
        comments.forEach(comment => {
            const sentimentClass = getSentimentClass(comment.sentiment);
            const sentimentIcon = getSentimentIcon(comment.sentiment);
            
            html += `
                <div class="comment-card mb-3">
                    <div class="d-flex">
                        <img src="${comment.authorProfileImageUrl || '/static/images/default-avatar.png'}" 
                             alt="${comment.author}" class="comment-avatar me-3">
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <strong>${comment.author}</strong>
                                <div class="d-flex align-items-center">
                                    <span class="sentiment-badge ${sentimentClass}">
                                        ${sentimentIcon} ${comment.sentiment.toUpperCase()}
                                    </span>
                                    <small class="text-muted ms-2">${formatDate(comment.date)}</small>
                                </div>
                            </div>
                            <p class="mb-1">${comment.comment}</p>
                            html_snippet = f'<small class="text-muted">❤️ {comment["likeCount"]} likes</small>'

                        </div>
                    </div>
                </div>
            `;
        });
    }
    
    container.innerHTML = html;
}

function getSentimentClass(sentiment) {
    switch(sentiment) {
        case 'positive': return 'sentiment-positive';
        case 'negative': return 'sentiment-negative';
        default: return 'sentiment-neutral';
    }
}

function getSentimentIcon(sentiment) {
    switch(sentiment) {
        case 'positive': return '😊';
        case 'negative': return '😞';
        default: return '😐';
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
</script>
{% endblock %}

"""
File 8: templates/dashboard.html
"""
{% extends "base.html" %}

{% block title %}Dashboard - Cars.co.za Analytics{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4">Analytics Dashboard</h1>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-danger text-white">
                <h5 class="mb-0">Sentiment Distribution</h5>
            </div>
            <div class="card-body">
                <canvas id="sentimentChart"></canvas>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-danger text-white">
                <h5 class="mb-0">Comment Activity</h5>
            </div>
            <div class="card-body">
                <div id="stats-container">
                    <div class="text-center">
                        <div class="spinner-border text-danger" role="status"></div>
                        <p class="mt-2">Loading statistics...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header bg-danger text-white">
                <h5 class="mb-0">Recent Activity</h5>
            </div>
            <div class="card-body">
                <div id="recent-activity">
                    <!-- Recent activity will be loaded here -->
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
let sentimentChart;

document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    // Refresh data every 5 minutes
    setInterval(loadDashboardData, 300000);
});

function loadDashboardData() {
    fetch('/api/sentiment-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateSentimentChart(data.stats);
                updateStats(data.stats);
            } else {
                console.error('Error loading dashboard data:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function updateSentimentChart(stats) {
    const ctx = document.getElementById('sentimentChart').getContext('2d');
    
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [stats.positive, stats.negative, stats.neutral],
                backgroundColor: [
                    '#28a745',
                    '#dc3545',
                    '#6c757d'
                ],
                borderColor: [
                    '#28a745',
                    '#dc3545',
                    '#6c757d'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function updateStats(stats) {
    const container = document.getElementById('stats-container');
    const total = stats.positive + stats.negative + stats.neutral;
    
    const positivePercent = total > 0 ? (stats.positive / total * 100).toFixed(1) : 0;
    const negativePercent = total > 0 ? (stats.negative / total * 100).toFixed(1) : 0;
    const neutralPercent = total > 0 ? (stats.neutral / total * 100).toFixed(1) : 0;
    
    container.innerHTML = `
        <div class="row text-center">
            <div class="col-4">
                <div class="stat-card positive">
                    <div class="stat-number">${stats.positive}</div>
                    <div class="stat-label">Positive</div>
                    <div class="stat-percent">${positivePercent}%</div>
                </div>
            </div>
            <div class="col-4">
                <div class="stat-card negative">
                    <div class="stat-number">${stats.negative}</div>
                    <div class="stat-label">Negative</div>
                    <div class="stat-percent">${negativePercent}%</div>
                </div>
            </div>
            <div class="col-4">
                <div class="stat-card neutral">
                    <div class="stat-number">${stats.neutral}</div>
                    <div class="stat-label">Neutral</div>
                    <div class="stat-percent">${neutralPercent}%</div>
                </div>
            </div>
        </div>
        <div class="mt-3 text-center">
            <strong>Total Comments Analyzed: ${total}</strong>
        </div>
    `;
}
</script>
{% endblock %}
