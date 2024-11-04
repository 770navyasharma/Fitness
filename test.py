import pytest
from app import app, db, User, WorkoutLog
import hashlib  
from flask import session
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# Test setup and teardown for the database
@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()

    # Set up a temporary test database
    with app.app_context():
        db.create_all()
        yield client  # this is where the testing happens

        # Drop all tables after tests to reset state
        db.drop_all()

# Utility function to hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Test cases for Signup functionality
def test_signup_success(client):
    response = client.post('/signup', data={
        'username': 'testuser',
        'password': 'testpassword',
        'age': 25,
        'gender': 'male'
    }, follow_redirects=True)

    # Check if the signup was successful
    assert b"Signup successful! Please log in." in response.data
    assert User.query.filter_by(username='testuser').first() is not None

def test_signup_existing_user(client):
    # Create a user
    user = User(username='existinguser', password=hash_password('password'), age=25, gender='female')
    db.session.add(user)
    db.session.commit()

    # Attempt to sign up with the same username
    response = client.post('/signup', data={
        'username': 'existinguser',
        'password': 'newpassword',
        'age': 30,
        'gender': 'female'
    }, follow_redirects=True)

    # Check if the appropriate message is displayed
    assert b"Username already exists" in response.data


def test_login_invalid_credentials(client):
    # Attempt to log in with wrong credentials
    response = client.post('/login', data={
        'username': 'wronguser',
        'password': 'wrongpassword'
    }, follow_redirects=True)

    # Check if the appropriate error message is shown
    assert b"Invalid credentials" in response.data

# Test case for Logout functionality
def test_logout(client):
    # Create a test user session
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'testuser'

    # Logout the user
    response = client.get('/logout', follow_redirects=True)

    # Ensure the user is logged out
    assert b"You have been logged out." in response.data
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

# Test case for adding a workout log
def test_add_workout_log(client):
    # Create a test user
    user = User(username='workoutuser', password=hash_password('password'), age=25, gender='male')
    db.session.add(user)
    db.session.commit()

    # Log in the user
    client.post('/login', data={'username': 'workoutuser', 'password': 'password'}, follow_redirects=True)

    # Simulate workout session and add log
    with client.session_transaction() as sess:
        sess['user_id'] = user.id

    response = client.post('/end_workout', data={}, follow_redirects=True)

    # Check if the workout log has been added
    workout_log = WorkoutLog.query.filter_by(user_id=user.id).first()
    assert workout_log is not None
    assert b"Workout session ended. Data has been logged." in response.data

# Test case to check dashboard display for logged-in user
def test_dashboard(client):
    # Create a test user and log them in
    user = User(username='dashboarduser', password=hash_password('password'), age=25, gender='male')
    db.session.add(user)
    db.session.commit()

    # Log in the user and check dashboard
    client.post('/login', data={'username': 'dashboarduser', 'password': 'password'}, follow_redirects=True)

    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b"Your Workout Logs" in response.data


# Test case for workout session start and end
def test_workout_start_end(client):
    # Create a test user and log them in
    user = User(username='workoutuser2', password=hash_password('password'), age=25, gender='male')
    db.session.add(user)
    db.session.commit()

    client.post('/login', data={'username': 'workoutuser2', 'password': 'password'}, follow_redirects=True)

    # Start workout session
    client.get('/workout')
    assert client.get('/video_feed').status_code == 200  # Confirm the video feed starts

    # End workout session
    response = client.post('/end_workout', follow_redirects=True)
    assert b"Workout session ended. Data has been logged." in response.data
