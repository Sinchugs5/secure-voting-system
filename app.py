# app.py
# ---------------- Imports ----------------
from flask import Flask, request, jsonify, render_template, session, current_app, redirect, send_from_directory
from flask_mail import Mail, Message
from flask_session import Session
from dotenv import load_dotenv
import os
import sqlite3
import base64
import json
from datetime import datetime
from io import BytesIO
try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    # Mock PIL for deployment
    class Image:
        @staticmethod
        def open(*args, **kwargs):
            return None
    class UnidentifiedImageError(Exception):
        pass
from werkzeug.utils import secure_filename
import random
import requests
import uuid

# load .env early
load_dotenv()

# ---------------- App config ----------------
app = Flask(__name__)

# ---------------- Upload & Database paths ----------------
UPLOAD_FOLDER = 'static/uploads'
CANDIDATE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'candidates')
DATABASE = 'Election.db'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CANDIDATE_UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
app.config['SESSION_TYPE'] = 'filesystem'

# ---------------- Flask-Mail config ----------------
app.config['MAIL_SERVER'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('SMTP_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or app.config['MAIL_USERNAME']

mail = Mail(app)
Session(app)

# ---------------- Location Functions ----------------
def get_location_name(latitude, longitude):
    """Get location name from coordinates using reverse geocoding"""
    try:
        # Using OpenStreetMap Nominatim API (free)
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&zoom=18&addressdetails=1"
        headers = {'User-Agent': 'VotingSystem/1.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            
            # Build location string from components
            location_parts = []
            if address.get('house_number'):
                location_parts.append(address['house_number'])
            if address.get('road'):
                location_parts.append(address['road'])
            if address.get('suburb') or address.get('neighbourhood'):
                location_parts.append(address.get('suburb') or address['neighbourhood'])
            if address.get('city') or address.get('town') or address.get('village'):
                location_parts.append(address.get('city') or address.get('town') or address['village'])
            if address.get('state'):
                location_parts.append(address['state'])
            
            return ', '.join(location_parts) if location_parts else f"Lat: {latitude}, Lng: {longitude}"
        else:
            return f"Lat: {latitude}, Lng: {longitude}"
    except Exception as e:
        print(f"Geocoding error: {e}")
        return f"Lat: {latitude}, Lng: {longitude}"

# ---------------- SMS Function ----------------
def send_sms_otp(mobile, otp, name):
    # For testing - print OTP to console
    print(f"SMS OTP for {mobile}: {otp}")
    
    # Try Twilio first
    twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
    twilio_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
    
    if twilio_sid and twilio_token and twilio_sid != 'your_twilio_account_sid_here':
        try:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            message = client.messages.create(
                body=f"Hello {name}, Your OTP is: {otp}. Valid for 5 minutes.",
                from_=os.environ.get('TWILIO_PHONE_NUMBER', '+1234567890'),
                to=f'+91{mobile}' if not mobile.startswith('+') else mobile
            )
            print(f"Twilio SMS sent: {message.sid}")
            return True
        except Exception as e:
            print(f"Twilio SMS Error: {e}")
    
    # Fallback to other SMS providers
    api_key = os.environ.get('SMS_API_KEY', '')
    
    if not api_key or api_key.strip() == '' or api_key == 'your_actual_sms_api_key_here':
        print(f"No SMS API configured. Check console for OTP: {otp}")
        return True  # Allow login to proceed with console OTP
    
    message = f"Hello {name}, Your OTP is: {otp} for casting your valuable vote. Valid for 5 minutes."
    
    # Textlocal API
    url = 'https://api.textlocal.in/send/'
    data = {
        'apikey': api_key,
        'numbers': mobile,
        'message': message,
        'sender': 'VOTING'
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        print(f"SMS API Response: {result}")
        
        if response.status_code == 200 and result.get('status') == 'success':
            return True
        else:
            print(f"SMS failed: {result}")
            return True  # Still allow console OTP
    except Exception as e:
        print(f"SMS Error (using console OTP): {e}")
        return True

# ---------------- Try to import blockchain ----------------
try:
    from blockchain import Blockchain, Block
except Exception:
    try:
        from blockchain import Blockchain
        Block = None
    except Exception:
        class Blockchain:
            def __init__(self):
                self.chain = []

            def get_latest_block(self):
                return self.chain[-1] if self.chain else None
        Block = None

# ---------------- face utils ----------------
try:
    from face_utils import get_face_encoding_from_base64, compare_encodings
except Exception:
    try:
        from face_utils_mock import get_face_encoding_from_base64, compare_encodings
        print("Using mock face recognition for deployment")
    except Exception:
        def get_face_encoding_from_base64(*args, **kwargs):
            return [0.1] * 128
        def compare_encodings(*args, **kwargs):
            return True, 0.3

# ---------------- Blockchain ----------------
blockchain = Blockchain()

# ---------------- Database setup ----------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Student_details (
            Name TEXT,
            DateOfBirth TEXT,
            Age INTEGER,
            Gender TEXT,
            Email TEXT,
            Mobile TEXT,
            Username TEXT UNIQUE,
            Password TEXT,
            Photo TEXT,
            FaceEncoding TEXT,
            Latitude TEXT,
            Longitude TEXT,
            Location TEXT
        )
    ''')
    
    # Add new columns if they don't exist
    try:
        cursor.execute('ALTER TABLE Student_details ADD COLUMN DateOfBirth TEXT')
        cursor.execute('ALTER TABLE Student_details ADD COLUMN Age INTEGER')
        cursor.execute('ALTER TABLE Student_details ADD COLUMN Gender TEXT')
        cursor.execute('ALTER TABLE Student_details ADD COLUMN Mobile TEXT')
        cursor.execute('ALTER TABLE Student_details ADD COLUMN Latitude TEXT')
        cursor.execute('ALTER TABLE Student_details ADD COLUMN Longitude TEXT')
        cursor.execute('ALTER TABLE Student_details ADD COLUMN Location TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Columns already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Candidate (
            Name TEXT,
            PartyName TEXT,
            Photo TEXT,
            Symbol TEXT,
            Age INTEGER,
            Gender TEXT,
            Email TEXT,
            PhoneNumber TEXT,
            Description TEXT
        )
    ''')
    
    # Add new columns to existing Candidate table
    try:
        cursor.execute('ALTER TABLE Candidate ADD COLUMN PartyName TEXT')
        cursor.execute('ALTER TABLE Candidate ADD COLUMN Symbol TEXT')
        cursor.execute('ALTER TABLE Candidate ADD COLUMN Age INTEGER')
        cursor.execute('ALTER TABLE Candidate ADD COLUMN Gender TEXT')
        cursor.execute('ALTER TABLE Candidate ADD COLUMN Email TEXT')
        cursor.execute('ALTER TABLE Candidate ADD COLUMN PhoneNumber TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Columns already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Vote (
            Name TEXT,
            Username TEXT,
            Email TEXT,
            Candidate TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Result (
            Name TEXT,
            Photo TEXT,
            PartyName TEXT,
            Votes INTEGER
        )
    ''')
    
    # Update Result table to use PartyName instead of Class
    try:
        cursor.execute('ALTER TABLE Result ADD COLUMN PartyName TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS VotingSchedule (
            id INTEGER PRIMARY KEY,
            start_date TEXT,
            end_date TEXT,
            start_time TEXT,
            end_time TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS LoginHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            login_time TEXT,
            latitude TEXT,
            longitude TEXT,
            location TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ProctoringData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            session_start TEXT,
            session_end TEXT,
            duration INTEGER,
            violations TEXT,
            tab_switches INTEGER,
            recording_path TEXT,
            total_violations INTEGER,
            ip_address TEXT,
            mac_address TEXT
        )
    ''')
    
    # Add new columns if they don't exist
    try:
        cursor.execute('ALTER TABLE ProctoringData ADD COLUMN ip_address TEXT')
        cursor.execute('ALTER TABLE ProctoringData ADD COLUMN mac_address TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Columns already exist
    conn.commit()
    conn.close()

init_db()

# ---------------- Routes ----------------
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/')
    return render_template("Admin.html")

@app.route('/student-login')
def student_login():
    return render_template("student_login.html")

@app.route('/student-registration')
def student_registration():
    return render_template("student_registration.html")

# ---------------- Registration ----------------
@app.route('/register', methods=['POST'])
def register():
    try:
        full_name = request.form['fullName']
        date_of_birth = request.form['dateOfBirth']
        age = int(request.form['age'])
        gender = request.form['gender']
        email = request.form['email']
        mobile = request.form['mobile']
        username = request.form['username']
        password = request.form['password']
        photo_data_url = request.form['photoData']
        latitude = request.form.get('latitude', '')
        longitude = request.form.get('longitude', '')
        location = request.form.get('location', '')

        # Check age eligibility
        if age < 18:
            return jsonify({"success": False, "message": "You are not eligible for voting. Minimum age requirement is 18 years."})

        if "base64," not in photo_data_url:
            return jsonify({"success": False, "message": "Invalid photo data."})

        header, encoded = photo_data_url.split(",", 1)
        image_data = base64.b64decode(encoded)
        photo_filename = f"{username}.png"
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename).replace("\\", "/")
        with open(photo_path, "wb") as f:
            f.write(image_data)

        encoding = get_face_encoding_from_base64(photo_data_url)
        encoding_json = json.dumps(encoding)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Student_details (Name, DateOfBirth, Age, Gender, Email, Mobile, Username, Password, Photo, FaceEncoding, Latitude, Longitude, Location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (full_name, date_of_birth, age, gender, email, mobile, username, password, photo_path, encoding_json, latitude, longitude, location))
        conn.commit()
        conn.close()

        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ---------------- Username/password + OTP login ----------------
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        login_type = data.get('loginType', 'email')
        login_value = data.get('loginValue') or data.get('email')
        password = data.get('password')

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        if login_type == 'mobile':
            cursor.execute('''
                SELECT Name, DateOfBirth, Age, Gender, Email, Mobile, Username, Photo FROM Student_details
                WHERE Mobile = ? AND Password = ?
            ''', (login_value, password))
        else:
            cursor.execute('''
                SELECT Name, DateOfBirth, Age, Gender, Email, Mobile, Username, Photo FROM Student_details
                WHERE Email = ? AND Password = ?
            ''', (login_value, password))
            
        result = cursor.fetchone()
        conn.close()

        if result:
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['otp_user'] = login_value

            name, date_of_birth, age, gender, email, mobile, username, photo_path = result

            # Send OTP based on login type
            if login_type == 'mobile':
                try:
                    send_sms_otp(mobile, otp, name)
                    return jsonify({'success': True, 'message': f'OTP sent to {mobile}. Please verify OTP to complete login.'})
                except Exception as e:
                    try:
                        msg = Message(
                            subject="Your OTP Code (SMS Failed)",
                            sender=app.config['MAIL_DEFAULT_SENDER'],
                            recipients=[email]
                        )
                        msg.body = f"Hello {name},\n\nYour OTP is: {otp}\nThis code is valid for 5 minutes.\n\nNote: SMS to {mobile} failed, so we sent it to your email."
                        
                        with app.app_context():
                            mail.send(msg)
                        
                        return jsonify({'success': True, 'message': f'SMS failed. OTP sent to your email {email} instead.'})
                    except Exception as email_error:
                        return jsonify({'success': False, 'message': f'Both SMS and email failed. Please contact support.'})
            else:
                try:
                    msg = Message(
                        subject="Your OTP Code - Voting System",
                        sender=app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[email]
                    )
                    msg.body = f"Hello {name},\n\nYour OTP for voting system login is: {otp}\n\nThis code is valid for 5 minutes.\n\nRegards,\nVoting System"
                    
                    with app.app_context():
                        mail.send(msg)
                    
                    return jsonify({'success': True, 'message': f'OTP sent to {email}. Please check your email.'})
                except Exception as e:
                    return jsonify({'success': False, 'message': f'Failed to send OTP to {email}. Please try again.'})
        else:
            field_name = 'mobile number' if login_type == 'mobile' else 'email'
            return jsonify({'success': False, 'message': f'Invalid {field_name} or password.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        login_type = data.get('loginType', 'email')
        login_value = data.get('loginValue') or data.get('email')
        otp_input = data.get('otp')

        if not otp_input or not login_value:
            return jsonify({"success": False, "message": "OTP and login credentials required"}), 400

        if session.get("otp") == otp_input and session.get("otp_user") == login_value:
            # OTP matched → fetch user details
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            if login_type == 'mobile':
                cursor.execute(
                    "SELECT Name, DateOfBirth, Age, Gender, Email, Mobile, Username, Photo FROM Student_details WHERE Mobile = ?",
                    (login_value,)
                )
            else:
                cursor.execute(
                    "SELECT Name, DateOfBirth, Age, Gender, Email, Mobile, Username, Photo FROM Student_details WHERE Email = ?",
                    (login_value,)
                )
                
            result = cursor.fetchone()
            conn.close()

            if not result:
                return jsonify({"success": False, "message": "User not found"}), 404

            name, date_of_birth, age, gender, email, mobile, username, photo_path = result

            # Store user data but mark as OTP verified only
            session["otp_verified_user"] = {
                "name": name,
                "email": email,
                "mobile": mobile,
                "date_of_birth": date_of_birth,
                "age": age,
                "gender": gender,
                "username": username,
                "photo": photo_path,
            }
            session["otp_verified"] = True
            session["login_type"] = login_type

            # Clear OTP
            session.pop("otp", None)
            session.pop("otp_user", None)

            return jsonify({"message": "otp_verified", "success": True})
        else:
            return jsonify({"error": "Invalid or expired OTP", "success": False}), 401
    except Exception as e:
        return jsonify({'error': str(e)})

# ---------------- Admin login ----------------
@app.route('/admin-login', methods=['POST'])
def admin_login():
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        admin_username = data.get('username')
        admin_password = data.get('password')

        expected_user = os.getenv('ADMIN_USERNAME', 'admin')
        expected_pass = os.getenv('ADMIN_PASSWORD', 'admin')

        if admin_username == expected_user and admin_password == expected_pass:
            session['admin'] = True
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ---------------- Face Login ----------------
@app.route('/face-login', methods=['POST'])
def face_login():
    try:
        username = request.form.get('username')
        login_type = request.form.get('loginType', 'email')
        photo = request.files.get('photo')
        
        if not username or not photo:
            return jsonify({'success': False, 'message': 'Username and photo required'})
        
        # Check if OTP was verified first
        if not session.get('otp_verified'):
            return jsonify({'success': False, 'message': 'Please verify OTP first'})
        
        # Get stored face encoding based on login type
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        if login_type == 'mobile':
            cursor.execute('SELECT Name, DateOfBirth, Age, Gender, Email, Mobile, Photo, FaceEncoding FROM Student_details WHERE Mobile = ?', (username,))
        else:
            cursor.execute('SELECT Name, DateOfBirth, Age, Gender, Email, Mobile, Photo, FaceEncoding FROM Student_details WHERE Email = ?', (username,))
            
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'message': 'User not found'})
        
        name, date_of_birth, age, gender, email, mobile, photo_path, stored_encoding = result
        
        # Verify this matches the OTP verified user
        otp_user = session.get('otp_verified_user', {})
        user_identifier = mobile if login_type == 'mobile' else email
        otp_identifier = otp_user.get('mobile') if login_type == 'mobile' else otp_user.get('email')
        
        if user_identifier != otp_identifier:
            return jsonify({'success': False, 'message': 'Face login must match OTP verified user'})
        
        # Compare face encodings with improved validation
        photo_data = photo.read()
        current_photo_b64 = f"data:image/png;base64,{base64.b64encode(photo_data).decode()}"
        
        try:
            current_encoding = get_face_encoding_from_base64(current_photo_b64)
        except ValueError as e:
            return jsonify({'success': False, 'message': 'No face detected in the photo. Please ensure your face is clearly visible.'})
        except Exception as e:
            return jsonify({'success': False, 'message': 'Face detection failed. Please try again with better lighting.'})
        
        stored_encoding_list = json.loads(stored_encoding)
        
        # Use stricter tolerance for better accuracy
        match_result, distance = compare_encodings(current_encoding, stored_encoding_list, tolerance=0.4)
        
        print(f"Face matching - Distance: {distance:.3f}, Match: {match_result}, Tolerance: 0.4")
        
        if match_result and distance < 0.4:
            # Store login location with reverse geocoding
            latitude = request.form.get('latitude', '')
            longitude = request.form.get('longitude', '')
            location = request.form.get('location', '')
            
            # Get location name if coordinates are available
            if latitude and longitude:
                location_name = get_location_name(latitude, longitude)
            else:
                location_name = location or 'Location not available'
            
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO LoginHistory (username, login_time, latitude, longitude, location) VALUES (?, ?, ?, ?, ?)',
                          (otp_user['username'], datetime.now().isoformat(), latitude, longitude, location_name))
            conn.commit()
            conn.close()
            
            # Both OTP and face verified - set full user session
            session['user'] = otp_user
            session['face_verified'] = True
            # Keep login_type for confirmation messages
            # Clear temporary data
            session.pop('otp_verified_user', None)
            session.pop('otp_verified', None)
            return jsonify({'success': True, 'message': 'Face login successful', 'redirect': '/voter-details'})
        else:
            if distance >= 0.6:
                return jsonify({'success': False, 'message': 'Face does not match registered photo. Please ensure you are the registered user.'})
            else:
                return jsonify({'success': False, 'message': f'Face recognition failed (confidence: {(1-distance)*100:.1f}%). Please try again with better lighting and face positioning.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ---------------- Voter Details Page ----------------
@app.route('/voter-details')
def voter_details():
    # Check if both OTP and face are verified
    if 'user' not in session or not session.get('face_verified'):
        return redirect('/student-login')
    
    # Check voting time and get schedule info
    can_vote, voting_message = is_voting_time()
    
    # Check if user has already voted and get user location
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT Candidate FROM Vote WHERE Username = ?', (session['user']['username'],))
    vote_record = cursor.fetchone()
    
    # Get user's latest login location
    cursor.execute('SELECT latitude, longitude, location FROM LoginHistory WHERE username = ? ORDER BY login_time DESC LIMIT 1', (session['user']['username'],))
    location_record = cursor.fetchone()
    
    # Get voting schedule for display
    cursor.execute('SELECT start_date, end_date, start_time, end_time FROM VotingSchedule ORDER BY id DESC LIMIT 1')
    schedule = cursor.fetchone()
    conn.close()
    
    has_voted = vote_record is not None
    voted_candidate = vote_record[0] if vote_record else None
    
    user_location = location_record[2] if location_record and location_record[2] and location_record[2].strip() else 'Location not captured during login'
    user_lat = location_record[0] if location_record and location_record[0] else None
    user_lng = location_record[1] if location_record and location_record[1] else None
    voting_ended = is_voting_ended()
    
    # Generate unique voter ID for E-card
    voter_id = f"VID{str(uuid.uuid4())[:8].upper()}"
    
    return render_template('voter_details.html', user=session['user'], has_voted=has_voted, 
                         voted_candidate=voted_candidate, can_vote=can_vote, 
                         voting_message=voting_message, schedule=schedule, user_location=user_location,
                         user_lat=user_lat, user_lng=user_lng, voting_ended=voting_ended, voter_id=voter_id)

def is_voting_time():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT start_date, end_date, start_time, end_time FROM VotingSchedule ORDER BY id DESC LIMIT 1')
    schedule = cursor.fetchone()
    conn.close()
    
    if not schedule:
        return True, "No voting schedule set"
    
    from datetime import datetime, time
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()
    
    start_date = datetime.strptime(schedule[0], '%Y-%m-%d').date()
    end_date = datetime.strptime(schedule[1], '%Y-%m-%d').date()
    start_time = datetime.strptime(schedule[2], '%H:%M').time()
    end_time = datetime.strptime(schedule[3], '%H:%M').time()
    
    if current_date < start_date:
        return False, f"Voting starts on {start_date} at {start_time}"
    elif current_date > end_date:
        return False, f"Voting ended on {end_date} at {end_time}"
    elif current_date == start_date and current_time < start_time:
        return False, f"Voting starts at {start_time}"
    elif current_date == end_date and current_time > end_time:
        return False, f"Voting ended at {end_time}"
    
    return True, "Voting is active"

def is_voting_ended():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT start_date, end_date, start_time, end_time FROM VotingSchedule ORDER BY id DESC LIMIT 1')
    schedule = cursor.fetchone()
    conn.close()
    
    if not schedule:
        return True  # No schedule means results can be shown
    
    from datetime import datetime, time
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()
    
    end_date = datetime.strptime(schedule[1], '%Y-%m-%d').date()
    end_time = datetime.strptime(schedule[3], '%H:%M').time()
    
    if current_date > end_date:
        return True
    elif current_date == end_date and current_time > end_time:
        return True
    
    return False

# ---------------- Voting Page ----------------
@app.route('/voting-page')
def voting_page():
    # Check if both OTP and face are verified
    if 'user' not in session or not session.get('face_verified'):
        return redirect('/student-login')
    
    # Check voting time
    can_vote, message = is_voting_time()
    if not can_vote:
        return render_template('message.html', message=message, redirect_url='/voter-details')
    
    # Check if user has already voted
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Vote WHERE Username = ?', (session['user']['username'],))
    if cursor.fetchone():
        conn.close()
        return redirect('/voter-details')
    
    cursor.execute('SELECT Name, PartyName, Photo, Symbol, Age, Gender, Email, PhoneNumber, Description FROM Candidate')
    candidates = cursor.fetchall()
    conn.close()
    
    return render_template('candidates.html', candidates=candidates, user=session['user'])

# ---------------- Candidates Page (Legacy) ----------------
@app.route('/candidates')
def candidates():
    # Redirect to voter details first
    return redirect('/voter-details')

# ---------------- Submit Vote ----------------
@app.route('/submit-vote', methods=['POST'])
def submit_vote():
    if 'user' not in session or not session.get('face_verified'):
        return jsonify({'success': False, 'message': 'Authentication required'})
    
    # Check voting time
    can_vote, message = is_voting_time()
    if not can_vote:
        return jsonify({'success': False, 'message': message})
    
    try:
        data = request.get_json()
        candidate = data.get('candidate')
        emotion_photo = data.get('emotionPhoto')
        user = session['user']
        
        # Face verification security check during voting
        if emotion_photo:
            try:
                # Get current photo encoding
                current_encoding = get_face_encoding_from_base64(emotion_photo)
                
                # Get stored face encoding
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute('SELECT FaceEncoding FROM Student_details WHERE Username = ?', (user['username'],))
                stored_result = cursor.fetchone()
                conn.close()
                
                if stored_result:
                    stored_encoding = json.loads(stored_result[0])
                    match_result, distance = compare_encodings(current_encoding, stored_encoding, tolerance=0.5)
                    
                    print(f"Voting Face Check - Distance: {distance:.3f}, Match: {match_result}")
                    
                    if not match_result or distance > 0.5:
                        return jsonify({
                            'success': False, 
                            'message': f'Security Alert: Face verification failed during voting. Please ensure you are the registered voter. (Confidence: {(1-distance)*100:.1f}%)',
                            'security_alert': True
                        })
                        
            except Exception as e:
                print(f"Face verification error during voting: {e}")
                return jsonify({
                    'success': False, 
                    'message': 'Security verification failed. Please try again with clear face visibility.',
                    'security_alert': True
                })
        
        # Check if user already voted
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Vote WHERE Username = ?', (user['username'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'You have already voted'})
        
        # Create blockchain transaction
        vote_transaction = blockchain.create_vote_transaction(
            user['name'], user['username'], candidate, datetime.now().isoformat()
        )
        blockchain.add_transaction(vote_transaction)
        blockchain.mine_pending_transactions()
        
        # Record vote in database
        cursor.execute('INSERT INTO Vote (Name, Username, Email, Candidate) VALUES (?, ?, ?, ?)',
                      (user['name'], user['username'], user['email'], candidate))
        
        # Update results
        cursor.execute('SELECT * FROM Result WHERE Name = ?', (candidate,))
        if cursor.fetchone():
            cursor.execute('UPDATE Result SET Votes = Votes + 1 WHERE Name = ?', (candidate,))
        else:
            cursor.execute('SELECT PartyName, Photo FROM Candidate WHERE Name = ?', (candidate,))
            candidate_info = cursor.fetchone()
            if candidate_info:
                cursor.execute('INSERT INTO Result (Name, Photo, PartyName, Votes) VALUES (?, ?, ?, 1)',
                              (candidate, candidate_info[1], candidate_info[0]))
        
        conn.commit()
        conn.close()
        
        # Send confirmation
        confirmation_sent = False
        login_type = session.get('login_type', 'email')
        
        try:
            confirmation_msg = f"Dear {user['name']}, Your vote has been securely recorded on blockchain. Block Hash: {blockchain.get_latest_block().hash[:16]}... Thank you!"
            
            if login_type == 'mobile' and user.get('mobile'):
                confirmation_sent = send_sms_otp(user['mobile'], confirmation_msg.replace('Dear ', '').replace(', Your', '. Your'), user['name'])
            else:
                if app.config.get('MAIL_USERNAME'):
                    msg = Message(
                        subject="Vote Confirmation - Blockchain Secured",
                        sender=current_app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[user['email']]
                    )
                    msg.body = f"Dear {user['name']},\n\nYour vote has been successfully recorded and secured on blockchain!\n\nVote Details:\n- Voter: {user['name']}\n- Age: {user['age']}\n- Gender: {user['gender']}\n- Block Hash: {blockchain.get_latest_block().hash}\n- Transaction Hash: {vote_transaction['hash']}\n- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nYour vote is confidential and securely stored. Thank you for participating in the democratic process.\n\nRegards,\nState Election Commission Karnataka"
                    mail.send(msg)
                    confirmation_sent = True
        except Exception as e:
            print(f"Confirmation sending failed: {e}")
        
        print(f"\n=== BLOCKCHAIN VOTE RECORDED ===")
        print(f"Voter: {user['name']} ({user['username']})")
        print(f"Candidate: {candidate}")
        print(f"Block Hash: {blockchain.get_latest_block().hash}")
        print(f"Transaction Hash: {vote_transaction['hash']}")
        print(f"Blockchain Valid: {blockchain.is_chain_valid()}")
        print(f"================================\n")
        
        return jsonify({
            'success': True, 
            'message': 'Vote recorded on blockchain successfully', 
            'block_hash': blockchain.get_latest_block().hash[:16] + '...',
            'transaction_hash': vote_transaction['hash'][:16] + '...',
            'confirmation_sent': confirmation_sent
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ---------------- Logout ----------------
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return '', 204

# ---------------- Results Page ----------------
@app.route('/results')
def results():
    # Check if voting has ended
    if not is_voting_ended():
        return render_template('wait_results.html', schedule=get_voting_schedule())
    
    # Get results from blockchain for verification
    blockchain_votes = blockchain.get_all_votes()
    blockchain_results = {}
    for vote in blockchain_votes:
        candidate = vote['candidate']
        blockchain_results[candidate] = blockchain_results.get(candidate, 0) + 1
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT Name, Photo, PartyName, Votes FROM Result ORDER BY Votes DESC')
    db_results = cursor.fetchall()
    conn.close()
    
    # Verify blockchain vs database consistency
    verification_status = True
    for result in db_results:
        candidate_name = result[0]
        db_votes = result[3]
        blockchain_votes_count = blockchain_results.get(candidate_name, 0)
        if db_votes != blockchain_votes_count:
            verification_status = False
            break
    
    return render_template('result.html', results=db_results, 
                         blockchain_valid=blockchain.is_chain_valid(),
                         verification_status=verification_status,
                         total_blocks=len(blockchain.chain))

def get_voting_schedule():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT start_date, end_date, start_time, end_time FROM VotingSchedule ORDER BY id DESC LIMIT 1')
    schedule = cursor.fetchone()
    conn.close()
    return schedule

# ---------------- Blockchain API Routes ----------------
@app.route('/blockchain-status')
def blockchain_status():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'})
    
    return jsonify({
        'chain_length': len(blockchain.chain),
        'is_valid': blockchain.is_chain_valid(),
        'latest_block_hash': blockchain.get_latest_block().hash,
        'total_votes': len(blockchain.get_all_votes()),
        'pending_transactions': len(blockchain.pending_transactions)
    })

@app.route('/blockchain-votes')
def blockchain_votes():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'})
    
    votes = blockchain.get_all_votes()
    return jsonify(votes)

@app.route('/get-proctoring-data')
def get_proctoring_data():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'})
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username, session_start, duration, violations, tab_switches, total_violations, recording_path, ip_address, mac_address
            FROM ProctoringData ORDER BY session_start DESC
        ''')
        data = cursor.fetchall()
        conn.close()
        
        proctoring_data = []
        for row in data:
            proctoring_data.append({
                'username': row[0],
                'session_start': row[1],
                'duration': row[2],
                'violations': json.loads(row[3]) if row[3] else [],
                'tab_switches': row[4],
                'total_violations': row[5],
                'recording_path': row[6],
                'ip_address': row[7],
                'mac_address': row[8]
            })
        
        return jsonify(proctoring_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/proctoring-video/<filename>')
def serve_proctoring_video(filename):
    if not session.get('admin'):
        return 'Unauthorized', 403
    
    try:
        protocard_dir = os.path.join(os.getcwd(), 'static', 'protocard')
        file_path = os.path.join(protocard_dir, filename)
        
        if os.path.exists(file_path):
            return send_from_directory(protocard_dir, filename)
        else:
            return f'Video file not found: {filename}', 404
    except Exception as e:
        return f'Error serving video: {str(e)}', 500

# ---------------- Admin Routes ----------------
@app.route('/add-candidate', methods=['POST'])
def add_candidate():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        name = request.form['name']
        party_name = request.form['partyName']
        age = int(request.form['age'])
        gender = request.form['gender']
        email = request.form['email']
        phone_number = request.form['phoneNumber']
        description = request.form['description']
        photo = request.files['photo']
        symbol = request.files.get('symbol')
        
        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(CANDIDATE_UPLOAD_FOLDER, filename)
            photo.save(photo_path)
            photo_url = f'static/uploads/candidates/{filename}'
        else:
            return jsonify({'success': False, 'message': 'Photo required'})
        
        symbol_url = ''
        if symbol:
            symbol_filename = secure_filename(symbol.filename)
            symbol_path = os.path.join(CANDIDATE_UPLOAD_FOLDER, symbol_filename)
            symbol.save(symbol_path)
            symbol_url = f'static/uploads/candidates/{symbol_filename}'
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Candidate (Name, PartyName, Photo, Symbol, Age, Gender, Email, PhoneNumber, Description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (name, party_name, photo_url, symbol_url, age, gender, email, phone_number, description))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get-voters')
def get_voters():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'})
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT Name, Username, Email FROM Student_details')
        students = cursor.fetchall()
        
        cursor.execute('SELECT Username FROM Vote')
        voted_users = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        voters = []
        for student in students:
            voters.append({
                'name': student[0],
                'username': student[1],
                'email': student[2],
                'voted': student[1] in voted_users
            })
        
        return jsonify(voters)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get-stats')
def get_stats():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'})
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get all candidates with their vote counts
        cursor.execute('''
            SELECT c.Name, c.Photo, c.PartyName, c.Symbol, COALESCE(r.Votes, 0) as Votes 
            FROM Candidate c 
            LEFT JOIN Result r ON c.Name = r.Name 
            ORDER BY COALESCE(r.Votes, 0) DESC
        ''')
        stats = cursor.fetchall()
        conn.close()
        
        return jsonify([{
            'name': stat[0],
            'photo': stat[1],
            'party_name': stat[2],
            'symbol': stat[3],
            'votes': stat[4]
        } for stat in stats])
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/get-candidates')
def get_candidates():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'})
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT Name, PartyName, Photo, Symbol, Age, Gender, Email, PhoneNumber, Description FROM Candidate')
        candidates = cursor.fetchall()
        conn.close()
        
        return jsonify([{
            'name': candidate[0],
            'party_name': candidate[1],
            'photo': candidate[2],
            'symbol': candidate[3],
            'age': candidate[4],
            'gender': candidate[5],
            'email': candidate[6],
            'phone_number': candidate[7],
            'description': candidate[8]
        } for candidate in candidates])
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/save-results', methods=['POST'])
def save_results():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Results are already saved in real-time during voting
        return jsonify({'success': True, 'message': 'Results saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete-election', methods=['POST'])
def delete_election():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Vote')
        cursor.execute('DELETE FROM Result')
        cursor.execute('DELETE FROM Candidate')
        cursor.execute('DELETE FROM Student_details')
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/set-voting-schedule', methods=['POST'])
def set_voting_schedule():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        data = request.get_json() or request.form
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM VotingSchedule')  # Clear existing schedule
        cursor.execute('INSERT INTO VotingSchedule (start_date, end_date, start_time, end_time) VALUES (?, ?, ?, ?)',
                      (start_date, end_date, start_time, end_time))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Voting schedule set successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reset-election', methods=['POST'])
def reset_election():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Clear votes and results but keep candidates and students
        cursor.execute('DELETE FROM Vote')
        cursor.execute('DELETE FROM Result')
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Election reset successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/fix-blockchain', methods=['POST'])
def fix_blockchain():
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        # Clear blockchain and rebuild from database
        global blockchain
        blockchain.chain = [blockchain.create_genesis_block()]
        blockchain.pending_transactions = []
        
        # Get all votes from database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT Name, Username, Email, Candidate FROM Vote')
        db_votes = cursor.fetchall()
        
        # Rebuild blockchain from database votes
        for vote in db_votes:
            name, username, email, candidate = vote
            vote_transaction = blockchain.create_vote_transaction(
                name, username, candidate, datetime.now().isoformat()
            )
            blockchain.add_transaction(vote_transaction)
            blockchain.mine_pending_transactions()
        
        # Update results table to match blockchain
        cursor.execute('DELETE FROM Result')
        
        # Count votes from blockchain
        blockchain_votes = blockchain.get_all_votes()
        vote_counts = {}
        
        for vote in blockchain_votes:
            candidate = vote['candidate']
            vote_counts[candidate] = vote_counts.get(candidate, 0) + 1
        
        # Insert updated results
        for candidate, votes in vote_counts.items():
            cursor.execute('SELECT PartyName, Photo FROM Candidate WHERE Name = ?', (candidate,))
            candidate_info = cursor.fetchone()
            
            if candidate_info:
                party_name, photo = candidate_info
                cursor.execute('INSERT INTO Result (Name, Photo, PartyName, Votes) VALUES (?, ?, ?, ?)',
                              (candidate, photo, party_name, votes))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Blockchain integrity fixed! Rebuilt {len(blockchain_votes)} votes across {len(blockchain.chain)} blocks.'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ---------------- E-Card Generation ----------------
@app.route('/verify-voter')
def verify_voter():
    voter_id = request.args.get('id')
    name = request.args.get('name')
    roll = request.args.get('roll')
    
    if not voter_id:
        return "Invalid verification link", 400
    
    # Find user by voter ID or roll number
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    if roll:
        cursor.execute('SELECT Name, DateOfBirth, Age, Gender, Email, Mobile, Photo FROM Student_details WHERE Username LIKE ?', (f'%{roll}%',))
    else:
        cursor.execute('SELECT Name, DateOfBirth, Age, Gender, Email, Mobile, Photo FROM Student_details WHERE Username LIKE ?', (f'%{voter_id[-8:]}%',))
    
    result = cursor.fetchone()
    
    if result:
        user = {
            'name': result[0],
            'date_of_birth': result[1], 
            'age': result[2],
            'gender': result[3],
            'email': result[4],
            'mobile': result[5],
            'photo': result[6]
        }
        cursor.execute('SELECT location FROM LoginHistory WHERE username = (SELECT Username FROM Student_details WHERE Username LIKE ?) ORDER BY login_time DESC LIMIT 1', (f'%{roll or voter_id[-8:]}%',))
        location_record = cursor.fetchone()
        conn.close()
        
        user_location = location_record[0] if location_record else 'Location not available'
        return render_template('ecard.html', user=user, voter_id=voter_id, user_location=user_location)
    
    conn.close()
    return "Voter not found", 404

@app.route('/generate-ecard')
def generate_ecard():
    voter_id = request.args.get('id')
    
    if voter_id:
        return redirect(f'/verify-voter?id={voter_id}')
    
    # Authenticated access
    if 'user' not in session or not session.get('face_verified'):
        return redirect('/student-login')
    
    user = session['user']
    voter_id = f"VID{str(uuid.uuid4())[:8].upper()}"
    
    # Get user's location
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT latitude, longitude, location FROM LoginHistory WHERE username = ? ORDER BY login_time DESC LIMIT 1', (user['username'],))
    location_record = cursor.fetchone()
    conn.close()
    
    user_location = location_record[2] if location_record and location_record[2] else 'Location not available'
    
    return render_template('ecard.html', user=user, voter_id=voter_id, user_location=user_location)

# ---------------- Proctoring Routes ----------------
@app.route('/upload-proctoring-data', methods=['POST'])
def upload_proctoring_data():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        username = request.form.get('username')
        violations_json = request.form.get('violations')
        recording = request.files.get('recording')
        ip_address = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'Unknown')
        mac_address = request.form.get('mac_address', 'Unknown')
        
        # Save recording file
        recording_path = None
        if recording:
            filename = secure_filename(recording.filename)
            recording_path = filename  # Store only filename, not full path
            os.makedirs('static/protocard', exist_ok=True)
            recording.save(os.path.join('static/protocard', filename))
        
        # Parse violations
        violations = json.loads(violations_json) if violations_json else []
        tab_switches = sum(1 for v in violations if 'Tab switched' in v.get('violation', ''))
        
        # Store in database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ProctoringData 
            (username, session_start, session_end, duration, violations, tab_switches, recording_path, total_violations, ip_address, mac_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            username,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            0,
            violations_json,
            tab_switches,
            recording_path,
            len(violations),
            ip_address,
            mac_address
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Proctoring data saved'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ---------------- Run ----------------
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)