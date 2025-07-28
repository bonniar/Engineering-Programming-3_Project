from flask import Flask, render_template, request, redirect, session, flash,jsonify
import pymysql
import serial
import time
import threading
from datetime import datetime
import requests



app= Flask(__name__)
app.secret_key = 'secret@2025'

# Database connection
def get_db_connection():
    conn = pymysql.connect(
            host="localhost",
            user="root",
            password="project@2025",
            database="project",
            cursorclass=pymysql.cursors.DictCursor
        )
    return conn

def init_db():
    conn= get_db_connection()
    cursor = conn.cursor()
    

# Create table for users if not exists
    cursor.execute('''
               CREATE TABLE IF NOT EXISTS users (
                 user_id INT AUTO_INCREMENT PRIMARY KEY,
                 email  VARCHAR(100) NOT NULL,
                 name VARCHAR(100) NOT NULL,
                 surname VARCHAR(100) NOT NULL,
                 password VARCHAR(100) NOT NULL,
                 username VARCHAR(100) NOT NULL,
                 cell CHAR(10) NOT NULL,
                 role ENUM('admin', 'user') NOT NULL 
                 
                )'''
               )
    


#creating table for data from the sensor

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensors(
               sensor_id INT AUTO_INCREMENT PRIMARY KEY,
               user_id INT,
               indoors VARCHAR(10) NOT NULL,
               outdoors VARCHAR(10) NOT NULL,
               motion BOOLEAN NOT NULL,
               temperature FLOAT NOT NULL,
               humidity FLOAT NOT NULL,
               timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY (user_id) REFERENCES users (user_id)
               )
               ''')

    conn.commit()
    conn.close()

# Telegram Bot Setup
TELEGRAM_API_URL = "8308158915:AAFiLNv48EO8HEXmQtmyH6G13Zlha2JDRoQ"
CHAT_IDS = ["7064929794"]
def send_telegram_message(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_API_URL}/sendMessage"
        payload = {                    
        "chat_id": chat_id,
        "text": message
        }
        response = requests.post(url, data=payload)
        print("Telegram Response:", response.text)




init_db()

# Global serial connection
ser = None

def serial_reader():

    ser = serial.Serial('COM9', 9600)
    line = ser.readline().decode('utf-8').strip()
    if ser.in_waiting > 0:
     if line:
        # Parse Arduino data (format: "indoors,outdoors,motion,temperature,humidity")
        parts = line.split(',')
        if len(parts) == 5:
            data = {
                         'indoors': parts[0],
                         'outdoors': parts[1],
                         'motion': bool(int(parts[2])),
                         'temperature': float(parts[3]),
                         'humidity': float(parts[4])
                            }
            
            conn = get_db_connection()
            cursor = conn.cursor()
    
         
                            
            query="""
             INSERT INTO sensors( indoors, outdoors, motion, temperature, humidity, timestamp) VALUES (%s, %s, %s, %s, %s, %s)
             """
            cursor.execute(query, (
                                 data['indoors'],
                                data['outdoors'],
                                data['motion'],
                                data['temperature'],
                                data['humidity']
            ))
            conn.commit()
            conn.close()
            
        if ser:
                ser.close()
                ser = None
                time.sleep(2)
        
@app.route('/upload', methods=['POST','GET']) #Route for receiving data from ESP32
def upload():
    
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
         
                            
    query="""
        INSERT INTO sensors( indoors, outdoors, motion, temperature, humidity, timestamp) VALUES (%s, %s, %s, %s, %s, %s)
        """
    cursor.execute(query, (
        data.get('indoors'),
        data.get('outdoors'),
        data.get('motion',False),
        data.get('temperature'),
        data.get('humidity'),
        datetime.now()
        ))
    
    conn.commit()
    cursor.close()

    if data.get('temperature') > 60 and data.get('humidity') > 60:
            send_telegram_message("🔥 Alert! Temperature  is above 60°C & Humidity 60 % , there is a possibility of fire ")
            
        

    if data.get('motion',False):
            print("🚨 Motion detected! Sending Telegram alert...")
            send_telegram_message("🚨 Human detected by ESP32!")
            
        

    
    
    
    return jsonify({'status':'success'}),200


    

@app.route('/data', methods=['GET'])
def get_data():
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
                    SELECT indoors, outdoors, motion, temperature, humidity, timestamp
                    FROM sensors 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                        """)
    data = cursor.fetchall()

    # Prepare data for charts
    chart_data = {
                'timestamps': [str(item['timestamp']) for item in data],
                'temperature':  [float(item['temperature']) for item in data],
                'humidity':  [float(item['humidity']) for item in data],
                'motion':  [1 if item['motion'] else 0 for item in data],  # Convert to 1/0 for chart
                'indoors': [1 if item['indoors'] == 'ON' else 0 if item['indoors'] == 'OFF' else float(item['indoors']) for item in data],
                 'outdoors': [1 if item['outdoors'] == 'ON' else 0 if item['outdoors'] == 'OFF' else float(item['outdoors']) for item in data],
                'raw_data': data } # For table display
    return jsonify(chart_data)
    








@app.route('/', methods=['GET', 'POST']) #Route for the Signin page
def Login():
    

    if request.method == 'POST':
        username_or_email = request.form['username_or_email'] # get username_email from form
        password = request.form['fpasswd'] #get password from form
        role = request.form.get('role')  # Get role from form

        if not all([username_or_email, password, role]): 
            flash('Please fill all fields', 'danger')
            return redirect('/')
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
                SELECT * FROM users 
                WHERE (email = %s OR username = %s) 
                AND role = %s
            ''', (username_or_email, username_or_email, role)) 
                   
        use = cursor.fetchone()


       
        

        if use and use['password']== password:
            session['use'] = use['username']  # Store username in session
            columns = ['username_or_email', 'username_or_email', 'role']  # your actual column names
            use_dict = dict(zip(columns, use))
            session['role'] = use_dict['role']
           
            if use['role'] == 'user':

                if username_or_email == 'bonniar23@gmail.com' or username_or_email =='Risana' :
                    flash('Login successful!', 'success')
                    return redirect('/ldrdash')
                
                elif username_or_email == '221034684' or username_or_email == '221034684@edu.vut.ac.za':
                    flash('Login successful!', 'success')
                    return redirect('/oldrdash')
                
                elif username_or_email == '224071157@edu.vut.ac.za'  or username_or_email =='una':
                    flash('Login successful!', 'success')
                    return redirect('/pirdash')
                
                elif username_or_email == 'Siphesihle ' or username_or_email =='siphesihlengcobo959@gmail.com':
                    flash('Login successful!', 'success')
                    return redirect('/humdash')
                
                elif username_or_email == 'nk' or username_or_email =='219170932@edu.vut.ac.za              ':
                    flash('Login successful!', 'success')
                    return redirect('/tempdash')
                
                else:
                    flash('Login successful!', 'success')
                    return redirect('/dash')
                
                    


                
                
            else:

                
                
                flash('Login successful!', 'success')
                return redirect('/home')
            
            
        else:
            flash('Invalid credentials or role', 'danger') 
            return redirect('/')

    return render_template('signin.html')

