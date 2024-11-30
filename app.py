from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib
import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime, timedelta
import time
import os
import secrets
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

if not os.path.exists('instance'):
    os.makedirs('instance')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db = SQLAlchemy(app)

# MediaPipe and OpenCV setup
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


# Database Models
# Define the database models

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)

    # Relationships with logs
    pushups_logs = db.relationship('PushUpsLog', backref='user', lazy=True)
    squats_logs = db.relationship('SquatsLog', backref='user', lazy=True)
    planks_logs = db.relationship('PlanksLog', backref='user', lazy=True)
    lunges_logs = db.relationship('LungesLog', backref='user', lazy=True)
    pullups_logs = db.relationship('PullUpsLog', backref='user', lazy=True)



class PushUpsLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    reps = db.Column(db.Integer, nullable=False)  # Number of repetitions
    sets = db.Column(db.Integer, nullable=False, default=1)  # Number of sets completed
    duration = db.Column(db.Integer, nullable=False)  # Duration in seconds
    difficulty = db.Column(db.String(50), nullable=False)  # Difficulty level (e.g., Beginner, Advanced)
    rest_period = db.Column(db.Integer, nullable=True)  # Rest period between sets in seconds
    calories_burned = db.Column(db.Float, nullable=True)  # Estimated calories burned
    form_notes = db.Column(db.String(255), nullable=True)  # Notes on form or technique

class SquatsLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    sets = db.Column(db.Integer, nullable=False, default=1)
    duration = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=True)  # Weight used, if any, in kg
    rest_period = db.Column(db.Integer, nullable=True)
    calories_burned = db.Column(db.Float, nullable=True)
    depth = db.Column(db.String(50), nullable=True)  # Squat depth (e.g., "Parallel", "Below parallel")
    form_notes = db.Column(db.String(255), nullable=True)

class PlanksLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in seconds
    stage = db.Column(db.String(50), nullable=True)  # E.g., Forearm plank, Side plank
    rest_period = db.Column(db.Integer, nullable=True)  # Rest period between plank holds
    calories_burned = db.Column(db.Float, nullable=True)
    form_notes = db.Column(db.String(255), nullable=True)

class LungesLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    sets = db.Column(db.Integer, nullable=False, default=1)
    duration = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=True)  # Weight in kg used for added resistance
    rest_period = db.Column(db.Integer, nullable=True)
    calories_burned = db.Column(db.Float, nullable=True)
    stance = db.Column(db.String(50), nullable=True)  # E.g., Forward lunge, Reverse lunge
    form_notes = db.Column(db.String(255), nullable=True)

class PullUpsLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    sets = db.Column(db.Integer, nullable=False, default=1)
    duration = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)  # Difficulty level or assisted weight
    rest_period = db.Column(db.Integer, nullable=True)
    calories_burned = db.Column(db.Float, nullable=True)
    grip_type = db.Column(db.String(50), nullable=True)  # E.g., Overhand, Underhand, Neutral
    form_notes = db.Column(db.String(255), nullable=True)

def analyze_pushups_video(video_path, user_notes):
    # Initialize MediaPipe pose detection
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(video_path)
    
    # Initialize form_notes with user-provided notes
    form_notes = f"{user_notes}; "  # Keep user notes

    reps = 0
    sets = 0
    in_pushup = False
    start_time = datetime.now()
    end_time = None
    difficulty = "Beginner"
    calories_burned = 0.0
    rest_period = 0

    # Process the video frame by frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            # Logic for calculating pushups based on body landmarks
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            left_elbow = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW]
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            right_elbow = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW]

            # Detect a push-up movement
            if left_elbow.y < left_shoulder.y and right_elbow.y < right_shoulder.y:
                if not in_pushup:
                    reps += 1
                    in_pushup = True
            elif left_elbow.y > left_shoulder.y and right_elbow.y > right_shoulder.y:
                in_pushup = False

        end_time = datetime.now()

    duration = (end_time - start_time).seconds if end_time and start_time else 0
    sets = reps // 10  # Example: Every 10 reps make a new set

    # Estimate calories burned
    calories_burned = reps * 0.1  # Simplified formula

    cap.release()

    return reps, sets, duration, difficulty, rest_period, calories_burned, form_notes

