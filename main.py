from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from datetime import date
from flask_mysqldb import MySQL
import MySQLdb.cursors
import mysql.connector
import re
import os
import flask
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
import nltk
from nltk.corpus import stopwords
from random import randint
from decimal import Decimal
from sklearn.preprocessing import StandardScaler
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
nltk.download('stopwords')
import pickle

conn = mysql.connector.connect(host="localhost", user="root", password="root", database="bitsbuddy", charset="utf8")

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = os.urandom(24)

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'bitsbuddy'

# Intialize MySQL
mysql = MySQL(app)

# Load the model from the pickle file
model = pickle.load(open('kmeans_model.pkl','rb'))
#knn_model = pickle.load(open('knn_model.pkl','rb'))
KNN_Price_model = pickle.load(open('KNN_Price_model.pkl','rb'))









@app.route('/')
def index():
    return render_template("index.html")

@app.route('/req')
def req():
    return render_template("/requestor/req.html")

@app.route('/work')
def work():
    return render_template("/worker/work.html")

@app.route('/host')
def host():
    
    
    return render_template("/host/host.html")
    
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if     something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts_users WHERE username LIKE %s AND password LIKE %s AND logintype LIKE %s', ([username], [password],'req'))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']

            # Redirect to home page
            return redirect('/home')
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('requestor/req.html', msg=msg)

@app.route('/loginwork', methods=['GET', 'POST'])
def loginwork():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts_users WHERE username = %s AND password = %s AND logintype=%s', (username, password,'wor'))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts_users table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            
            
            cursor.execute("UPDATE `worker_profile` SET `islogged_in`=%s WHERE `id`=%s", (1,session['id']))
            mysql.connection.commit()
            # Redirect to homework page
            return redirect('location')
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('/worker/work.html', error='Invalid username or password')   
   
@app.route('/location')
def location():
    return render_template("/worker/location.html")   

@app.route('/save-coordinates', methods=['GET', 'POST'])
def save_coordinates():
    id = flask.session['id']
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    # Perform some processing on the latitude and longitude data, if needed
    new_data = [[latitude, longitude]]

    # Predict the cluster for the new latitude and longitude
    cluster_prediction = model.predict(new_data)
    print("The cluster prediction for the new data point is:", cluster_prediction[0])

    # Update the database with the predicted cluster
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""UPDATE `worker_profile` set cluster =%s WHERE id=%s""", (cluster_prediction[0], id))
    mysql.connection.commit()

    # Return the cluster number
    return str(cluster_prediction[0])
   

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        logintype = request.form['account']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts_users WHERE username LIKE %s', [username])
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('INSERT INTO accounts_users VALUES (NULL,NULL, %s, %s, %s, %s)', (username, email, password, logintype))
            
            mysql.connection.commit()
            cursor.execute("UPDATE accounts_users SET `USERID`=CONCAT('ID_',id) where id like %s",[cursor.lastrowid])
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            # Redirect to login page
            return redirect(url_for('login'))
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)



@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
   cursor.execute("UPDATE `worker_profile` SET `islogged_in`=%s WHERE id=%s", (0,session['id']))
   mysql.connection.commit()
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   
   # Redirect to login page
   return redirect(url_for('index'))

#=========================================Requestor=======================================================================


@app.route('/home', methods=['GET', 'POST'])
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('requestor/home.html', username=session['username'])


    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route("/pickupdrop", methods=['GET','POST'])
def pickupdrop():
    msg = ''
    if request.method =="POST":
        task_type = 'Pick&Drop'
        status = 'Task Created'
        producttype = request.form['producttype']
        productsize = request.form['productsize']
        productweight = request.form['productweight']
        pickupadd = request.form['pickuploc']
        locator = Nominatim(user_agent="myGeocoder")
        picklocation = locator.geocode(pickupadd)
        
        pickup_lat = picklocation.latitude
        pickup_long = picklocation.longitude
        pickup_datetime = request.form['datetimelocal']
        dropoffadd = request.form['dropofloc']
        dropofflocation = locator.geocode(dropoffadd)
        del_lat = dropofflocation.latitude
        del_long = dropofflocation.longitude
        del_tentativetime = request.form['dropofdatetimelocal']
        id = flask.session['id']
        

        new_data = [[pickup_lat, pickup_long]]

        # Predict the cluster for the new latitude and longitude
        cluster_prediction = model.predict(new_data)
        print("The cluster prediction for the new data point is:", cluster_prediction[0])


        #insertion of the new task to mysql
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM accounts_profile WHERE id like '{}'".format(id))
        account = cursor.fetchone()
        cursor.execute("""INSERT INTO `trans_task`(`task_type`,`pro_type`,`pro_size`,`pro_weight`,`status`,`pickup_lat`,`pickup_long`,`pickup_datetime`,`del_lat`,`del_long`,`del_tentativetime`,`profile_id`,`pickup`,`dropof`,`cluster`) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')""".format(task_type, producttype, productsize, productweight,status, pickup_lat, pickup_long, pickup_datetime, del_lat,del_long,del_tentativetime,account['profile_id'],pickupadd,dropoffadd,cluster_prediction[0]))
        mysql.connection.commit()
                
        myDate = datetime.strptime(pickup_datetime, "%Y-%m-%d")
        # Today's Date is 2022-06-27
        todayDate = datetime.now()
        
        

        if myDate.date() == todayDate.date():
            #selecting the worker_id who is active and ready to accept the task request
            cursor.execute("""SELECT `worker_id` FROM `worker_profile` where islogged_in=%s AND `status`=%s AND cluster=%s LIMIT 1 """,('1','N',cluster_prediction[0]))
            worker = cursor.fetchone()
            
            if worker:
                w_id=worker['worker_id']
                cursor.execute("""SELECT A.* FROM `trans_task` as A join `accounts_profile` as P on A.profile_id = P.profile_id WHERE id like '{}' AND status like '{}'""".format(id,'Task Created'))
                task = cursor.fetchone()
                t_id=task['task_id']
                cursor.execute("""UPDATE `trans_task` SET TASKID=CONCAT('TID_',task_id), `status`=%s, worker_id=%s WHERE task_id=%s""",('Worker Assigned',w_id,t_id))
                cursor.execute("UPDATE `worker_profile` SET `status`=%s WHERE worker_id=%s",('Y',w_id))
                mysql.connection.commit()
                msg = 'Your request have been submitted'
                
            else:
                
                msg = 'Workers are busy, we will find another worker for your task to be completed'
                
        else:
            print('complete false')
            msg = 'Thank you for taking the time to submit your request.Our team will be working on it promptly and we will keep you updated on its progress.'
            
    return render_template('requestor/home.html', msg=msg)



        
