from flask import Flask, request, render_template, redirect, url_for, flash
import mysql.connector
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.secret_key = "235676543dfghredfg"

app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "Amol@12345"
app.config['MYSQL_DB'] = "appointment_db"

mysql = MySQL(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

# User Class
class User(UserMixin):
    def __init__(self, user_id, name, email, date, time):
        self.id = user_id
        self.name = name
        self.email = email
        self.date = date
        self.time = time

    @staticmethod
    def get(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT name, email, date, time FROM appointments WHERE id = %s', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return User(user_id, result[0], result[1], result[2], result[3])

# Load User
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

#Home Page Route
@app.route('/')
def index():
    return render_template('index.html')

#Registration Page route
@app.route('/appinment', methods=['POST', 'GET'])
def appinmnet():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        date = request.form['date']
        time = request.form['time']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id FROM appointments WHERE email = %s', (email,))
        user_data = cursor.fetchone()

        if user_data:
            flash("Email already registered!")
        else:
            cursor.execute(
                'INSERT INTO appointments(name, email, password, date, time) VALUES (%s, %s, %s, %s, %s)',
                (name, email, hashed_password, date, time)
            )
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('success'))

    return render_template('appinment.html')


@app.route('/success')
def success():
    return render_template('success.html')


# formatted_time = datetime.strptime(str(user_data[5]), "%H:%M:%S").strftime("%I:%M %p")



@app.route('/checkAppointment', methods=['GET', 'POST'])
def check_appointment():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, name, email, password, date, time FROM appointments WHERE email = %s', (email,))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data and bcrypt.check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2], user_data[4], user_data[5])
            formatted_time = datetime.strptime(str(user_data[5]), "%H:%M:%S").strftime("%I:%M %p")

            # Include 'id' field in the appointment dictionary
            appointment = {
                'id': user_data[0],
                'date': user_data[4],
                'time': formatted_time
            }
            login_user(user)
            return render_template('checkAppoinment.html', appointments=[appointment])
        else:
            flash("Invalid email or password", "error")

    return render_template('checkAppoinment.html')



@app.route('/appointment_details')
@login_required
def appointment_details():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT name, date, time FROM appointments WHERE email = %s", (current_user.email,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        appointment = {
            'name': result[0],
            'date': result[1],
            'time': result[2]
        }
        return render_template('appointment_details.html', appointment=appointment)
    else:
        flash("No appointment found.")
        return redirect(url_for('check_appointment'))
    

@app.route('/deletepage/<int:id>', methods=['POST'])
def deletepage(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM appointments WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()

    flash("Appointment deleted successfully!", "success")
    return redirect(url_for('check_appointment')) 


@app.route('/editData/<int:id>', methods=['GET', 'POST'])
@login_required
def editData(id):
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        time = request.form['time']

        # Update the record
        cursor.execute("""
            UPDATE appointments 
            SET name = %s, date = %s, time = %s 
            WHERE id = %s
        """, (name, date, time, id))
        mysql.connection.commit()
        cursor.close()

        flash("Appointment updated successfully!", "success")
        return redirect(url_for('check_appointment'))

    else:
        # Fetch appointment data to prefill the form
        cursor.execute("SELECT id, name, email, password, date, time FROM appointments WHERE id = %s", (id,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            appointment = {
                'id': result[0],
                'name': result[1],
                'email': result[2],
                'password': result[3],
                'date': result[4],
                'time': result[5]
            }
            return render_template('editpage.html', appointments=[appointment])
        else:
            flash("Appointment not found", "error")
            return redirect(url_for('check_appointment'))



# Run the app
if __name__ == '__main__':
    app.run(debug=True)