def analyze_squats_video(video_path, user_notes, weight):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(video_path)

    reps = 0
    sets = 1
    weight = weight  # Example weight in kg
    calories_burned = 0.0
    rest_period = 0
    depth = "Parallel"
    form_notes = f"{user_notes}; "
    in_squat = False
    in_rest = False
    start_time = datetime.now()
    end_time = None
    last_squat_time = datetime.now()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            left_hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
            left_knee = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE]
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]

            # Calculate depth of squat based on hip and knee positions
            if left_hip.y > left_knee.y:
                depth = "Above parallel"
            elif left_hip.y < left_knee.y:
                depth = "Below parallel"
            else:
                depth = "Parallel"

            # Detect squat movement based on hip and knee
            if left_hip.y > left_knee.y:
                if not in_squat:
                    reps += 1
                    in_squat = True
                    last_squat_time = datetime.now()
            else:
                in_squat = False

            # Calculate rest period (time between sets)
            if reps > 0 and (datetime.now() - last_squat_time).seconds > 10:  # example rest time threshold
                in_rest = True
                rest_period = (datetime.now() - last_squat_time).seconds
            else:
                in_rest = False
                rest_period = 0

        end_time = datetime.now()

    duration = (end_time - start_time).seconds if end_time and start_time else 0
    calories_burned = reps * 0.15  # Adjusted for squats

    cap.release()
    return reps, sets, duration, weight, calories_burned, rest_period, depth, form_notes

def analyze_planks_video(video_path, user_notes, weight):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(video_path)

    duration = 0
    calories_burned = 0.0
    rest_period = 0
    form_notes = f"{user_notes}; "
    stage = "Forearm plank"
    start_time = datetime.now()
    last_rest_time = datetime.now()
    in_plank = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            # Example: Identify pose for forearm vs. side plank
            left_elbow = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW]
            right_elbow = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW]
            
            if left_elbow.visibility > 0.5 and right_elbow.visibility > 0.5:
                in_plank = True
                stage = "Forearm plank"
            else:
                in_plank = False
                stage = "Side plank"

        duration = (datetime.now() - start_time).seconds
        rest_period = (datetime.now() - last_rest_time).seconds if not in_plank else 0
        calories_burned = duration * 0.12  # Calories burned estimate

    cap.release()
    return duration, stage, rest_period, calories_burned, form_notes

def analyze_lunges_video(video_path, user_notes, weight):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(video_path)

    reps = 0
    sets = 1
    weight = weight  # Example weight in kg
    calories_burned = 0.0
    rest_period = 0
    stance = "Forward Lunge"
    form_notes = f"{user_notes}; "
    in_lunge = False
    in_rest = False
    start_time = datetime.now()
    end_time = None
    last_lunge_time = datetime.now()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            left_hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP]
            left_knee = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE]
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]

            # Detect lunge stance based on leg position
            if left_hip.x > left_knee.x:
                stance = "Forward Lunge"
            else:
                stance = "Reverse Lunge"

            # Detect lunge movement based on knee angle
            if left_knee.y < left_hip.y:  # Indicates a lunge
                if not in_lunge:
                    reps += 1
                    in_lunge = True
                    last_lunge_time = datetime.now()
            else:
                in_lunge = False

            # Calculate rest period (time between sets)
            if reps > 0 and (datetime.now() - last_lunge_time).seconds > 10:  # Example rest time threshold
                in_rest = True
                rest_period = (datetime.now() - last_lunge_time).seconds
            else:
                in_rest = False
                rest_period = 0

        end_time = datetime.now()

    duration = (end_time - start_time).seconds if end_time and start_time else 0
    calories_burned = reps * 0.2  # Adjusted for lunges

    cap.release()
    return reps, sets, duration, weight, calories_burned, rest_period, stance, form_notes

# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']  # New email field
        password = hash_password(request.form['password'])
        age = request.form['age']
        gender = request.form['gender']

        # Check if the username or email already exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash("Email already exists", "danger")
            return redirect(url_for('signup'))

        # Create a new user
        new_user = User(username=username, email=email, password=password, age=age, gender=gender)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))  # Assuming a 'dashboard' route exists
        else:
            flash("Login failed. Check your credentials.", "danger")
            return redirect(url_for('login'))

        
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clears the session, logging the user out
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))  # Redirects to the login page after logout


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    username = session['username']
    
    # Grouping logs by exercise type
    workout_logs = {
        'pushups': PushUpsLog.query.filter_by(user_id=user_id).all(),
        'squats': SquatsLog.query.filter_by(user_id=user_id).all(),
        'planks': PlanksLog.query.filter_by(user_id=user_id).all(),
        'lunges': LungesLog.query.filter_by(user_id=user_id).all(),
        'pullups': PullUpsLog.query.filter_by(user_id=user_id).all()
    }

    return render_template('dashboard.html', username=username,workout_logs=workout_logs)

@app.route('/start_workout/<exercise>', methods=['GET'])
def start_workout(exercise):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # You can add more logic here, e.g., storing workout start time in the database or logging it
    # Based on the exercise, you can redirect to a video feed or workout page

    if exercise == 'pushups':
        return redirect(url_for('pushups_video'))  # Redirect to Pushups workout page
    elif exercise == 'squats':
        return redirect(url_for('squats_video'))  # Redirect to Squats workout page
    elif exercise == 'planks':
        return redirect(url_for('planks_video'))  # Redirect to Planks workout page
    elif exercise == 'lunges':
        return redirect(url_for('lunges_video'))  # Redirect to Lunges workout page
    elif exercise == 'pullups':
        return redirect(url_for('pullups_video'))  # Redirect to Pullups workout page
    else:
        flash("Invalid exercise", "danger")
        return redirect(url_for('dashboard'))