@app.route('/myorder')
def myorder():

    id = flask.session['id']
    print(id)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""SELECT A.*,P.* FROM `trans_task` as A join `accounts_profile` as P on A.profile_id = P.profile_id where id like {} AND A.status NOT like 'Delivery completed'""".format(id))
    tasks = cursor.fetchall()

    
    if len(tasks) > 0 and tasks[0]['wor_rating'] is None:
        wor_rating = False
    else:
        wor_rating = True     
        
    return render_template("requestor/pickupdelivery.html", data=tasks, wor_rating=wor_rating)
    
    

@app.route('/worker_details', methods=['POST'])
def worker_details():
    task_id = flask.request.form.get('task_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""Select A.*,P.*,I.* FROM `trans_task` as A join `worker_profile` as W on A.worker_id = W.worker_id join `accounts_profile` as P on P.profile_id=W.profile_id  join `accounts_users` as I on I.id=P.id where task_id like '{}'""".format(task_id))
    work = cursor.fetchall()
    print(work)
    return flask.jsonify(work)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the profile page
        return render_template('requestor/profile.html', username=session['username'])


    # User is not loggedin redirect to login page
    return redirect(url_for('home'))



@app.route('/updateprofile', methods=['GET', 'POST'])
def updateprofile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page

        id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        Fullname = request.form['name']
        bdate = request.form['bdate']
        phone = request.form['phone']
        gender = request.form['gender']
        address = request.form['address']
        country = request.form['country']
        state = request.form['state']
        city = request.form['district']
        landmark = request.form['address']
        zipcode = request.form['zipcode']
        Occupation = request.form['Occupation']
        locator = Nominatim(user_agent="myGeocoder")
        location = locator.geocode(address)
        User_Latitude = location.latitude
        User_Longitude = location.longitude
        
        #age = calculateAge(date(1997, 2, 3))
        age = 20
        

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO accounts_profile VALUES (NULL,NULL,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s,NULL, %s)', (Fullname,bdate,age,gender,phone,address,country,state,city,landmark,zipcode,Occupation,User_Latitude,User_Longitude,session['id']))
        mysql.connection.commit()
        # Show the profile page with account info
        return render_template('/requestor/profile.html')
    # User is not loggedin redirect to login page
    return redirect(url_for('home'))



