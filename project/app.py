from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import func
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alumni.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define upload folder and allowed extensions
UPLOAD_FOLDER = os.path.join('static', 'profile_pictures')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure the app with upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload directory if it doesn't exist
os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Add custom Jinja2 filter
@app.template_filter('from_json')
def from_json_filter(value):
    if value is None:
        return []
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# Models
class Institution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email_domain = db.Column(db.String(100), nullable=False, unique=True)
    website = db.Column(db.String(200))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    users = db.relationship('User', backref='institution', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'alumni', or 'admin'
    graduation_year = db.Column(db.Integer)
    company = db.Column(db.String(100))
    bio = db.Column(db.Text)
    linkedin_url = db.Column(db.String(200))
    profile_picture = db.Column(db.String(100))  # Path to profile picture
    skills = db.Column(db.Text)  # Comma-separated list of skills
    work_experience = db.Column(db.Text)  # JSON string of work experience
    education_history = db.Column(db.Text)  # JSON string of education history
    twitter_url = db.Column(db.String(200))
    github_url = db.Column(db.String(200))
    is_approved = db.Column(db.Boolean, default=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    institution_id = db.Column(db.Integer, db.ForeignKey('institution.id'), nullable=False)
    forum_posts = db.relationship('ForumPost', backref='author', lazy=True)
    forum_comments = db.relationship('ForumComment', backref='author', lazy=True)
    group_memberships = db.relationship('GroupMembership', backref='user', lazy=True)
    event_rsvps = db.relationship('EventRSVP', backref='user', lazy=True)
    uploaded_photos = db.relationship('Photo', backref='uploader', lazy=True)
    group_posts = db.relationship('GroupPost', backref='author', lazy=True, foreign_keys='GroupPost.author_id')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    institution_id = db.Column(db.Integer, db.ForeignKey('institution.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rsvps = db.relationship('EventRSVP', backref='event', lazy=True, cascade='all, delete-orphan')
    galleries = db.relationship('PhotoGallery', backref='event', lazy=True)

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    institution_id = db.Column(db.Integer, db.ForeignKey('institution.id'), nullable=False)
    comments = db.relationship('ForumComment', backref='post', lazy=True, cascade='all, delete-orphan')

class ForumComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)

class InterestGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    institution_id = db.Column(db.Integer, db.ForeignKey('institution.id'), nullable=False)
    members = db.relationship('GroupMembership', backref='group', lazy=True, cascade='all, delete-orphan')
    posts = db.relationship('GroupPost', backref='group', lazy=True, cascade='all, delete-orphan')

class GroupMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('interest_group.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
# Find the GroupPost class definition and update it like this:
class GroupPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('interest_group.id'), nullable=False)

class EventRSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'attending', 'maybe', 'declined'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class PhotoGallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    institution_id = db.Column(db.Integer, db.ForeignKey('institution.id'), nullable=False)
    
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gallery_id = db.Column(db.Integer, db.ForeignKey('photo_gallery.id'), nullable=False)


class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

    requester = db.relationship('User', foreign_keys=[requester_id], backref='sent_connections')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_connections')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')


User.location = db.Column(db.String(100))


class JobPosting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    salary_range = db.Column(db.String(50))
    application_link = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Foreign keys
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    institution_id = db.Column(db.Integer, db.ForeignKey('institution.id'), nullable=False)
    
    # Relationships
    poster = db.relationship('User', backref='job_postings')
    institution = db.relationship('Institution', backref='job_postings')
def init_db():
    with app.app_context():
        # Drop all tables
        # db.drop_all()
        # # Create all tables
        db.create_all()
        print("Database tables created successfully!")

# Initialize the database when the application starts
init_db()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper function to extract domain from email
def get_email_domain(email):
    return email.split('@')[1] if '@' in email else None

# Routes

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Get upcoming events
        upcoming_events = Event.query.filter_by(institution_id=current_user.institution_id)\
            .filter(Event.date >= datetime.now())\
            .order_by(Event.date).limit(3).all()
        
        # Get recent forum posts
        recent_posts = ForumPost.query.filter_by(institution_id=current_user.institution_id)\
            .order_by(ForumPost.created_at.desc()).limit(3).all()
        
        # Get user's group memberships
        user_groups = GroupMembership.query.filter_by(user_id=current_user.id).all()
        
        # Get pending connection requests
        pending_requests = Connection.query.filter_by(
            receiver_id=current_user.id,
            status='pending'
        ).order_by(Connection.created_at.desc()).all()
        
        # Get recent messages
        recent_messages = Message.query.filter(
            ((Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id))
        ).order_by(Message.created_at.desc()).limit(3).all()
        
        # Get a featured alumni (random selection)
        featured_alumni = User.query.filter_by(
            institution_id=current_user.institution_id,
            role='alumni',
            is_approved=True
        ).order_by(func.random()).first()
        
        return render_template('index.html', 
                              upcoming_events=upcoming_events,
                              recent_posts=recent_posts,
                              user_groups=user_groups,
                              pending_requests=pending_requests,
                              recent_messages=recent_messages,
                              featured_alumni=featured_alumni)
    else:
        # Show landing page for non-authenticated users
         return render_template('index.html', is_landing_page=True)

@app.route('/register-institution', methods=['GET', 'POST'])
def register_institution():
    if request.method == 'POST':
        name = request.form.get('name')
        email_domain = request.form.get('email_domain').lower()
        website = request.form.get('website')
        address = request.form.get('address')
        admin_email = request.form.get('admin_email')
        admin_password = request.form.get('admin_password')
        admin_name = request.form.get('admin_name')

        if Institution.query.filter_by(email_domain=email_domain).first():
            flash('Institution with this email domain already exists')
            return redirect(url_for('register_institution'))

        institution = Institution(
            name=name,
            email_domain=email_domain,
            website=website,
            address=address
        )
        db.session.add(institution)
        db.session.commit()

        # Create admin user for the institution
        admin = User(
            email=admin_email,
            name=admin_name,
            password=generate_password_hash(admin_password),
            role='admin',
            institution_id=institution.id
        )
        db.session.add(admin)
        db.session.commit()

        flash('Institution registered successfully. Please wait for verification.')
        return redirect(url_for('login'))
    return render_template('register_institution.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Check password
            if check_password_hash(user.password, password):
                # Check institution verification status
                if not user.institution.is_verified and user.role != 'admin':
                    flash('Your institution is not verified yet. Please wait for admin verification.', 'warning')
                    return redirect(url_for('login'))
                
                # Check alumni approval status
                if user.role == 'alumni' and not user.is_approved:
                    flash('Your account is pending approval from the institution admin.', 'info')
                    return redirect(url_for('login'))
                
                # Login the user
                login_user(user)
                next_page = request.args.get('next')
                
                # Redirect based on role
                if user.role == 'admin':
                    return redirect(next_page or url_for('admin_dashboard'))
                else:
                    return redirect(next_page or url_for('index'))
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('No account found with this email. Please check your email or register.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        institutions = Institution.query.filter_by(is_verified=True).all()
        print(f"Found {len(institutions)} verified institutions")
        for inst in institutions:
            print(f"Institution: {inst.name} (ID: {inst.id})")
        return render_template('register.html', institutions=institutions)
    
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        role = request.form.get('role')
        graduation_year = request.form.get('graduation_year')
        
        # For alumni, they can choose their institution
        if role == 'alumni':
            institution_id = request.form.get('institution_id')
            institution = Institution.query.get(institution_id)
            if not institution:
                flash('Please select a valid institution', 'danger')
                return redirect(url_for('register'))
        else:
            # For students and admins, use email domain to find institution
            email_domain = get_email_domain(email)
            institution = Institution.query.filter_by(email_domain=email_domain).first()
            if not institution:
                flash('Your institution is not registered. Please use your institution email.', 'danger')
                return redirect(url_for('register'))
            
            if not institution.is_verified:
                flash('Your institution is not verified yet', 'warning')
                return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create user with appropriate approval status
        is_approved = True if role != 'alumni' else False
        
        user = User(
            email=email,
            name=name,
            password=generate_password_hash(password),
            role=role,
            graduation_year=graduation_year,
            institution_id=institution.id,
            is_approved=is_approved
        )
        
        db.session.add(user)
        db.session.commit()
        
        if role == 'alumni':
            flash('Registration successful! Please wait for admin approval.', 'info')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

@app.route('/events')
@login_required
def events():
    # Get events only for the user's institution
    events = Event.query.filter_by(institution_id=current_user.institution_id)\
        .order_by(Event.date.desc()).all()
    return render_template('events.html', events=events)

@app.route('/events/<int:event_id>')
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if the event belongs to the user's institution
    if event.institution_id != current_user.institution_id:
        flash('You do not have permission to view this event.', 'danger')
        return redirect(url_for('events'))
    
    # Get user's RSVP status
    user_rsvp = EventRSVP.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()
    
    # Get RSVP counts
    attending_count = EventRSVP.query.filter_by(
        event_id=event_id,
        status='attending'
    ).count()
    
    maybe_count = EventRSVP.query.filter_by(
        event_id=event_id,
        status='maybe'
    ).count()
    
    # Get photo galleries for this event
    galleries = PhotoGallery.query.filter_by(event_id=event_id).all()
        
    return render_template('view_event.html', 
                          event=event, 
                          user_rsvp=user_rsvp,
                          attending_count=attending_count,
                          maybe_count=maybe_count,
                          galleries=galleries)

@app.route('/forum')
@login_required
def forum():
    # Get forum posts only for the user's institution
    posts = ForumPost.query.filter_by(institution_id=current_user.institution_id)\
        .order_by(ForumPost.created_at.desc()).all()
    return render_template('forum.html', posts=posts)

@app.route('/forum/post/<int:post_id>')
@login_required
def view_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    
    # Check if the post belongs to the user's institution
    if post.institution_id != current_user.institution_id:
        flash('You do not have permission to view this post.', 'danger')
        return redirect(url_for('forum'))
        
    return render_template('view_post.html', post=post)

@app.route('/forum/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        post = ForumPost(
            title=title,
            content=content,
            author_id=current_user.id,
            institution_id=current_user.institution_id  # Automatically set to user's institution
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('forum'))
        
    return render_template('new_post.html')

@app.route('/forum/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = ForumPost.query.get_or_404(post_id)
    
    # Check if the post belongs to the user's institution
    if post.institution_id != current_user.institution_id:
        flash('You do not have permission to comment on this post.', 'danger')
        return redirect(url_for('forum'))
        
    content = request.form.get('content')
    if content:
        comment = ForumComment(
            content=content,
            author_id=current_user.id,
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.email = request.form.get('email')
        current_user.graduation_year = request.form.get('graduation_year')
        current_user.bio = request.form.get('bio')
        current_user.linkedin_url = request.form.get('linkedin_url')
        current_user.twitter_url = request.form.get('twitter_url')
        current_user.github_url = request.form.get('github_url')
        current_user.skills = request.form.get('skills')
        current_user.location = request.form.get('location') 
        
        # Handle work experience
        work_experience = []
        for i in range(1, 4):  # Allow up to 3 work experiences
            company = request.form.get(f'company_{i}')
            position = request.form.get(f'position_{i}')
            start_date = request.form.get(f'start_date_{i}')
            end_date = request.form.get(f'end_date_{i}')
            if company and position:
                work_experience.append({
                    'company': company,
                    'position': position,
                    'start_date': start_date,
                    'end_date': end_date
                })
        current_user.work_experience = json.dumps(work_experience)
        
        # Handle education history
        education_history = []
        for i in range(1, 3):  # Allow up to 2 education entries
            institution = request.form.get(f'edu_institution_{i}')
            degree = request.form.get(f'degree_{i}')
            field = request.form.get(f'field_{i}')
            grad_year = request.form.get(f'edu_grad_year_{i}')
            if institution and degree:
                education_history.append({
                    'institution': institution,
                    'degree': degree,
                    'field': field,
                    'graduation_year': grad_year
                })
        current_user.education_history = json.dumps(education_history)
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename and allowed_file(file.filename):
                # Generate a unique filename
                filename = secure_filename(f"{current_user.id}_{int(datetime.now().timestamp())}_{file.filename}")
                
                # Ensure the upload directory exists
                upload_path = os.path.join(app.root_path, UPLOAD_FOLDER)
                os.makedirs(upload_path, exist_ok=True)
                
                # Save the file
                file_path = os.path.join(upload_path, filename)
                file.save(file_path)
                
                # Update the user's profile picture path
                current_user.profile_picture = filename
                print(f"Profile picture saved to: {file_path}")  # Debug print
        
        if current_user.role == 'alumni':
            current_user.company = request.form.get('company')
        
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        if current_password and new_password:
            if check_password_hash(current_user.password, current_password):
                current_user.password = generate_password_hash(new_password)
            else:
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('edit_profile'))
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Parse existing work experience and education history
    work_experience = json.loads(current_user.work_experience) if current_user.work_experience else []
    education_history = json.loads(current_user.education_history) if current_user.education_history else []
    
    return render_template('edit_profile.html', 
                         work_experience=work_experience,
                         education_history=education_history)

@app.route('/jobs')
@login_required
def jobs():
    # Get all job postings for the user's institution
    job_postings = JobPosting.query.filter_by(institution_id=current_user.institution_id)\
        .order_by(JobPosting.created_at.desc()).all()
    
    return render_template('jobs.html', job_postings=job_postings)

# View a specific job posting
@app.route('/jobs/<int:job_id>')
@login_required
def view_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    
    # Check if job belongs to user's institution
    if job.institution_id != current_user.institution_id:
        flash('You do not have permission to view this job posting', 'danger')
        return redirect(url_for('jobs'))
    
    return render_template('view_job.html', job=job)

# Post a new job (only for alumni and admin)
@app.route('/jobs/post', methods=['GET', 'POST'])
@login_required
def post_job():
    # Check if user is alumni or admin
    if current_user.role not in ['alumni', 'admin']:
        flash('Only alumni and administrators can post jobs', 'danger')
        return redirect(url_for('jobs'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        company = request.form.get('company')
        location = request.form.get('location')
        description = request.form.get('description')
        requirements = request.form.get('requirements')
        salary_range = request.form.get('salary_range')
        application_link = request.form.get('application_link')
        
        # Parse expiration date
        expires_at_str = request.form.get('expires_at')
        expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d') if expires_at_str else None
        
        job = JobPosting(
            title=title,
            company=company,
            location=location,
            description=description,
            requirements=requirements,
            salary_range=salary_range,
            application_link=application_link,
            expires_at=expires_at,
            poster_id=current_user.id,
            institution_id=current_user.institution_id
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash('Job posting created successfully!', 'success')
        return redirect(url_for('jobs'))
    
    return render_template('post_job.html')

# Edit a job posting
@app.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    
    # Check if user is the poster or an admin
    if job.poster_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to edit this job posting', 'danger')
        return redirect(url_for('jobs'))
    
    if request.method == 'POST':
        job.title = request.form.get('title')
        job.company = request.form.get('company')
        job.location = request.form.get('location')
        job.description = request.form.get('description')
        job.requirements = request.form.get('requirements')
        job.salary_range = request.form.get('salary_range')
        job.application_link = request.form.get('application_link')
        
        # Parse expiration date
        expires_at_str = request.form.get('expires_at')
        job.expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d') if expires_at_str else None
        
        db.session.commit()
        
        flash('Job posting updated successfully!', 'success')
        return redirect(url_for('view_job', job_id=job.id))
    
    return render_template('post_job.html', job=job)

# Delete a job posting
@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    job = JobPosting.query.get_or_404(job_id)
    
    # Check if user is the poster or an admin
    if job.poster_id != current_user.id and current_user.role != 'admin':
        flash('You do not have permission to delete this job posting', 'danger')
        return redirect(url_for('jobs'))
    
    db.session.delete(job)
    db.session.commit()
    
    flash('Job posting deleted successfully!', 'success')
    return redirect(url_for('jobs'))

@app.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('settings.html')

@app.route('/groups')
@login_required
def groups():
    groups = InterestGroup.query.filter_by(institution_id=current_user.institution_id).all()
    return render_template('groups.html', groups=groups)

@app.route('/groups/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        group = InterestGroup(
            name=name,
            description=description,
            creator_id=current_user.id,
            institution_id=current_user.institution_id
        )
        db.session.add(group)
        db.session.commit()
        
        # Add creator as admin member
        membership = GroupMembership(
            user_id=current_user.id,
            group_id=group.id,
            is_admin=True
        )
        db.session.add(membership)
        db.session.commit()
        
        flash('Group created successfully!', 'success')
        return redirect(url_for('view_group', group_id=group.id))
    
    return render_template('create_group.html')

@app.route('/groups/<int:group_id>')
@login_required
def view_group(group_id):
    group = InterestGroup.query.get_or_404(group_id)
    
    # Check if group belongs to user's institution
    if group.institution_id != current_user.institution_id:
        flash('You do not have permission to view this group', 'danger')
        return redirect(url_for('groups'))
    
    # Check if user is a member
    is_member = GroupMembership.query.filter_by(
        user_id=current_user.id, 
        group_id=group.id
    ).first() is not None
    
    # Get all members
    memberships = GroupMembership.query.filter_by(group_id=group.id).all()
    members = [User.query.get(m.user_id) for m in memberships]
    
    # Get group posts
    posts = GroupPost.query.filter_by(group_id=group.id).order_by(GroupPost.created_at.desc()).all()
    
    return render_template('view_group.html', 
                          group=group, 
                          is_member=is_member, 
                          members=members,
                          posts=posts)

@app.route('/groups/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    group = InterestGroup.query.get_or_404(group_id)
    
    # Check if group belongs to user's institution
    if group.institution_id != current_user.institution_id:
        flash('You do not have permission to join this group', 'danger')
        return redirect(url_for('groups'))
    
    # Check if already a member
    existing_membership = GroupMembership.query.filter_by(
        user_id=current_user.id, 
        group_id=group.id
    ).first()
    
    if existing_membership:
        flash('You are already a member of this group', 'info')
    else:
        membership = GroupMembership(
            user_id=current_user.id,
            group_id=group.id
        )
        db.session.add(membership)
        db.session.commit()
        flash('You have joined the group successfully!', 'success')
    
    return redirect(url_for('view_group', group_id=group.id))

@app.route('/groups/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id, 
        group_id=group_id
    ).first_or_404()
    
    db.session.delete(membership)
    db.session.commit()
    flash('You have left the group', 'info')
    return redirect(url_for('groups'))

@app.route('/groups/<int:group_id>/post', methods=['POST'])
@login_required
def create_group_post(group_id):
    group = InterestGroup.query.get_or_404(group_id)
    
    # Check if user is a member
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id, 
        group_id=group.id
    ).first()
    
    if not membership:
        flash('You must be a member to post in this group', 'danger')
        return redirect(url_for('view_group', group_id=group.id))
    
    content = request.form.get('content')
    if content:
        post = GroupPost(
            content=content,
            author_id=current_user.id,
            group_id=group.id
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
    
    return redirect(url_for('view_group', group_id=group.id))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Get the admin's institution
    admin_institution = current_user.institution
    
    # Get user counts for the admin's institution
    student_count = User.query.filter_by(
        institution_id=admin_institution.id, 
        role='student'
    ).count()
    
    alumni_count = User.query.filter_by(
        institution_id=admin_institution.id, 
        role='alumni',
        is_approved=True
    ).count()
    
    admin_count = User.query.filter_by(
        institution_id=admin_institution.id, 
        role='admin'
    ).count()
    
    # Get pending alumni for the admin's institution
    pending_alumni = User.query.filter_by(
        institution_id=admin_institution.id,
        role='alumni',
        is_approved=False
    ).all()
    
    # Get pending and verified institutions
    pending_institutions = Institution.query.filter_by(is_verified=False).all()
    verified_institutions = Institution.query.filter_by(is_verified=True).all()
    
    return render_template('admin_dashboard.html', 
                         institution=admin_institution,
                         student_count=student_count,
                         alumni_count=alumni_count,
                         admin_count=admin_count,
                         pending_alumni=pending_alumni,
                         pending_institutions=pending_institutions,
                         verified_institutions=verified_institutions)

@app.route('/admin/verify/<int:institution_id>', methods=['POST'])
@login_required
def verify_institution(institution_id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    institution = Institution.query.get_or_404(institution_id)
    institution.is_verified = True
    db.session.commit()
    
    flash(f'Institution {institution.name} has been verified successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:institution_id>', methods=['POST'])
@login_required
def reject_institution(institution_id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    institution = Institution.query.get_or_404(institution_id)
    # Delete all users associated with this institution
    User.query.filter_by(institution_id=institution.id).delete()
    # Delete the institution
    db.session.delete(institution)
    db.session.commit()
    
    flash(f'Institution {institution.name} has been rejected and removed')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_alumni/<int:user_id>', methods=['POST'])
@login_required
def approve_alumni(user_id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.institution_id != current_user.institution_id:
        flash('Access denied')
        return redirect(url_for('admin_dashboard'))
    
    user.is_approved = True
    db.session.commit()
    
    flash(f'Alumni {user.name} has been approved successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_alumni/<int:user_id>', methods=['POST'])
@login_required
def reject_alumni(user_id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.institution_id != current_user.institution_id:
        flash('Access denied')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Alumni {user.name} has been rejected and removed')
    return redirect(url_for('admin_dashboard'))

@app.route('/events/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M')
        
        event = Event(
            title=title,
            description=description,
            date=date,
            organizer_id=current_user.id,
            institution_id=current_user.institution_id  # Automatically set to user's institution
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('events'))
        
    return render_template('add_event.html')

@app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id:
        flash('You do not have permission to edit this event')
        return redirect(url_for('events'))
        
    if request.method == 'POST':
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        event.date = datetime.strptime(request.form.get('date'), '%Y-%m-%dT%H:%M')
        
        db.session.commit()
        flash('Event updated successfully')
        return redirect(url_for('events'))
        
    return render_template('add_event.html', event=event)

@app.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.organizer_id != current_user.id:
        flash('You do not have permission to delete this event')
        return redirect(url_for('events'))
        
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully')
    return redirect(url_for('events'))

   
    
    
@app.route('/events/<int:event_id>/rsvp/<status>', methods=['POST'])
@login_required
def rsvp_event(event_id, status):
    event = Event.query.get_or_404(event_id)
    
    # Check if event belongs to user's institution
    if event.institution_id != current_user.institution_id:
        flash('You do not have permission to RSVP to this event', 'danger')
        return redirect(url_for('events'))
    
    # Validate status
    if status not in ['attending', 'maybe', 'declined']:
        flash('Invalid RSVP status', 'danger')
        return redirect(url_for('view_event', event_id=event_id))
    
    # Check if already RSVP'd
    existing_rsvp = EventRSVP.query.filter_by(
        user_id=current_user.id, 
        event_id=event_id
    ).first()
    
    if existing_rsvp:
        existing_rsvp.status = status
        flash('Your RSVP has been updated', 'success')
    else:
        rsvp = EventRSVP(
            user_id=current_user.id,
            event_id=event_id,
            status=status
        )
        db.session.add(rsvp)
        flash('Your RSVP has been recorded', 'success')
    
    db.session.commit()
    return redirect(url_for('view_event', event_id=event_id))




    
    
@app.route('/galleries')
@login_required
def galleries():
    galleries = PhotoGallery.query.filter_by(
        institution_id=current_user.institution_id
    ).order_by(PhotoGallery.created_at.desc()).all()
    return render_template('galleries.html', galleries=galleries)

@app.route('/galleries/create', methods=['GET', 'POST'])
@login_required
def create_gallery():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_id = request.form.get('event_id') or None
        
        gallery = PhotoGallery(
            title=title,
            description=description,
            event_id=event_id,
            creator_id=current_user.id,
            institution_id=current_user.institution_id
        )
        db.session.add(gallery)
        db.session.commit()
        
        flash('Gallery created successfully!', 'success')
        return redirect(url_for('view_gallery', gallery_id=gallery.id))
    
    # Get events for dropdown
    events = Event.query.filter_by(
        institution_id=current_user.institution_id
    ).order_by(Event.date.desc()).all()
    
    return render_template('create_gallery.html', events=events)

@app.route('/galleries/<int:gallery_id>')
@login_required
def view_gallery(gallery_id):
    gallery = PhotoGallery.query.get_or_404(gallery_id)
    
    # Check if gallery belongs to user's institution
    if gallery.institution_id != current_user.institution_id:
        flash('You do not have permission to view this gallery', 'danger')
        return redirect(url_for('galleries'))
    
    photos = Photo.query.filter_by(gallery_id=gallery.id).all()
    
    return render_template('view_gallery.html', gallery=gallery, photos=photos)

@app.route('/galleries/<int:gallery_id>/upload', methods=['GET', 'POST'])
@login_required
def upload_photo(gallery_id):
    gallery = PhotoGallery.query.get_or_404(gallery_id)
    
    # Check if gallery belongs to user's institution
    if gallery.institution_id != current_user.institution_id:
        flash('You do not have permission to upload to this gallery', 'danger')
        return redirect(url_for('galleries'))
    
    if request.method == 'POST':
        caption = request.form.get('caption')
        
        if 'photo' not in request.files:
            flash('No photo selected', 'danger')
            return redirect(request.url)
        
        file = request.files['photo']
        
        if file.filename == '':
            flash('No photo selected', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(f"gallery_{gallery_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            
            # Create the static directory and profile_pictures subdirectory if they don't exist
            static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
            os.makedirs(static_dir, exist_ok=True)
            
            upload_dir = os.path.join(static_dir, 'profile_pictures')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            photo = Photo(
                filename=filename,
                caption=caption,
                uploader_id=current_user.id,
                gallery_id=gallery.id
            )
            db.session.add(photo)
            db.session.commit()
            
            flash('Photo uploaded successfully!', 'success')
            return redirect(url_for('view_gallery', gallery_id=gallery.id))
    
    return render_template('upload_photo.html', gallery=gallery)



@app.route('/photos/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    gallery_id = photo.gallery_id
    
    # Check if user is the uploader or gallery creator
    gallery = PhotoGallery.query.get(gallery_id)
    if photo.uploader_id != current_user.id and gallery.creator_id != current_user.id:
        flash('You do not have permission to delete this photo', 'danger')
        return redirect(url_for('view_gallery', gallery_id=gallery_id))
    
    # Delete the file from the filesystem
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'profile_pictures', photo.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # Log the error but continue with database deletion
        print(f"Error deleting file: {e}")
    
    # Delete from database
    db.session.delete(photo)
    db.session.commit()
    
    flash('Photo deleted successfully!', 'success')
    return redirect(url_for('view_gallery', gallery_id=gallery_id))


@app.route('/alumni/search', methods=['GET', 'POST'])
@login_required
def search_alumni():
    # Get all skills from users for the filter dropdown
    all_skills = set()
    users_with_skills = User.query.filter(User.skills.isnot(None)).all()
    for user in users_with_skills:
        if user.skills:
            skills_list = [skill.strip() for skill in user.skills.split(',')]
            all_skills.update(skills_list)
    
    # Get all companies for the filter dropdown
    all_companies = db.session.query(User.company).filter(
        User.company.isnot(None), 
        User.company != ''
    ).distinct().all()
    all_companies = [company[0] for company in all_companies]
    
    # Get graduation years range
    min_year = db.session.query(db.func.min(User.graduation_year)).scalar() or datetime.now().year - 50
    max_year = db.session.query(db.func.max(User.graduation_year)).scalar() or datetime.now().year
    
    # Default query - all approved alumni from user's institution
    query = User.query.filter_by(
        institution_id=current_user.institution_id,
        is_approved=True
    )
    
    # Apply filters if form is submitted
    if request.method == 'POST':
        name = request.form.get('name', '')
        min_grad_year = request.form.get('min_grad_year')
        max_grad_year = request.form.get('max_grad_year')
        company = request.form.get('company')
        skill = request.form.get('skill')
        location = request.form.get('location')
        
        if name:
            query = query.filter(User.name.ilike(f'%{name}%'))
        
        if min_grad_year and min_grad_year.isdigit():
            query = query.filter(User.graduation_year >= int(min_grad_year))
            
        if max_grad_year and max_grad_year.isdigit():
            query = query.filter(User.graduation_year <= int(max_grad_year))
            
        if company and company != 'all':
            query = query.filter(User.company == company)
            
        if skill and skill != 'all':
            query = query.filter(User.skills.ilike(f'%{skill}%'))
            
        if location:
            query = query.filter(User.location.ilike(f'%{location}%'))
    
    # Execute the query
    alumni = query.all()
    
    # Get connection status for each alumni
    connection_status = {}
    for alum in alumni:
        if alum.id == current_user.id:
            connection_status[alum.id] = 'self'
            continue
            
        # Check if there's a connection request from current user to this alumni
        sent_request = Connection.query.filter_by(
            requester_id=current_user.id,
            receiver_id=alum.id
        ).first()
        
        if sent_request:
            connection_status[alum.id] = sent_request.status
            continue
            
        # Check if there's a connection request from this alumni to current user
        received_request = Connection.query.filter_by(
            requester_id=alum.id,
            receiver_id=current_user.id
        ).first()
        
        if received_request:
            connection_status[alum.id] = f'received_{received_request.status}'
            continue
            
        connection_status[alum.id] = 'none'
    
    return render_template(
        'search_alumni.html',
        alumni=alumni,
        all_skills=sorted(all_skills),
        all_companies=sorted(all_companies),
        min_year=min_year,
        max_year=max_year,
        connection_status=connection_status
    )
    
@app.route('/connections')
@login_required
def connections():
    # Get all accepted connections
    sent_connections = Connection.query.filter_by(
        requester_id=current_user.id,
        status='accepted'
    ).all()
    
    received_connections = Connection.query.filter_by(
        receiver_id=current_user.id,
        status='accepted'
    ).all()
    
    # Get pending connection requests
    pending_requests = Connection.query.filter_by(
        receiver_id=current_user.id,
        status='pending'
    ).all()
    
    # Combine connections
    connections = []
    for conn in sent_connections:
        connections.append({
            'user': conn.receiver,
            'connection_id': conn.id,
            'created_at': conn.created_at
        })
    
    for conn in received_connections:
        connections.append({
            'user': conn.requester,
            'connection_id': conn.id,
            'created_at': conn.created_at
        })
    
    # Sort connections by name
    connections.sort(key=lambda x: x['user'].name)
    
    return render_template(
        'connections.html',
        connections=connections,
        pending_requests=pending_requests
    )

@app.route('/connection/request/<int:user_id>', methods=['POST'])
@login_required
def request_connection(user_id):
    # Check if user exists and is from the same institution
    user = User.query.get_or_404(user_id)
    if user.institution_id != current_user.institution_id:
        flash('You can only connect with users from your institution.', 'danger')
        return redirect(url_for('search_alumni'))
    
    # Check if connection already exists
    existing_sent = Connection.query.filter_by(
        requester_id=current_user.id,
        receiver_id=user_id
    ).first()
    
    existing_received = Connection.query.filter_by(
        requester_id=user_id,
        receiver_id=current_user.id
    ).first()
    
    if existing_sent or existing_received:
        flash('A connection request already exists with this user.', 'warning')
        return redirect(url_for('search_alumni'))
    
    # Create new connection request
    connection = Connection(
        requester_id=current_user.id,
        receiver_id=user_id,
        status='pending'
    )
    
    db.session.add(connection)
    db.session.commit()
    
    flash(f'Connection request sent to {user.name}.', 'success')
    return redirect(url_for('search_alumni'))

@app.route('/connection/accept/<int:connection_id>', methods=['POST'])
@login_required
def accept_connection(connection_id):
    connection = Connection.query.get_or_404(connection_id)
    
    # Verify the current user is the receiver
    if connection.receiver_id != current_user.id:
        flash('You are not authorized to accept this connection.', 'danger')
        return redirect(url_for('connections'))
    
    connection.status = 'accepted'
    db.session.commit()
    
    flash('Connection request accepted.', 'success')
    return redirect(url_for('connections'))

@app.route('/connection/reject/<int:connection_id>', methods=['POST'])
@login_required
def reject_connection(connection_id):
    connection = Connection.query.get_or_404(connection_id)
    
    # Verify the current user is the receiver
    if connection.receiver_id != current_user.id:
        flash('You are not authorized to reject this connection.', 'danger')
        return redirect(url_for('connections'))
    
    connection.status = 'rejected'
    db.session.commit()
    
    flash('Connection request rejected.', 'success')
    return redirect(url_for('connections'))

@app.route('/connection/remove/<int:connection_id>', methods=['POST'])
@login_required
def remove_connection(connection_id):
    connection = Connection.query.get_or_404(connection_id)
    
    # Verify the current user is part of the connection
    if connection.requester_id != current_user.id and connection.receiver_id != current_user.id:
        flash('You are not authorized to remove this connection.', 'danger')
        return redirect(url_for('connections'))
    
    db.session.delete(connection)
    db.session.commit()
    
    flash('Connection removed.', 'success')
    return redirect(url_for('connections'))

@app.route('/messages')
@login_required
def messages():
    # Get all users the current user has conversations with
    conversations_query = db.session.query(
        Message.sender_id, Message.receiver_id
    ).filter(
        db.or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        )
    ).distinct()
    
    # Extract unique user IDs from conversations
    user_ids = set()
    for sender_id, receiver_id in conversations_query:
        if sender_id != current_user.id:
            user_ids.add(sender_id)
        if receiver_id != current_user.id:
            user_ids.add(receiver_id)
    
    # Get user objects for the conversations
    conversation_users = User.query.filter(User.id.in_(user_ids)).all()
    
    # Get unread message counts for each conversation
    unread_counts = {}
    for user in conversation_users:
        count = Message.query.filter_by(
            sender_id=user.id,
            receiver_id=current_user.id,
            is_read=False
        ).count()
        unread_counts[user.id] = count
    
    # Get all connections for messaging new users
    connections = []
    sent_connections = Connection.query.filter_by(
        requester_id=current_user.id,
        status='accepted'
    ).all()
    
    received_connections = Connection.query.filter_by(
        receiver_id=current_user.id,
        status='accepted'
    ).all()
    
    for conn in sent_connections:
        if conn.receiver_id not in user_ids:  # Only add if not already in conversations
            connections.append(conn.receiver)
    
    for conn in received_connections:
        if conn.requester_id not in user_ids:  # Only add if not already in conversations
            connections.append(conn.requester)
    
    return render_template(
        'messages.html',
        conversation_users=conversation_users,
        unread_counts=unread_counts,
        connections=connections
    )

@app.route('/messages/<int:user_id>', methods=['GET', 'POST'])
@login_required
def view_conversation(user_id):
    # Check if user exists
    other_user = User.query.get_or_404(user_id)
    
    # Check if users are connected
    connection = Connection.query.filter(
        db.or_(
            db.and_(Connection.requester_id == current_user.id, Connection.receiver_id == user_id),
            db.and_(Connection.requester_id == user_id, Connection.receiver_id == current_user.id)
        ),
        Connection.status == 'accepted'
    ).first()
    
    # Allow messaging only if users are connected or have existing conversation
    existing_conversation = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            db.and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).first()
    
    if not connection and not existing_conversation:
        flash('You need to be connected with this user to send messages.', 'warning')
        return redirect(url_for('messages'))
    
    # Handle new message submission
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            message = Message(
                sender_id=current_user.id,
                receiver_id=user_id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            return redirect(url_for('view_conversation', user_id=user_id))
    
    # Get all messages between the two users
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            db.and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at).all()
    
    # Mark unread messages as read
    unread_messages = Message.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user.id,
        is_read=False
    ).all()
    
    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()
    
    return render_template(
        'conversation.html',
        other_user=other_user,
        messages=messages
    )

@app.route('/messages/new/<int:user_id>')
@login_required
def new_message(user_id):
    # Check if user exists
    other_user = User.query.get_or_404(user_id)
    
    # Check if users are connected
    connection = Connection.query.filter(
        db.or_(
            db.and_(Connection.requester_id == current_user.id, Connection.receiver_id == user_id),
            db.and_(Connection.requester_id == user_id, Connection.receiver_id == current_user.id)
        ),
        Connection.status == 'accepted'
    ).first()
    
    if not connection:
        flash('You need to be connected with this user to send messages.', 'warning')
        return redirect(url_for('messages'))
    
    return redirect(url_for('view_conversation', user_id=user_id))

@app.context_processor
def inject_unread_message_count():
    if current_user.is_authenticated:
        unread_count = Message.query.filter_by(
            receiver_id=current_user.id,
            is_read=False
        ).count()
        return {'unread_message_count': unread_count}
    return {'unread_message_count': 0}

# Add this after creating the app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(os.path.join(app.root_path, UPLOAD_FOLDER)):
    os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)