@app.route('/signup',methods=['GET', 'POST'])
def sign():
    
    if request.method == 'POST':
        name = request.form['fname']
        sur = request.form['fsurname']
        email = request.form['femail']
        cell = request.form['fcell']
        user = request.form['fuser']
        password = request.form['fpasswd']
        role = request.form.get('role', 'user')
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO users (email, name, surname, password, username, cell, role) VALUES (%s, %s, %s, %s, %s, %s, %s)", (email, name, sur,  password, user, cell, role))
        conn.commit()
        return redirect('/')
    return render_template('signup.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/home') #Route for the Homepage
def Home():
    return render_template('index.html')

@app.route('/aboutdash')
def aboutdash():
    return render_template("aboutdash.html")
@app.route('/bout')
def bout():
    return render_template("bout.html")

@app.route('/dash')
def dash():

    if 'use' in session:
        return render_template("dash.html")  
    return redirect('/signin')

@app.route('/ldrdash')
def ldr():
    return render_template("ldrdash.html")

@app.route('/oldrdash')
def oldr():
    return render_template("oldrdash.html")

@app.route('/bou')
def bou ():
    return render_template("bout.html")


@app.route('/humdash')
def hum():
    return render_template('humdash.html')

@app.route('/adash')
def adash():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
                    SELECT indoors, outdoors, motion, temperature, humidity, timestamp 
                    FROM sensors 
                    ORDER BY timestamp DESC 
                    LIMIT 4
                        """)
    rows=cursor.fetchall()
    conn.commit()
    cursor.close()
    



    if 'use' in session:
        return render_template("adash.html", rows=rows)  
    return redirect('/signin')

@app.route('/pirdash')
def pir():
    return render_template("pirdash.html")

@app.route('/tempdash')
def temp():
    return render_template("tempdash.html") 

@app.route('/logout')
def logout():
    session.pop('use', None)
    flash('You have been logged out')
    return redirect('/')

if __name__== "__main__":
    # Start serial thread
    serial_thread = threading.Thread(target=serial_reader, daemon=True)
    serial_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)