#==========================================Worker=======================================================================================================


@app.route('/homework', methods=['GET', 'POST'])
def homework():
    # Check if user is loggedin
    if 'loggedin' in session:
        id = flask.session['id']
        
        # User is loggedin show them the homework page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""SELECT * FROM `trans_task` as A join worker_profile as W on A.worker_id=W.worker_id WHERE id like {} and A.status not like 'Delivery Completed'""".format(id))
        worker = cursor.fetchall()
        accept = False
        if len(worker) > 0 and worker[0]['worker_accepttime'] is None:
            accept = False
        else:
            accept = True     
        if len(worker) > 0 and worker[0]['worker_pickup_loc_datetime'] is None:
            pickup = False
        else:
            pickup = True 

        if len(worker) > 0 and worker[0]['worker_del_loc_datetime'] is None:
            dropoff = False
        else:
            dropoff = True     
        
        return render_template('/worker/homework.html', data=worker, accept=accept, pickup = pickup, dropoff = dropoff)
    # User is not loggedin redirect to login page
    return redirect(url_for('loginwork'))

@app.route('/accept_task', methods=['GET','POST'])
def accept_task():
    now = datetime.now()
    task_id = flask.request.form.get('task_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("UPDATE `trans_task` SET status=%s, worker_accepttime=%s WHERE task_id=%s",('WAC',now,task_id))
    mysql.connection.commit()
    
    cursor.execute("""SELECT * FROM `trans_task` WHERE task_id and status like 'WAC'""".format(task_id))
    worker = cursor.fetchall()
    return render_template('/worker/homework.html', data=worker)


    
@app.route('/work_details', methods=['POST'])
def work_details():
    
    task_id = flask.request.form.get('task_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""Select * FROM `trans_task` where task_id like '{}'""".format(task_id))
    medical = cursor.fetchall()
    return flask.jsonify(medical)

@app.route("/update_pickup", methods=['POST'])
def update_pickup():
    task_id = request.form['task_id']
    now = datetime.now()

    # Connect to the MySQL database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Update the pickup status in the database
    cursor.execute("UPDATE `trans_task` SET status=%s, worker_pickup_loc_datetime=%s WHERE task_id=%s",('PickUpComplete',now,task_id))
    mysql.connection.commit()

    cursor.execute("""Select * FROM `trans_task` where task_id like '{}'""".format(task_id))
    account = cursor.fetchone()

    # Return success message
    return render_template('/worker/homework.html', account=account)


@app.route("/update_dropoff", methods=['POST'])
def update_dropoff():
    task_id = request.form['task_id']
    now = datetime.now()
    # Connect to the MySQL database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Update the pickup status in the database
    cursor.execute("UPDATE `trans_task` SET status=%s, worker_del_loc_datetime=%s WHERE task_id=%s",('Delivery Completed',now,task_id))  
    mysql.connection.commit()
    
    cursor.execute("SELECT worker_id FROM trans_task WHERE task_id like {}".format(task_id)) 
    account = cursor.fetchone()
    


    cursor.execute("UPDATE `worker_profile` SET status=%s WHERE worker_id=%s",('N',account['worker_id']))
    mysql.connection.commit()
    cursor.execute("""Select * FROM `trans_task` where task_id like '{}'""".format(task_id))
    account = cursor.fetchone()
    
    start = account["worker_pickup_loc_datetime"]
    end = account["worker_del_loc_datetime"]
    delta = datetime.strptime(end, '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(start, '%Y-%m-%d %H:%M:%S.%f')
    cursor.execute("UPDATE `trans_task` SET trip_time_inhrs=%s WHERE task_id=%s",(delta,task_id))
    mysql.connection.commit()

    # Return success message
    return render_template('/worker/homework.html', account=account)



@app.route("/submit_ratings", methods=["POST"])
def submit_ratings():
    task_id = request.form.get("task_id")
    rating = request.form.get("rating")
    print(rating)
    print(task_id)
    # Connect to the MySQL database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

     # Update the table in the database
    cursor.execute(f"UPDATE trans_task SET req_rating='{rating}' WHERE task_id='{task_id}'")
    mysql.connection.commit()
    

    return "Rating updated successfully!"

@app.route("/submit_rating_worker", methods=["POST"])
def submit_rating_worker():
    task_id = request.form.get("task_id")
    rating = request.form.get("rating")
    print(rating)
    print(task_id)
    # Connect to the MySQL database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

     # Update the table in the database
    cursor.execute(f"UPDATE trans_task SET wor_rating='{rating}' WHERE task_id='{task_id}'")
    mysql.connection.commit()
    

    return "Rating updated successfully!"



@app.route('/profilewo')
def profilewo():
    # Check if user is loggedin
    if 'loggedin' in session:
        id = flask.session['id']
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts_users WHERE id like {}'.format(id))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('/worker/profilewo.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('homework'))


#====================================Pick & drop ends============================================


#================================Admin=========================================================

@app.route('/admin')
def admin():
   cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
   cursor.execute("Select * FROM `trans_task` WHERE status like '{}'" .format('WA'))
   req_tasks = cursor.fetchall()
   cursor.execute("Select * FROM `worker_profile` WHERE islogged_in=%s",('1'))
   online_workers = cursor.fetchall()
   return render_template("admin.html", tasks=req_tasks, online=online_workers)
   

    
#================================Admin Ends=========================================================    
#new_data = pd.DataFrame([[20, 2, 1, 1, 1]], columns=['host_total_listings_count', 'accommodates', 'bathrooms', 'bedrooms', 'beds'])
#new_data = new_data.apply(pd.to_numeric)

# use the predict method to predict the price for the new data
#predicted_price = knn_model.predict(new_data)

# print the predicted price
#print('Predicted price:', predicted_price[0])




#================================Appointment code starts=========================================================    
# Define a function to predict the price using the KNN model
@app.route('/predict_price', methods=['POST'])
def predict_price():
  # parse the form data
  property_type = request.form['place-type']
  room_type = request.form['room_type']
  minimum_nights = request.form['minimum_nights']
  city = request.form.get('city')
  state = request.form.get('State')
  postcode = request.form.get('postcode')
  country = request.form.get('country')

  address = city + ", " + state + "," + postcode + ", " + country
  # create a Nominatim geocoder instance
  geolocator = Nominatim(user_agent="myGeocoder")
    # geocode the address
  location = geolocator.geocode(address)

  if location is not None:
        host_lat = location.latitude
        host_long = location.longitude
        print(host_lat,host_long)
  else:
       print("Could not find location for address:", address)

  # call your predict_price function to get the predicted price
  new_data = pd.DataFrame({'latitude': [host_lat], 'longitude': [host_long]})
  # Use the KNN model to predict the price
  predicted_price = KNN_Price_model.predict(new_data)[0]
  print(predicted_price)

  # store the predicted price in a session variable
  session['predicted_price'] = predicted_price
  session['host_lat'] = host_lat
  session['host_long'] = host_long
  session['property_type'] = property_type
  session['room_type'] = room_type
  session['minimum_nights'] = minimum_nights
  


  # return the predicted price as a JSON response
  return jsonify({'predicted_price': predicted_price})

@app.route('/submit', methods=['GET','POST'])
def submit():
    price = request.form.get('price')
    print(price)
    # do something with the submitted price, such as calculate the predicted price
    # retrieve the predicted price from the session variable
    predicted_price = session.get('predicted_price', None)
    print(predicted_price)
    host_lat = session.get('host_lat', None)
    host_long = session.get('host_long', None)
    property_type = session.get('property_type', None)
    room_type = session.get('room_type', None)
    minimum_nights = session.get('minimum_nights', None)
    guests = 0
    bedrooms = 0
    beds = 0
    bathrooms = 0
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('INSERT INTO listing (id, name, property_type, room_type, guests, bedrooms, beds, bathrooms, latitude, longitude, minimum_nights, price) VALUES (NULL, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (property_type, room_type, guests, bedrooms, beds, bathrooms, host_lat, host_long, minimum_nights, price))
    mysql.connection.commit()
    

    return render_template("/host/check.html") 


@app.route('/check')
def check():
    return render_template("/host/check.html")  


#================================Appointment code Ends=========================================================    



if __name__ == "__main__":
    app.run(debug=True)
    

