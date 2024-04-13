# Library used in code
from flask import Flask, render_template, request, redirect, url_for, Response, flash, jsonify
import speech_recognition as sr
from google.cloud import texttospeech as tts
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import func,text
import base64
import cv2
import json
import os
import RPi.GPIO as GPIO
import time
from flask_mail import Mail, Message
import requests
from bs4 import BeautifulSoup

# s
app = Flask(__name__)
# CORS(app)
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/Sebasty/Desktop/updated-ui/demo.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'demo.json'
# Initialize TextToSpeechClient
client = tts.TextToSpeechClient()

enA = 17
in1 = 27
in2 = 22
enB = 18
in3 = 14
in4 = 15

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(enA, GPIO.OUT)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(enB, GPIO.OUT)
GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)
p1 = GPIO.PWM(enA, 1000)
p2 = GPIO.PWM(enB, 1000)
p1.start(95)
p2.start(100)

    
    
# For Database
# configuration of the database 
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'survey_secret'

db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sebastyemail@gmail.com'
app.config['MAIL_PASSWORD'] = 'xoinyydlchzzpklf'
app.config['MAIL_DEFAULT_SENDER'] = 'sebastyemail@gmail.com'  # Default sender email address

mail = Mail(app)

class Survey1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(225))
    There_Department = db.Column(db.String(50))
    There_TDepartment = db.Column(db.String(50))
    rating = db.Column(db.Integer)
    suggestion = db.Column(db.Text)
    srating = db.Column(db.Integer)
    
class Slider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)

class Aboutimage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)

class Coursesimage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)

class Administration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)
    
class QA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String)
    answer = db.Column(db.String)
    call_count = db.Column(db.Integer, default=0)

class Displayfqa(db.Model):
    id =   db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String)
    answer = db.Column(db.String)
    
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    announcement = db.Column(db.String)
    

def load_responses():
    if os.path.exists('responses.json'):
        with open('responses.json', 'r') as file:
            return json.load(file)
    return {}

def save_responses(responses):
    with open('responses.json', 'w') as file:
        json.dump(responses, file, indent=4)

def load_unknown_questions():
    if os.path.exists('unknown_questions.json'):
        with open('unknown_questions.json', 'r') as file:
            return json.load(file)
    return []

def save_unknown_questions(unknown_questions):
    with open('unknown_questions.json', 'w') as file:
        json.dump(unknown_questions, file, indent=4)

def store_unknown_question(question):
    unknown_questions = load_unknown_questions()
    unknown_questions.append(question)
    save_unknown_questions(unknown_questions)


# For Camera Settings
def generate_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')               

# Route Index Login page
@app.route('/')
def index():
    return render_template('Login.html')

# Route Login Settings 
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == 'Sebasty' and password == '12345':
        return redirect(url_for('admin'))
    elif username == 'Sebastyui' and password == '1233':
       return redirect(url_for('SEBASTYINDEX'))
    else:
        return render_template('Login.html', message='Invalid username or password. Please try again.')

# Admin interface
# Admin interface
@app.route('/admin')
def admin():
    camera_feed_url = url_for('video_feed')
    top_questions = Displayfqa.query.limit(5).all()
    top_qas = QA.query.order_by(QA.call_count.desc()).limit(3).all()
    query = text("""
        SELECT 
            There_TDepartment AS Target_Department,
            COUNT(*) AS total_voter,
            COUNT(*) * 5 AS expected_total_stars,
            SUM(rating) AS total_earned_stars
        FROM 
            Survey1
        GROUP BY 
            There_TDepartment;
        """)

    conn = db.engine.connect()
    results = conn.execute(query)
    average_ratings = results.fetchall()

    query_overall_srating = text("""
        SELECT 
            AVG(srating) AS overall_average_rating,
            COUNT(*) AS    Stotal_voter,
            COUNT(*) * 5 AS Sexpected_total_stars,
            SUM(srating) AS Stotal_earned_stars
        FROM Survey1
        """)

    # Execute the query for overall school rating
    results_overall_srating = conn.execute(query_overall_srating)
    overall_srating = results_overall_srating.fetchall()

    surveys = Survey1.query.all()
    conn.close()

    unknown_questions = load_unknown_questions()

    # Initialize a set to keep track of unique questions
    unique_questions = set()

    # Filter out repetitive questions
    unique_unknown_questions = []
    for question in unknown_questions:
        if question.lower() not in unique_questions:
            unique_unknown_questions.append(question)
            unique_questions.add(question.lower())
            
    return render_template('Admin.html',top_questions=top_questions,top_qas=top_qas, surveys=surveys, average_ratings=average_ratings, overall_srating=overall_srating, unknown_questions=unique_unknown_questions,camera_feed_url = url_for('video_feed'))


  
