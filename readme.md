# Alumni Network Web Application

A Flask-based web application for managing alumni networks and connecting graduates with their institutions.

## Features

### User Management
- Multi-role system (Students, Alumni, Administrators)
- Profile management with education history and work experience
- Profile picture upload capability
- Custom institution registration and verification system

### Networking
- Alumni search with advanced filters (skills, company, graduation year)
- Connection management system
- Private messaging between connected users
- Real-time unread message notifications

### Content Sharing
- Forum system for discussions
- Interest groups creation and management
- Event management with RSVP functionality
- Photo galleries for events and memories
- Job board for posting and finding opportunities

### Administration
- Institution verification system
- Alumni approval workflow
- Dashboard with analytics
- Content moderation capabilities

## Technical Requirements

- Python 3.x
- Flask 2.0.1
- SQLite database
- Additional dependencies listed in requirements.txt

## Installation

1. Clone the repository:

git clone <repository-url>
cd project

2. Create a virtual environment:

python -m venv venv
source venv/bin/activate  
On Windows: venv\Scripts\activate

3. Install dependencies:

pip install -r requirements.txt

4. RUN Flask application



## Environment Variables
Create a .env file in the project root with the following variables:

FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key

## Database Models

User
Institution
Event
ForumPost
ForumComment
InterestGroup
GroupMembership
GroupPost
PhotoGallery
Photo
Connection
Message
JobPosting


## Project Structure

project/
├── app.py              # Main application file
├── requirements.txt    # Project dependencies
├── instance/          # Instance-specific files
│   └── alumni.db     # SQLite database
├── static/           # Static files
│   ├── css/         # Stylesheets
│   ├── js/          # JavaScript files
│   └── profile_pictures/ # User uploads
└── templates/        # HTML templates