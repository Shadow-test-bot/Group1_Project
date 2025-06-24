# Django Chat Application with Friend System

A real-time chat application built with Django, Django Channels, and WebSockets that allows users to communicate through private messages and group chats with a comprehensive friend management system.

## 🚀 Features

### Core Chat Features
- **Real-time messaging** using WebSockets and Django Channels
- **Private chat** between friends
- **Group chat** functionality with multiple participants
- **File attachments** support (images, documents, videos)
- **Message history** with timestamp tracking
- **Online/offline status** indicators
- **Typing indicators** in real-time
- **Message notifications** with unread count badges

### Friend Management System
- **Send friend requests** with optional messages
- **Accept/decline friend requests** with real-time notifications
- **Friend list management** with search functionality
- **Remove friends** capability
- **Privacy protection** - only friends can chat with each other
- **Friend request notifications** with live count updates
- **User discovery** - find and add new friends
- **Profile viewing** for friends and potential friends

### User Management
- **User registration** with profile pictures
- **User authentication** (login/logout)
- **Profile management** with customizable avatars
- **Account settings** with password change
- **User search** functionality

### UI/UX Features
- **Responsive design** with Bootstrap 4
- **Modern chat interface** with bubbles and avatars
- **Real-time notification badges**
- **Profile picture support** with fallback avatars
- **Intuitive navigation** with sidebar and top navigation
- **Loading states** and success/error messages

## 🏗️ Technical Architecture

### Backend Technologies
- **Django 5.1.2** - Web framework
- **Django Channels 4.x** - WebSocket support for real-time features
- **Django REST Framework** - API endpoints
- **SQLite** - Database (easily configurable to PostgreSQL/MySQL)
- **Python 3.8+** - Programming language

### Frontend Technologies
- **HTML5/CSS3** - Markup and styling
- **Bootstrap 4** - CSS framework for responsive design
- **JavaScript (Vanilla)** - Client-side interactivity
- **WebSocket API** - Real-time communication
- **Font Awesome** - Icons

### Key Django Apps
- **chat/** - Chat functionality and messaging
- **users/** - User management and friend system
- **chat_app/** - Main project configuration

## 📁 Project Structure

```
chat_debug/
├── chat/                          # Chat application
│   ├── models.py                  # Message, Group models
│   ├── views.py                   # Chat views and API endpoints
│   ├── consumers.py               # WebSocket consumers for real-time chat
│   ├── routing.py                 # WebSocket URL routing
│   ├── forms.py                   # Message and group forms
│   └── migrations/                # Database migrations
├── users/                         # User management and friend system
│   ├── models.py                  # User Profile, Friendship, FriendRequest models
│   ├── views.py                   # User management and friend system views
│   ├── forms.py                   # User and friend request forms
│   ├── urls.py                    # URL patterns for user features
│   └── migrations/                # Database migrations
├── chat_app/                      # Main project configuration
│   ├── settings.py                # Django settings
│   ├── urls.py                    # Main URL configuration
│   ├── asgi.py                    # ASGI configuration for channels
│   └── wsgi.py                    # WSGI configuration
├── templates/                     # HTML templates
│   ├── base.html                  # Base template with navigation
│   ├── home.html                  # Landing page
│   ├── chat.html                  # Main chat interface
│   ├── login.html                 # Login page
│   ├── signup.html                # Registration page
│   ├── chat/                      # Chat-specific templates
│   └── users/                     # User management templates
│       ├── friends_list.html      # Friend management interface
│       ├── find_friends.html      # User discovery and search
│       ├── profile.html           # User profile display
│       └── profile_edit.html      # Profile editing
├── media/                         # User uploads
│   ├── chat_attachments/          # Chat file attachments
│   └── profile_pics/              # User profile pictures
├── staticfiles/                   # Static files (CSS, JS, images)
├── db.sqlite3                     # SQLite database
├── manage.py                      # Django management script
└── requirements.txt               # Python dependencies
```

## 🗄️ Database Models

### User Profile Model
```python
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
```

### Friendship Model
```python
class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('blocked', 'Blocked'),
    ]
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendship_requests_sent')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendship_requests_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
```

### Message Model
```python
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    content = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
```

### Group Chat Model
```python
class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, related_name='chat_groups')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_groups')
    created_at = models.DateTimeField(auto_now_add=True)
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd chat_debug

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup
```bash
# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### Step 3: Run the Application
```bash
# Start the development server
python manage.py runserver

# Access the application at http://127.0.0.1:8000
```

## 📋 Dependencies

```txt
Django==5.1.2
channels==4.1.0
channels-redis==4.2.0
daphne==4.1.2
Pillow==10.0.0
redis==4.6.0
asgiref==3.7.2
```

## 🔌 API Endpoints

### Friend Management APIs
- `GET /users/api/friend-requests-count/` - Get pending friend request count
- `POST /users/friends/send-request/` - Send friend request
- `GET /users/friends/respond/<int:request_id>/<str:action>/` - Accept/decline friend request
- `POST /users/friends/remove/<int:user_id>/` - Remove friend
- `POST /users/friends/quick-add/<int:user_id>/` - Quick add friend

### Chat APIs
- `GET /chat/` - Main chat interface
- `POST /chat/send-message/` - Send message (AJAX)
- `GET /chat/messages/<int:user_id>/` - Get message history
- `POST /chat/upload-file/` - Upload file attachment

## 🔄 Real-time Features

### WebSocket Consumers
The application uses Django Channels WebSocket consumers for real-time features:

- **ChatConsumer** - Handles private messaging
- **GroupChatConsumer** - Handles group messaging  
- **NotificationConsumer** - Handles friend request notifications

### WebSocket Events
- `chat_message` - New message received
- `typing_indicator` - User typing status
- `user_status` - Online/offline status
- `friend_request` - New friend request notification
- `friend_accepted` - Friend request accepted

## 🎨 UI Features

### Chat Interface
- **Message bubbles** with sender/receiver styling
- **Profile pictures** in chat
- **Timestamp** display
- **File attachment** previews
- **Scroll to bottom** functionality
- **Responsive design** for mobile devices

### Friend Management Interface
- **Friend list** with search
- **Pending requests** section with counts
- **Sent requests** tracking
- **User discovery** with search
- **Profile viewing** modal
- **Real-time notification** badges

## 🛡️ Security Features

### Privacy Protection
- **Friend-only messaging** - Users can only chat with friends
- **Profile privacy** - Only friends can view full profiles
- **Request filtering** - Prevent spam friend requests

### Authentication
- **Session-based authentication**
- **Login required** decorators on protected views
- **User permission** checks for all friend operations

## 🔧 Configuration

### Settings Configuration
Key settings in `chat_app/settings.py`:

```python
# Channels configuration
ASGI_APPLICATION = 'chat_app.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static files configuration
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
```

## 🚀 Deployment

### Production Considerations
1. **Database**: Switch from SQLite to PostgreSQL/MySQL
2. **Redis**: Configure Redis for channel layers
3. **Static Files**: Use whitenoise or CDN for static file serving
4. **Media Files**: Use cloud storage (AWS S3, etc.)
5. **Environment Variables**: Use environment variables for sensitive settings
6. **HTTPS**: Configure SSL/TLS for WebSocket security

### Environment Variables
```bash
# .env file
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379
```
