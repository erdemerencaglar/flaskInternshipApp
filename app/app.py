
import re  
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__) 

app.secret_key = 'abcdefgh'
  
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'cs353hw4db'
  
mysql = MySQL(app)  


# TODO: SUMMARY PAGE
# TODO: UI
# TODO: GPA NUMBER

# DONE:
# PREVIOUS PAGE LINK
# ADD AUTHORIZATION 
# IF NO COMPANY - MESSAGE
# REGISTRATION
# APPLY
# LOGOUT

authenticationErrorMessage = "Please login to access this page!"
@app.route('/')

@app.route('/login', methods =['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM student WHERE sname = % s AND sid = % s', (username, password, ))
        user = cursor.fetchone()
        if user:              
            session['loggedin'] = True
            session['userid'] = user['sid']
            session['username'] = user['sname']
            session['dept'] = user['dept']
            session['gpa'] = user['gpa']
            message = 'Logged in successfully!'
            return redirect(url_for('mainpage'))
        else:
            message = 'Please enter correct username and password!'
    return render_template('login.html', message = message)


@app.route('/register', methods =['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'sname' in request.form and 'studentid' in request.form and 'bdate' in request.form and 'dept' in request.form and 'year' in request.form and 'gpa' in request.form:
        
        sname = request.form['sname']
        student_id = request.form['studentid']
        bdate = request.form['bdate']
        dept = request.form['dept']
        year = request.form['year']
        gpa = request.form['gpa']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM student WHERE sid = % s', (student_id, ))
        account = cursor.fetchone()

        if not sname:
            message = 'Please fill out the form completely!^^' + "-- " + sname + " " + student_id + " " + bdate + " " + dept + " " + year + " " + gpa
        elif account:
            # Assuming that student ID's are unique provided by the university
            message = 'Please enter your student ID correctly!' 
        else:
            cursor.execute('INSERT INTO student (sid, sname, bdate, dept, year, gpa) VALUES (%s, %s, %s, %s, %s, %s)', (student_id,  sname, bdate, dept, year, gpa,))
            mysql.connection.commit()
            message = 'User successfully created!'
            return redirect(url_for('login'))

    elif request.method == 'POST':

        message = 'Please fill all the fields!'
    return render_template('register.html', message = message)

@app.route('/mainpage', methods =['GET', 'POST'])
def mainpage():
    if not session['userid']:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM company natural join apply natural join student WHERE sid = % s', (session['userid'],))
    companies = cursor.fetchall()
    return render_template("mainpage.html", companies=companies)


@app.route('/cancel/<company_id>', methods =['GET'])
def cancel(company_id):
    if not session['userid']:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    message = ''
    deletion = cursor.execute('DELETE FROM apply WHERE cid = %s and sid = %s', (company_id, session['userid']))
    if deletion: 
        mysql.connection.commit()
        message = 'Application successfully cancelled!'
        return redirect(url_for('mainpage'))      
    else: 
        message = 'Cancellation error!'
    cursor.execute('SELECT * FROM company natural join apply natural join student WHERE sid = % s', (session['userid'],))
    companies = cursor.fetchall()      
    return render_template('mainpage.html', companies = companies, message = message)

@app.route('/apply', methods =['GET', 'POST'])
def apply():
    if not session['userid']:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM apply WHERE sid = % s', (session['userid'],))
    appliedCompanies = cursor.fetchall()
    message = ""

    if len(appliedCompanies) >= 3:
        message = "You cannot apply for more internships! In order to apply, please cancel one of your previous applications..."
        return render_template("errorpage.html", message = message)
    else:
        # TODO: IF QUOTA FULL -> DO NOT SHOW
        cursor.execute('SELECT * FROM company WHERE gpa_threshold <= %s AND cid NOT IN (SELECT cid FROM apply WHERE sid = %s) AND quota > (SELECT COUNT(sid) FROM apply WHERE cid = company.cid)', (session['gpa'], session['userid'],))
        companiesToApply = cursor.fetchall()
        if request.method == 'POST' and 'companyid' in request.form:
            company_id = request.form['companyid']
            student_id = session['userid']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO apply (sid, cid) VALUES (%s, %s)', (student_id, company_id,))
            mysql.connection.commit()
            message = 'Succesfully applied for company with ID ' + company_id
            return redirect(url_for('mainpage'))
        return render_template("apply.html", companies = companiesToApply, message = message)

    return render_template('login.html', message = message)

@app.route('/logout', methods =['POST'])
def logout():
    session['loggedin'] = False
    session['userid'] = ""
    session['username'] = ""
    session['dept'] = ""
    session['gpa'] = ""
    return redirect(url_for('login'))
    


# 1. List the name, quota, and gpa-thresholds of the companies applied by the student, in descending order of quotas.

# 2. Find the maximum and minimum gpa-thresholds of the companies applied by the student.
# Name the attributes of the resulting table as max-gpa-threshold and min-gpa-threshold, respectively.

# 3. Find the number of companies applied by the student in each city. Name the attributes of the
# resulting table as city and application-count.

# 4. Give the names of the companies applied by the student with the maximum and minimum
# quotas. Name the attributes of the resulting table as company-with-max-quota and companywith-min-quota, respectively. 
@app.route('/summary', methods =['GET', 'POST'])
def summary():
    if not session['userid']:
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM company natural join apply natural join student WHERE sid = % s ORDER BY quota DESC', (session['userid'],))
    appliedCompanies = cursor.fetchall()
    cursor.execute('SELECT FORMAT(MAX(gpa_threshold),2) AS max_gpa_threshold FROM company natural join apply WHERE sid = % s', (session['userid'],))
    maxgpa = cursor.fetchone()
    cursor.execute('SELECT FORMAT(MIN(gpa_threshold),2) AS min_gpa_threshold FROM company natural join apply WHERE sid = % s', (session['userid'],))
    mingpa = cursor.fetchone()
    cursor.execute('SELECT COUNT(*) AS application_count, city FROM company natural join apply WHERE sid = % s GROUP BY city', (session['userid'],))
    citiesAppCount = cursor.fetchall()
    cursor.execute('SELECT cname as company_with_min_quota FROM company NATURAL JOIN (SELECT MIN(quota) as quota FROM company natural join apply WHERE sid = % s) AS MIN_QUOTA', (session['userid'],))
    minquota = cursor.fetchone()
    cursor.execute('SELECT cname as company_with_max_quota FROM company NATURAL JOIN (SELECT MAX(quota) as quota FROM company natural join apply WHERE sid = % s) AS MAX_QUOTA', (session['userid'],))
    maxquota = cursor.fetchone()
    return render_template('summary.html', appliedCompanies = appliedCompanies, maxgpa = maxgpa, mingpa = mingpa, citiesAppCount = citiesAppCount, minquota = minquota, maxquota = maxquota)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
