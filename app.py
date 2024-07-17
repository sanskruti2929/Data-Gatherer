
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey

app = Flask(__name__)

############################################ Configure the database URI ######################################################
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/your_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

offset = 0

# Initialize the SQLAlchemy extension
db = SQLAlchemy(app)

class College(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

############################################## Define your models here ######################################################
# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    is_marketing_associate = db.Column(db.Boolean, default=None)

# Contact_Details model
class ContactDetails(db.Model):
    contact_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    college_id = db.Column(db.Integer, ForeignKey('india_state_organization.college_id'), nullable=False)
    website_link = db.Column(db.String(100))
    name = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    marketer_id = db.Column(db.Integer, nullable=True)
    first_call = db.Column(db.Enum('yes', 'unanswered'), nullable=True)
    follow_up_call = db.Column(db.Enum('yes', 'unanswered'), nullable=True)
    preferred_mode = db.Column(db.Enum('phone', 'email'), nullable=True)
    response = db.Column(db.Enum('yes', 'maybe', 'no'), nullable=True)
    remarks = db.Column(db.Text)

#IndiaStateOrganization Model
class IndiaStateOrganization(db.Model):
    college_id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)    

########################################################### Main Page ###################################################################  
 
@app.route('/', methods=['GET'])
def home():
    print("Rendering home page")
    return render_template('main_page.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Perform authentication logic here (compare username and password with database)
    # For simplicity, I'm just checking if the username is 'admin' and password is 'admin'
    if username == 'admin' and password == 'admin':
        return redirect(url_for('admin_page'))
    else:
        return render_template('main_page.html', message='Invalid credentials. Please try again.')
    
############################################################# Admin Page ################################################################

@app.route('/admin')
def admin_page():
    return render_template('admin_page.html')

@app.route('/submit_admin', methods=['POST'])
def submit_admin():
    college_name = request.form['collegeName']
    csv_file = request.files['csvFile']

    # Save the CSV file to the 'uploads' folder with a unique filename
    if csv_file:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = os.path.join(app.config['UPLOAD_FOLDER'], f'{timestamp}_{csv_file.filename}')
        csv_file.save(filename)
    else:
        filename = None

    # Add the college to the database
    college = College(name=college_name)
    db.session.add(college)
    db.session.commit()

    # Redirect to admin page with a success message
    return render_template('admin_page.html', success_message='Data submitted successfully.')

###################################################### Add New User Page ##################################################

@app.route('/admin/add_new_user_page')
def add_new_user_page():
    return render_template('new_user.html')

@app.route('/admin/submit_new_user', methods=['POST'])
def submit_new_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_marketing_associate = request.form.get('is_marketing_associate') == 'on'
        
        new_user = User(username=username, password=password, is_marketing_associate=is_marketing_associate)    
        db.session.add(new_user)
        db.session.commit()

    # Handle the form submission logic for adding a new user
    return redirect(url_for('admin_page'))

##################################################### Marketing Dashboard ####################################################

@app.route('/admin/marketing_dashboard_page', methods=['GET'])
def marketing_dashboard_page():
    try:
        # Fetch data from the "contact_details" and "india_state_organization" tables
        #MySQL Query
        data_results = ContactDetails.query.all()
        organization_results = IndiaStateOrganization.query.all()

        # Pass the 'offset' variable to the template
        offset = request.args.get('offset', 0, type=int)

        # Fetch the college data based on the offset
        college_result = IndiaStateOrganization.query.offset(offset).first()

        if college_result:
            current_college_data = {'college_id': college_result.college_id, 'college_name': college_result.college_name, 'city': college_result.city}
        else:
            current_college_data = None

        return render_template('marketing_dashboard.html', data_results=data_results, organization_results=organization_results, offset=offset, current_college_data=current_college_data)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "An error occurred. Please check the server logs for details.", 500


#################################################### Data Collector Page #######################################################
    
@app.route('/admin/data_collector_page', methods=['GET', 'POST'])
def data_collector_page():
    if request.form.get('action') == 'next':
        # Increment the offset by 1
        offset = int(request.args.get('offset', 0)) + 1
    else:
        offset = int(request.args.get('offset', 0))
        
    # Fetch the first row from the IndiaStateOrganization table
    #MySQL Query
    result = IndiaStateOrganization.query.offset(offset).first()
    print("fetched data: ", result)
    if result:
        current_college_data = {'college_name': result.college_name, 'city': result.city}
    else:
        current_college_data = {'college_name': 'No Data', 'city': 'No Data'}

    # Render HTML template with the data
    return render_template('collected_data.html', current_college_data=current_college_data, offset=offset, result=result)

# Go to data collector 
@app.route('/admin/go_to_data_collector_page')
def go_to_data_collector_page():
    return redirect(url_for('data_collector_page'))

############################################################ Submit Data #######################################################

@app.route('/admin/submit_data_collector', methods=['POST'])
def submit_data_collector():
    website_link = request.form['website_link']
    name = request.form['name']
    position = request.form['position']
    email = request.form['email']
    phone_number = request.form['phone_number']
    contact_id = request.form['contact_id']
    college_id = request.form['college_id']
    marketer_id = request.form['marketer_id']
    first_call = request.form['first_call']
    follow_up_call = request.form['follow_up_call']
    preferred_mode = request.form['preferred_mode']
    response = request.form['response']
    remarks = request.form['remarks']
    

    # Create a new Data instance and add it to the database
    new_data = ContactDetails(
        website_link=website_link,
        name=name,
        position=position,
        email=email,
        phone_number=phone_number,
        contact_id=contact_id,
        college_id=college_id,
        marketer_id=marketer_id,
        first_call=first_call,
        follow_up_call=follow_up_call,
        preferred_mode=preferred_mode,
        response=response,
        remarks=remarks
    )

    db.session.add(new_data)
    db.session.commit()

    return redirect(url_for('admin_page'))

if __name__ == '__main__':
    # Create 'uploads' folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Create tables before running the application
    with app.app_context():
        db.create_all()

    app.run(debug=True)

############################################################# END ##########################################################################



from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey

app = Flask(__name__)

############################################ Configure the database URI ######################################################
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/your_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

offset = 0

# Initialize the SQLAlchemy extension
db = SQLAlchemy(app)

class College(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

############################################## Define your models here ######################################################
# User model
class User(db.Model):
    marketer_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    is_marketing_associate = db.Column(db.Boolean, default=None)

# Contact_Details model
class ContactDetails(db.Model):
    contact_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    college_id = db.Column(db.Integer, ForeignKey('india_state_organization.college_id'), nullable=False)
    website_link = db.Column(db.String(100))
    name = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    marketer_id = db.Column(db.Integer, nullable=True)
    first_call = db.Column(db.Enum('yes', 'unanswered'), nullable=True)
    follow_up_call = db.Column(db.Enum('yes', 'unanswered'), nullable=True)
    preferred_mode = db.Column(db.Enum('phone', 'email'), nullable=True)
    response = db.Column(db.Enum('yes', 'maybe', 'no'), nullable=True)
    remarks = db.Column(db.Text)

#IndiaStateOrganization Model
class IndiaStateOrganization(db.Model):
    college_id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)    

########################################################### Main Page ###################################################################  
 
@app.route('/', methods=['GET'])
def home():
    print("Rendering home page")
    return render_template('main_page.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Perform authentication logic here (compare username and password with database)
    # For simplicity, I'm just checking if the username is 'admin' and password is 'admin'
    if username == 'admin' and password == 'admin':
        return redirect(url_for('admin_page'))
    else:
        return render_template('main_page.html', message='Invalid credentials. Please try again.')
    
############################################################# Admin Page ################################################################

@app.route('/admin')
def admin_page():
    return render_template('admin_page.html')

@app.route('/submit_admin', methods=['POST'])
def submit_admin():
    college_name = request.form['collegeName']
    csv_file = request.files['csvFile']

    # Save the CSV file to the 'uploads' folder with a unique filename
    if csv_file:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = os.path.join(app.config['UPLOAD_FOLDER'], f'{timestamp}_{csv_file.filename}')
        csv_file.save(filename)
    else:
        filename = None

    # Add the college to the database
    college = College(name=college_name)
    db.session.add(college)
    db.session.commit()

    # Redirect to admin page with a success message
    return render_template('admin_page.html', success_message='Data submitted successfully.')

###################################################### Add New User Page ##################################################

@app.route('/admin/add_new_user_page')
def add_new_user_page():
    return render_template('new_user.html')

@app.route('/admin/submit_new_user', methods=['POST'])
def submit_new_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_marketing_associate = request.form.get('is_marketing_associate') == 'on'
        
        new_user = User(username=username, password=password, is_marketing_associate=is_marketing_associate)    
        db.session.add(new_user)
        db.session.commit()

    # Handle the form submission logic for adding a new user
    return redirect(url_for('admin_page'))

##################################################### Marketing Dashboard ####################################################

@app.route('/admin/marketing_dashboard_page', methods=['GET'])
def marketing_dashboard_page():
    try:
        # Fetch data from the "contact_details" and "india_state_organization" tables
        #MySQL Query
        data_results = ContactDetails.query.all()
        organization_results = IndiaStateOrganization.query.all()

        # Pass the 'offset' variable to the template
        offset = request.args.get('offset', 0, type=int)

        # Fetch the college data based on the offset
        college_result = IndiaStateOrganization.query.offset(offset).first()

        if college_result:
            current_college_data = {'college_id': college_result.college_id, 'college_name': college_result.college_name, 'city': college_result.city}
        else:
            current_college_data = None

        # Fetch marketer_ids for the current college_id
        marketer_ids = [contact.marketer_id for contact in ContactDetails.query.filter_by(college_id=college_result.college_id).all()]

        return render_template('marketing_dashboard.html', data_results=data_results, organization_results=organization_results, offset=offset, current_college_data=current_college_data, marketer_ids=marketer_ids)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "An error occurred. Please check the server logs for details.", 500


#################################################### Data Collector Page #######################################################
    
@app.route('/admin/data_collector_page', methods=['GET', 'POST'])
def data_collector_page():
        # Check if the form is submitted
    if request.form.get('action') == 'next':
        # Increment the offset by 1
        offset = int(request.args.get('offset', 0)) + 1
    else:
        offset = int(request.args.get('offset', 0))
        
    # Fetch the first row from the IndiaStateOrganization table
    #MySQL Query
    result = IndiaStateOrganization.query.offset(offset).first()
    print("fetched data: ", result)
    if result:
        current_college_data = {'college_name': result.college_name, 'city': result.city}
    else:
        current_college_data = {'college_name': 'No Data', 'city': 'No Data'}

    # Render HTML template with the data
    return render_template('collected_data.html', current_college_data=current_college_data, offset=offset, result=result)

# Go to data collector 
@app.route('/admin/go_to_data_collector_page')
def go_to_data_collector_page():
    return redirect(url_for('data_collector_page'))

############################################################ Submit Data #######################################################

@app.route('/admin/submit_data_collector', methods=['POST'])
def submit_data_collector():

    website_link = request.form['website_link']
    name = request.form['name']
    position = request.form['position']
    email = request.form['email']
    phone_number = request.form['phone_number']
    contact_id = request.form['contact_id']
    college_id = request.form['college_id']
    marketer_id = request.form['marketer_id']
    first_call = request.form['first_call']
    follow_up_call = request.form['follow_up_call']
    preferred_mode = request.form['preferred_mode']
    response = request.form['response']
    remarks = request.form['remarks']
    

    # Create a new Data instance and add it to the database
    new_data = ContactDetails(
        website_link=website_link,
        name=name,
        position=position,
        email=email,
        phone_number=phone_number,
        contact_id=contact_id,
        college_id=college_id,
        marketer_id=marketer_id,
        first_call=first_call,
        follow_up_call=follow_up_call,
        preferred_mode=preferred_mode,
        response=response,
        remarks=remarks
    )

    db.session.add(new_data)
    db.session.commit()


    return redirect(url_for('admin_page'))

if __name__ == '__main__':
    # Create 'uploads' folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Create tables before running the application
    with app.app_context():
        db.create_all()

    app.run(debug=True)

############################################################# END ##########################################################################



