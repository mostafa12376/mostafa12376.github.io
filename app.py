from flask import Flask, render_template, redirect, request, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
from sqlalchemy import DateTime
import uuid
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = uuid.uuid4().hex
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./db.sqlite'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)  
    password = db.Column(db.String(60), nullable=False)
    # TODO: use it for notes encryption
    secret = db.Column(db.String(32), unique=True, nullable=True)  
    reset_token = db.Column(db.String(32), unique=True, nullable=True)
    token_expiration = db.Column(DateTime, nullable=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def generate_reset_token(user, token_length=32):
    letters_and_digits = string.ascii_uppercase + string.digits

    current_time_minutes = int(datetime.now().timestamp() // 60)
    seed = user.secret + str(current_time_minutes)

    random.seed(seed)
    reset_token = ''.join(random.choice(letters_and_digits) for _ in range(token_length))

    return reset_token

def send_reset_email(email, token):
    # Act cool as you have smtp :)
    return ""


@app.route('/')
def home():
    if 'user_id' in session:
        user_notes = Note.query.filter_by(user_id=session['user_id']).all()
        return render_template('home.html', notes=user_notes)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email'] 
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        secret = uuid.uuid4().hex
        user = User(username=username, email=email, password=hashed_password, secret=secret)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate a random reset token and set expiration
            token = generate_reset_token(user)
            user.reset_token = token
            user.token_expiration = datetime.now() + timedelta(minutes=10)
            db.session.commit()
            
            # Send the reset token to the user's email 
            send_reset_email(user.email, token)
            flash('Check your email for a password reset link.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email address not found.', 'danger')
    return render_template('forgot_password.html')


@app.route('/reset_password/<reset_token>', methods=['GET', 'POST'])
def reset_password(reset_token):
    user = User.query.filter_by(reset_token=reset_token).first()
    if user and user.token_expiration > datetime.now():
        if request.method == 'POST':
            new_password = request.form['new_password']
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.password = hashed_password
            user.reset_token = None
            user.token_expiration = None
            db.session.commit()
            flash('Password reset successfully. You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
        return render_template('reset_password.html')
    flash('Invalid or expired reset token.', 'danger')
    return redirect(url_for('forgot_password'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'] 
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            # Login successful
            session['user_id'] = user.id
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get(user_id)
    if user:
        return render_template('profile.html', user=user)
    flash('User not found', 'danger')
    return redirect(url_for('home'))

@app.route('/add_note', methods=['GET', 'POST'])
def add_note():
    if 'user_id' in session:
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            user_id = session['user_id']
            note = Note(title=title, content=content, user_id=user_id)
            db.session.add(note)
            db.session.commit()
            flash('Note added successfully!', 'success')
            return redirect(url_for('home'))
        return render_template('add_note.html')
    return redirect(url_for('login'))

@app.route('/update_note/<int:id>', methods=['GET', 'POST'])
def update_note(id):
    if 'user_id' in session:
        note = Note.query.get(id)
        if note and note.user_id == session['user_id']:
            if request.method == 'POST':
                note.title = request.form['title']
                note.content = request.form['content']
                db.session.commit()
                flash('Note updated successfully!', 'success')
                return redirect(url_for('home'))
            return render_template('update_note.html', note=note)
        flash('You can only edit your own notes.', 'danger')
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/delete_note/<int:id>')
def delete_note(id):
    if 'user_id' in session:
        note = Note.query.get(id)
        if note and note.user_id == session['user_id']:
            db.session.delete(note)
            db.session.commit()
            flash('Note deleted successfully!', 'success')
        else:
            flash('You can only delete your own notes.', 'danger')
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, port=8000)