# Admin Form-Post
# Update form Slider
@app.route('/upload_slider', methods=['GET','POST'])
def upload_slider():
    if request.method == 'POST':
        slider_name = request.form['Slide_name']
        slider_image = request.files['image'].read()
        existing_slider = Slider.query.filter_by(name=slider_name).first()
        if existing_slider:
            existing_slider.image = slider_image
            db.session.commit()
            flash('Slider image updated successfully', 'success')
        else:
            new_slider = Slider(name=slider_name, image=slider_image)
            db.session.add(new_slider)
            db.session.commit()
            flash('New slider uploaded successfully', 'success')
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))

@app.route("/control", methods=["POST"])
def control():
    direction = request.form["direction"]
    if direction == "backward":
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
        return redirect(url_for('admin'))
    elif direction == "forward":
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
        return redirect(url_for('admin'))
    elif direction == "right":
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
        time.sleep(3)
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.LOW)
        return redirect(url_for('admin'))
    elif direction == "left":
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
        time.sleep(3)
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.LOW)
        return redirect(url_for('admin'))
    elif direction == "stop":
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.LOW)
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))

# Update form About
@app.route('/upload_About', methods=['GET','POST'])
def upload_About():
    if request.method == 'POST':
        About_name = request.form['About_name']
        About_image = request.files['About_image'].read()
        existing_About = Aboutimage.query.filter_by(name=About_name).first()
        if existing_About:
            existing_About.image = About_image
            db.session.commit()
            flash('About image updated successfully', 'success')
        else:
            new_slider = Aboutimage(name=About_name, image=About_image)
            db.session.add(new_slider)
            db.session.commit()
            flash('New About uploaded successfully', 'success')
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))

# Update form Courses
@app.route('/upload_Course', methods=['GET','POST'])
def upload_Course():
    if request.method == 'POST':
        Course_name = request.form['Course_name']
        Course_image = request.files['Course_image'].read()
        existing_Course = Coursesimage.query.filter_by(name=Course_name).first()
        if existing_Course:
            existing_Course.image = Course_image
            db.session.commit()
            flash('Course image updated successfully', 'success')
        else:
            new_Course = Coursesimage(name=Course_name, image=Course_image)
            db.session.add(new_Course)
            db.session.commit()
            flash('New Course uploaded successfully', 'success')
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))

# Update form Administration
@app.route('/upload_Administration', methods=['GET','POST'])
def upload_Administration():
    if request.method == 'POST':
        Administration_name = request.form['Administration_name']
        Administration_image = request.files['Course_image'].read()
        existing_Administration = Administration.query.filter_by(name=Administration_name).first()
        if existing_Administration:
            existing_Administration.image = Administration_image
            db.session.commit()
            flash('Administration image updated successfully', 'success')
        else:
            new_Administration = Administration(name=Administration_name, image=Administration_image)
            db.session.add(new_Administration)
            db.session.commit()
            flash('New Administration uploaded successfully', 'success')
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))
  
# Button Funtions
# Delete button for the individual survey
@app.route('/delete/<int:id>')
def delete(id):
    survey = Survey1.query.get_or_404(id)
    db.session.delete(survey)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete1/<int:qa_id>')
def delete_qa(qa_id):
    # Find the question by ID
    question = QA.query.get_or_404(qa_id)
    # Delete the question from the database
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('admin'))  # Redirect back to the admin page after deletion

@app.route('/updatefqa/<int:qa_id>')
def send_qa(qa_id):
    # Find the question by ID in the QA table
    question = QA.query.get(qa_id)
    if question:
        # Create a new entry in the Displayfqa table with the same question and answer
        display_question = Displayfqa(question=question.question, answer=question.answer)
        db.session.add(display_question)
        db.session.commit()
        # Optionally, you can delete the question from the QA table after sending
        db.session.delete(question)
        db.session.commit()
    return redirect(url_for('admin'))  # Redirect back to the admin page after sending

# Delete all Data at table Survey1
@app.route('/delete_all', methods=['POST'])
def delete_all():
    Survey1.query.delete()
    db.session.commit()
    return redirect(url_for('admin'))

