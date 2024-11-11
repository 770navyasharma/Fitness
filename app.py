from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
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

# Curl counter variables
counter_up = 0
counter_down = 0
stage = None
workout_active = False
start_time = None
threshold_time = 3  # delay time in seconds before reps are counted

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))

class WorkoutLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    up_reps = db.Column(db.Integer, nullable=False)
    down_reps = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    stages = db.Column(db.String(100), nullable=False)

    def __init__(self, user_id, date, up_reps, down_reps, duration, stages):
        self.user_id = user_id
        self.date = date
        self.up_reps = up_reps
        self.down_reps = down_reps
        self.duration = duration
        self.stages = stages

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
        password = hash_password(request.form['password'])
        age = request.form['age']
        gender = request.form['gender']

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('signup'))

        new_user = User(username=username, password=password, age=age, gender=gender)
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
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    workout_logs = WorkoutLog.query.filter_by(user_id=user_id).all()
    
    return render_template('dashboard.html', workout_logs=workout_logs)

# Calculate angle between three points
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle

@app.route('/workout', methods=['GET', 'POST'])
def workout():
    global workout_active, start_time, counter_up, counter_down
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    workout_active = True
    start_time = time.time()  # Start time of workout
    counter_up = 0  # Reset counters
    counter_down = 0
    return render_template('workout.html')

# Workout tracking logic with camera feed
def workout_tracking():
    global counter_up, counter_down, stage, workout_active, start_time
    cap = cv2.VideoCapture(0)

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened() and workout_active:
            ret, frame = cap.read()
            if not ret:
                break

            current_time = time.time()
            if current_time - start_time < threshold_time:
                # Skip the first few seconds
                continue

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                angle = calculate_angle(shoulder, elbow, wrist)

                if angle > 160:
                    if stage == "up":
                        counter_down += 1
                    stage = "down"
                if angle < 30 and stage == 'down':
                    counter_up += 1
                    stage = "up"

            except Exception as e:
                print(f"Error processing landmarks: {e}")
                pass

            cv2.rectangle(image, (0, 0), (225, 73), (245, 117, 16), -1)
            cv2.putText(image, 'UP REPS', (15, 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter_up),
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(image, 'DOWN REPS', (85, 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter_down),
                        (80, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(workout_tracking(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/end_workout', methods=['POST'])
def end_workout():
    global workout_active, counter_up, counter_down, stage
    workout_active = False
    duration = time.time() - start_time  # Calculate duration

    if 'user_id' in session:
        user_id = session['user_id']
        workout_log = WorkoutLog(
            user_id=user_id,
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            up_reps=counter_up,
            down_reps=counter_down,
            duration=duration,
            stages=stage or "N/A"
        )
        db.session.add(workout_log)
        db.session.commit()

        counter_up = 0
        counter_down = 0
        stage = None

        flash("Workout session ended. Data has been logged.", "success")
    else:
        flash("You must be logged in to log workout data.", "danger")

    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