@app.route('/pushups_video')
def pushups_video():
    # Render a page or return video feed for pushups
    return render_template('pushups_video.html')

@app.route('/squats_video')
def squats_video():
    # Render a page or return video feed for squats
    return render_template('squats_video.html')

@app.route('/planks_video')
def planks_video():
    # Render a page or return video feed for planks
    return render_template('planks_video.html')

@app.route('/lunges_video')
def lunges_video():
    # Render a page or return video feed for lunges
    return render_template('lunges_video.html')

@app.route('/pullups_video')
def pullups_video():
    # Render a page or return video feed for pullups
    return render_template('pullups_video.html')




@app.route('/capture_video/pushups', methods=['POST'])
def capture_video():
    video_file = request.files['video']
    user_notes = request.form.get('notes', '')
    video_path = 'captured_videos/exercise_video.mp4'
    os.makedirs('captured_videos', exist_ok=True)
    video_file.save(video_path)
    
    # Analyze the video for pushups
    reps, sets, duration, difficulty, rest_period, calories_burned, form_notes = analyze_pushups_video(video_path, user_notes)
    
    # Store the results in the database
    new_pushup_log = PushUpsLog(
        user_id=session['user_id'],  # Example user ID
        date=datetime.now(),
        reps=reps,
        sets=sets,
        duration=duration,
        difficulty=difficulty,
        rest_period=rest_period,
        calories_burned=calories_burned,
        form_notes=form_notes
    )
    
    db.session.add(new_pushup_log)
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Video analyzed and data saved successfully!"})

@app.route('/capture_video/squats', methods=['POST'])
def capture_squats_video():
    video_file = request.files['video']
    user_notes = request.form.get('notes', '')
    user_weight = request.form.get('weight', '')
    video_path = 'captured_videos/squats_video.mp4'
    os.makedirs('captured_videos', exist_ok=True)
    video_file.save(video_path)
    
    reps, sets, duration, weight, calories_burned, rest_period, depth, form_notes = analyze_squats_video(video_path, user_notes, user_weight)

    new_squat_log = SquatsLog(
        user_id=session['user_id'],
        date=datetime.now(),
        reps=reps,
        sets=sets,
        duration=duration,
        weight=weight,
        calories_burned=calories_burned,
        rest_period=rest_period,
        depth=depth,
        form_notes=form_notes
    )
    
    db.session.add(new_squat_log)
    db.session.commit()

    return jsonify({"status": "success", "message": "Video analyzed and data saved successfully!"})


@app.route('/capture_video/planks', methods=['POST'])
def capture_planks_video():
    video_file = request.files['video']
    user_notes = request.form.get('notes', '')
    user_weight = request.form.get('weight', '')
    video_path = 'captured_videos/planks_video.mp4'
    os.makedirs('captured_videos', exist_ok=True)
    video_file.save(video_path)

    duration, stage, rest_period, calories_burned, form_notes = analyze_planks_video(video_path, user_notes, user_weight)

    new_plank_log = PlanksLog(
        user_id=session['user_id'],
        date=datetime.now(),
        duration=duration,
        stage=stage,
        rest_period=rest_period,
        calories_burned=calories_burned,
        form_notes=form_notes
    )
    
    db.session.add(new_plank_log)
    db.session.commit()

    return jsonify({"status": "success", "message": "Video analyzed and data saved successfully!"})


@app.route('/capture_video/lunges', methods=['POST'])
def capture_lunges_video():
    video_file = request.files['video']
    user_notes = request.form.get('notes', '')
    user_weight = request.form.get('weight', '')
    video_path = 'captured_videos/lunges_video.mp4'
    os.makedirs('captured_videos', exist_ok=True)
    video_file.save(video_path)

    reps, sets, duration, weight, calories_burned, rest_period, stance, form_notes = analyze_lunges_video(video_path, user_notes, user_weight)

    new_lunges_log = LungesLog(
        user_id=session['user_id'],
        date=datetime.now(),
        reps=reps,
        sets=sets,
        duration=duration,
        weight=weight,
        calories_burned=calories_burned,
        rest_period=rest_period,
        stance=stance,
        form_notes=form_notes
    )

    db.session.add(new_lunges_log)
    db.session.commit()

    return jsonify({"status": "success", "message": "Video analyzed and data saved successfully!"})


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/classes')
def classes():
    return render_template('classes.html')

@app.route('/class-details')
def class_details():
    return render_template('classes-details.html')

@app.route('/trainers')
def trainers():
    return render_template('trainer.html')

@app.route('/trainer-details')
def trainer_details():
    return render_template('trainer-details.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/event-details')
def event_details():
    return render_template('event-details.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/single-blog')
def single_blog():
    return render_template('single-blog.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