# Logout Settings
@app.route('/logout')
def logout():
    return redirect(url_for('index'))

# Sebasty UI Settings
@app.route('/SEBASTYINDEX')
def SEBASTYINDEX():
    announcement = Announcement.query.first()  # Assuming you want the first announcement
    slides = {
        'Slide1': None,
        'Slide2': None,
        'Slide3': None,
        'Slide4': None
    }
    
    abouts = Aboutimage.query.all() 
    
    courses = {
        'GradeSchool': None,
        'JuniorHighSchool': None,
        'ABM': None,
        'HUMSS': None,
        'STEM': None,
        'BSHM': None,
        'BSTM': None,
        'BSFM': None,
        'BSBAMM': None,
        'BSCOMM': None,
        'BSA & BSMA': None,
        'BSPSYCH': None,
        'BSIEBSECE': None,
        'BSCPE': None,
        'BSIT': None,
        'BSCRIM': None,
        'BSN': None
    }

    for name, _ in courses.items():
        courses[name] = Coursesimage.query.filter_by(name=name).first()
        
    for slide, _ in slides.items():
        slides[slide] = Slider.query.filter_by(name=slide).first()
        

    for about in abouts:
        about.image = base64.b64encode(about.image).decode('utf-8')
        
    for name, course in courses.items():
        if course:
            course.image = base64.b64encode(course.image).decode('utf-8')
            
    for name, slide in slides.items():
        if slide:
            slide.image = base64.b64encode(slide.image).decode('utf-8')

    return render_template('SEBASTYINDEX.html', slides=slides, abouts=abouts, courses=courses,announcement=announcement)

#Survey Settings Sebastyui2 
@app.route('/survey', methods=['GET', 'POST'])
def formsurvey():
    if request.method == 'POST':
        name = request.form['name']
        There_Department = request.form['There_Department']
        There_TDepartment = request.form['There_TDepartment']
        rating = request.form['department_rating']
        suggestion = request.form['suggestion']
        srating = request.form['schoolrating']
        
        with app.app_context():
            new_survey = Survey1(name=name,There_Department=There_Department,There_TDepartment=There_TDepartment,rating=rating,suggestion=suggestion,srating=srating)
            db.session.add(new_survey)
            db.session.commit()
        
        flash('Survey submitted successfully', 'success')
        return render_template('Sebastyui.html')
    return render_template('Sebastyui.html')
  
@app.route('/SebastyUI')
def SebastyUI():
    top_questions = Displayfqa.query.limit(5).all()
    return render_template('Sebastyui.html', top_questions=top_questions)
  

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input'].lower()
    
    # Update call count for the question in the database or save it if it's new
    question = QA.query.filter_by(question=user_input).first()
    if question:
        question.call_count += 1
    else:
        # If the question is new, save it to the database
        question = QA(question=user_input, answer="", call_count=1)
        db.session.add(question)
    
    # Commit changes to the database
    db.session.commit()
    
    # Your existing code for handling responses
    responses = load_responses()
    bot_response = ''
    if user_input == 'quit':
        bot_response = "Goodbye!"
    elif user_input in responses:
        bot_response = responses[user_input]
    else:
        # Store unknown question to a JSON file
        store_unknown_question(user_input)
        bot_response = "Sorry, I don't know the answer to that question."
    
    return jsonify({'bot_response': bot_response})


# @app.route('/chat', methods=['POST'])

# def chat():
#     user_input = request.form['user_input'].lower()
#     responses = load_responses()
#     bot_response = ''
#     if user_input == 'quit':
#         bot_response = "Goodbye!"
#     elif user_input in responses:
#         bot_response = responses[user_input]
#     else:
#         # Store unknown question to a JSON file
#         store_unknown_question(user_input)
#         bot_response = "Sorry, I don't know the answer to that question."
#     return jsonify({'bot_response': bot_response})


# @app.route('/chat', methods=['POST'])
# def chat():
#     user_input = request.form['user_input'].lower()
#     qa_entry = QA.query.filter_by(question=user_input).first()
#     responses = load_responses()
#     bot_response = ''

#     if user_input == 'quit':
#         bot_response = "Goodbye!"
#     elif user_input in responses:
#         qa_entry.call_count += 1
#         # db.session.commit()
#         bot_response = responses[user_input]
#         # Set the bot response to the answer stored in the database
#         # bot_response = qa_entry.answer
#     else:
#        # Store unknown question to a JSON file
#         store_unknown_question(user_input)
#         new_qa = QA(question=user_input, answer=None, call_count=0)
#         bot_response = "Sorry, I don't know the answer to that question."
#         db.session.commit()
#     return jsonify({'bot_response': bot_response})

#  # Check if the question exists in the database
#         if qa_entry:
#             # If the question exists, update the call_count
#             qa_entry.call_count += 1
#         else:
#             # If the question doesn't exist, create a new entry
#             new_qa = QA(question=user_input, answer=None, call_count=0)
#             db.session.add(new_qa)
#             # Store unknown question to a JSON file
#             store_unknown_question(user_input)
#             db.session.commit()
#             bot_response = "Sorry, I don't know the answer to that question."


# Update the /answer route to handle the form submission
from flask import redirect, url_for

@app.route('/answer', methods=['POST'])
def answer():
    num_questions = int(request.form['num_questions'])
    responses = load_responses()

    for i in range(1, num_questions + 1):
        original_question_key = f"original_question_{i}"
        answer_key = f"answer_{i}"
        original_question = request.form.get(original_question_key)
        answer = request.form.get(answer_key)

        if original_question and answer:
            # Update or create entry in the database
            qa_entry = QA.query.filter_by(question=original_question).first()
            if qa_entry:
                # Update existing entry
                qa_entry.answer = answer
            else:
                # Create new entry
                qa_entry = QA(question=original_question, answer=answer, call_count=0)
                db.session.add(qa_entry)
                
            # Update responses dictionary
            responses[original_question.lower()] = answer

    save_responses(responses)

    # Remove answered questions from the list of unknown questions
    unanswered_questions = [request.form.get(f"original_question_{i}") for i in range(1, num_questions + 1)
                             if not request.form.get(f"answer_{i}")]

    save_unknown_questions(unanswered_questions)
    
    # Commit changes to the database
    db.session.commit()

    return redirect(url_for('admin'))


@app.route('/convert', methods=['POST'])
def convert():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=3)
    try:
        text = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        text = "Could not understand audio"
    except sr.RequestError as e:
        text = "Error: {0}".format(e)
    return text

@app.route('/synthesize', methods=['POST'])
def synthesize():
    text_input = request.form['text']
    
    synthesis_input = tts.SynthesisInput(text=text_input)

    voice = tts.VoiceSelectionParams(
        language_code="fil-PH",
        name='fil-PH-Standard-A'
    )

    audio_config = tts.AudioConfig(
        audio_encoding=tts.AudioEncoding.MP3,
        effects_profile_id=['small-bluetooth-speaker-class-device'],
        speaking_rate=1,
        pitch=1
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    return response.audio_content, 200, {'Content-Type': 'audio/mpeg'}

@app.route('/announce', methods=['GET', 'POST'])
def announce():
    if request.method == 'POST':
        announcement_text = request.form.get('announcement')
        # Assuming there's only one announcement row you're editing:
        announcement = Announcement.query.first()
        if announcement:
            announcement.announcement = announcement_text
        else:
            announcement = Announcement(name="Main", announcement=announcement_text)
            db.session.add(announcement)
        db.session.commit()
        return redirect(url_for('admin'))
    else:
        announcement = Announcement.query.first()
        return render_template('Admin.html', announcement_text = announcement.announcement if announcement else "")
    
@app.route('/senitback/<int:question_id>', methods=['GET', 'POST'])
def delete_question(question_id):
    # Assuming you're using SQLAlchemy
    display_question = Displayfqa.query.get(question_id)
    if display_question:
        # Create a new record in QA with 0 call count
        new_qa_question = QA(question=display_question.question, answer=display_question.answer, call_count=0)
        db.session.add(new_qa_question)
        db.session.commit()

        # Delete the question from Displayfqa
        db.session.delete(display_question)
        db.session.commit()

    # Redirect back to the page displaying the questions
    return redirect('/admin')

@app.route('/send_email', methods=['POST'])

def send_email():
    # Make an HTTP GET request to the URL
    response = requests.get("http://127.0.0.1:5000/admin#results")
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    # Extract the section you want to send
    section = soup.find(id='results')
    # Prepare email message
    msg = Message("Section from Admin Panel", recipients=["dmpsml1@gmail.com"])
    # Include the HTML content of the section in the email body
    msg.html = section.prettify()
    # Send email
    mail.send(msg)
    return redirect(url_for('admin'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

