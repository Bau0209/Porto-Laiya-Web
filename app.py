from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from datetime import datetime

# Create a Flask application instance
app = Flask(__name__)
app.secret_key = '@Eddielynjoy123'  # This is used to secure the session

@app.route('/rentals_dashboard_home')
def rentals_dashboard_home():
    if 'username' not in session:
        return redirect(url_for('rentals_dashboard_login'))  # Redirect to login if not logged in
    
    username = session['username']  # Get the logged-in username
    
    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)
    
    # Fetch business name, description, price, and images for the logged-in user
    mycursor.execute("""
        SELECT 
            r.Business_Name,
            r.Description,
            r.Price,
            (SELECT COUNT(*) FROM transactions t 
             JOIN login_credentials l ON t.Property_Code = l.Property_Code
             WHERE t.Date_of_Checkin = CURRENT_DATE AND l.Username = %s) AS BookingForToday,
            (SELECT COUNT(*) FROM transactions t 
             JOIN login_credentials l ON t.Property_Code = l.Property_Code
             WHERE t.Date_of_Checkin >= CURRENT_DATE AND l.Username = %s) AS TotalUpcomingBookings,
            (SELECT COUNT(*) FROM transactions t 
             JOIN login_credentials l ON t.Property_Code = l.Property_Code
             WHERE t.Environmental_Fee_Status = 'Not Paid' AND l.Username = %s) AS UnpaidEnvironmentalFee,
            (SELECT GROUP_CONCAT(p.Image) FROM property_pictures p
             JOIN login_credentials l ON p.Property_Code = l.Property_Code
             WHERE l.Username = %s) AS Images
        FROM rentals r
        JOIN login_credentials l ON l.Property_Code = r.Property_Code
        WHERE l.Username = %s
    """, (username, username, username, username, username))

    result = mycursor.fetchone()
    mycursor.close()
    mydb.close()

    # If result exists, show the page, else show an error
    if result:
        # Split the images into a list
        images = result['Images'].split(',') if result['Images'] else []
        return render_template('rentals_dashboard/home.html',
                               business_name=result['Business_Name'],
                               description=result['Description'],
                               price_per_day=result['Price'],
                               bookings_for_today=result['BookingForToday'],
                               total_upcoming_bookings=result['TotalUpcomingBookings'],
                               unpaid_environmental_fee=result['UnpaidEnvironmentalFee'],
                               images=images)  # Pass images as a list
    else:
        return "Business name or data not found"

    

def get_transactions(username):
    """Fetch transaction data from MySQL based on logged-in user"""
    if not username:
        return []  # Return empty list if no username is found (not logged in)

    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)
    
    # Query to get transactions associated with the logged-in username
    mycursor.execute("""
        SELECT 
            t.Transaction_ID AS transaction_id,
            CONCAT(g.First_Name, ' ', g.Middle_Name, ' ', g.Last_Name) AS booker,
            t.Total_Num_of_Guests AS total_guests,
            t.Total_Num_of_Vehicles AS total_vehicles,
            t.Date_of_Checkin AS checkin_date,
            t.Date_of_Checkout AS checkout_date,
            t.Transaction_Status AS status,
            t.Environmental_Fee_Total AS environmental_fee_total,
            t.Environmental_Fee_Status AS environmental_fee_status
        FROM transactions t
        JOIN guestsinfo g ON t.Booker_ID = g.Guest_ID
        JOIN login_credentials l ON t.Property_Code = l.Property_Code
        WHERE l.Username = %s;
    """, (username,))

    transactions = mycursor.fetchall()
    mycursor.close()
    mydb.close()

    return transactions


def get_guests(username):
    """Fetch guest data from MySQL based on logged-in user"""
    if not username:
        return []  # Return empty list if no username is found (not logged in)

    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)
    
    # Query to get guests associated with the logged-in username
    mycursor.execute("""
        SELECT 
            t.Transaction_ID AS transaction_id,
            g.Guest_ID AS guest_id,
            CONCAT(g.First_Name, ' ', g.Middle_Name, ' ', g.Last_Name) AS full_name,
            tg.Is_Booker AS is_booker,
            g.Age AS age,
            g.Gender AS gender,
            g.Contact_Number AS contact_number, 
            g.Email AS email
        FROM guestsinfo g
        JOIN transaction_guest tg ON g.Guest_ID = tg.Guest_ID
        JOIN transactions t ON tg.Transaction_ID = t.Transaction_ID
        JOIN login_credentials l ON t.Property_Code = l.Property_Code
        WHERE l.Username = %s;
    """, (username,))

    guests = mycursor.fetchall()
    mycursor.close()
    mydb.close()

    return guests


@app.route('/')
def index():
    return "Index"

@app.route('/user_home')
def user_home():
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="@Eddielynjoy123",
            database="porto_laiya_database"
        )
        cursor = conn.cursor()

        # SQL query to fetch featured resorts and their images
        query = """
        SELECT r.Business_Name, MIN(p.Image) AS Image
        FROM rentals r
        JOIN property_pictures p ON r.Property_Code = p.Property_Code
        GROUP BY r.Business_Name
        LIMIT 6;
        """
        
        cursor.execute(query)
        resorts = cursor.fetchall()  # Returns [(Business_Name, Image), ...]

        # Close connection
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        resorts = []  # Return an empty list if there's an error

    # Pass data to the template
    return render_template('user/home.html', resorts=resorts)


@app.route('/user_resorts_and_rentals')
def user_resorts_and_rentals():
    # Get current page number, default is 1
    page = request.args.get('page', 1, type=int)
    items_per_page = 4  # Number of resorts per page
    offset = (page - 1) * items_per_page

    # Establish database connection
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    cursor = conn.cursor()

    # SQL query with pagination (LIMIT and OFFSET)
    query = f"""
    WITH RankedImages AS (
        SELECT r.Business_Name, r.Description, p.Image,
               ROW_NUMBER() OVER (PARTITION BY r.Business_Name ORDER BY p.Image) AS rn
        FROM rentals r
        JOIN property_pictures p ON p.Property_Code = r.Property_Code
    )
    SELECT Business_Name, Description, GROUP_CONCAT(Image ORDER BY rn) AS Images
    FROM RankedImages
    WHERE rn <= 4
    GROUP BY Business_Name, Description
    ORDER BY Business_Name;
    """
    cursor.execute(query)
    resorts = cursor.fetchall()

    # Fetch the total number of resorts for pagination
    count_query = """
    SELECT COUNT(DISTINCT r.Business_Name) 
    FROM rentals r;
    """
    cursor.execute(count_query)
    total_resorts = cursor.fetchone()[0]

    # Calculate total pages
    total_pages = (total_resorts // items_per_page) + (1 if total_resorts % items_per_page > 0 else 0)

    # Close database connection
    cursor.close()
    conn.close()

    # Pass data to the template
    return render_template(
        'user/resorts_and_rentals.html',
        resorts=resorts,
        total_pages=total_pages,
        current_page=page
    )

@app.route('/user_resorts_and_rentals_info')
def user_resorts_and_rentals_info():
    resort_name = request.args.get('resort_name', 'Unknown Resort')

    # Database connection
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    cursor = conn.cursor()

    # Fetch resort information
    cursor.execute("SELECT * FROM rentals WHERE Business_Name = %s", (resort_name,))
    resort_info = cursor.fetchone()

    if not resort_info:
        return "Resort not found", 404  

    # Fetch the property code for the selected resort
    property_code = resort_info[0]  # Assuming property_code is the first column

    # ✅ Store `resort_info` in session (so it updates when selecting a new resort)
    session['resort_info'] = resort_info

    # Fetch users who booked at this resort along with transaction_id
    cursor.execute("""
        SELECT CONCAT(g.First_Name, ' ', g.Middle_Name, ' ', g.Last_Name) AS Full_Name, t.Transaction_ID
        FROM transactions t
        JOIN guestsinfo g ON t.Booker_ID = g.Guest_ID
        JOIN rentals rt ON rt.Property_Code = t.Property_Code
        WHERE rt.Business_Name = %s
    """, (resort_name,))
    users = cursor.fetchall()  # users now contains (Full_Name, Transaction_ID)


    # Fetch images
    cursor.execute("""
        SELECT Image FROM property_pictures p
        JOIN rentals r ON r.Property_Code = p.Property_Code
        WHERE Business_Name = %s
    """, (resort_name,))
    images = [row[0] for row in cursor.fetchall()]

    # Fetch reviews
    cursor.execute("""
        SELECT CONCAT(g.First_Name, ' ', g.Middle_Name, ' ', g.Last_Name) AS Full_Name, 
               r.Stars, r.Review_text
        FROM reviews r
        JOIN transactions t ON r.Transaction_ID = t.Transaction_ID
        JOIN guestsinfo g ON t.Booker_ID = g.Guest_ID
        JOIN rentals rt ON rt.Property_Code = t.Property_Code
        WHERE rt.Business_Name = %s
    """, (resort_name,))
    reviews = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'user/resorts_and_rentals_info.html',
        resort_name=resort_name,
        property_code=property_code,
        resort_info=resort_info,
        images=images,
        reviews=reviews,
        users=users
    )



@app.route('/submit_review', methods=['POST'])
def submit_review():
    transaction_id = request.form.get('transaction_id')
    review_text = request.form.get('review_text')
    stars = request.form.get('stars')
    resort_name = request.form.get('resort_name')  # Get resort name from form

    print(f"Transaction ID: {transaction_id}, Review: {review_text}, Stars: {stars}, Resort: {resort_name}")  # Debugging

    if not resort_name:
        flash("Error: Resort name is missing!", "error")
        return redirect(url_for('user_resorts_and_rentals_info'))  # Redirect with a default

    # Database connection
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    cursor = conn.cursor()

    query = """INSERT INTO reviews (Transaction_ID, Review_text, Stars) VALUES (%s, %s, %s)"""
    cursor.execute(query, (transaction_id, review_text, stars))
    conn.commit()

    cursor.close()
    conn.close()

    # ✅ Corrected Redirect (query parameter format)
    return redirect(url_for('user_resorts_and_rentals_info', resort_name=resort_name))




@app.route('/user_portal_user_booking')
def user_portal_user_booking():
    resort_info = session.get('resort_info', None)  # User portal session

    if not resort_info:
        return "Resort Info Not Found", 400  

    resort_name = resort_info[1]  # Resort name
    price = resort_info[7]        # Price

    return render_template('user/user_booking.html', resort_info=resort_info, resort_name=resort_name, price=price)


@app.route('/submit-booking', methods=['POST'])
def submit_booking():
    # Database connection
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )

    try:
        cursor = conn.cursor()

        # **1. Retrieve Booker Information**
        first_name = request.form['bookerFirstName']
        middle_name = request.form.get('bookerMiddleName', '')  # Optional
        last_name = request.form['bookerLastName']
        gender = request.form['bookerGender']
        age = int(request.form['bookerAge'])
        contact = request.form['bookerContact']
        email = request.form['bookerEmail']
        vehicles = int(request.form['bookerVehicles'])
        resort_name = request.form['resort_name']

        # **2. Fetch Property_Code for Resort**
        cursor.execute("SELECT Property_Code, Price FROM rentals WHERE Business_Name = %s", (resort_name,))
        property_details = cursor.fetchone()

        if not property_details:
            flash("Resort not found!", "error")
            return redirect(url_for('user_booking'))

        property_code = property_details[0]  # Extract Property_Code
        price_per_day = property_details[1]  # Extract Price per day

        # **3. Insert Booker into `guestsinfo` Table**
        cursor.execute("""
            INSERT INTO guestsinfo (First_Name, Middle_Name, Last_Name, Gender, Age, Contact_Number, Email)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (first_name, middle_name, last_name, gender, age, contact, email))

        # Retrieve the last inserted booker_id using LAST_INSERT_ID()
        cursor.execute("SELECT LAST_INSERT_ID()")
        booker_id = cursor.fetchone()[0]

        # **4. Insert into `transactions` table**
        check_in = request.form['checkIn']
        check_out = request.form['checkOut']

        # Ensure the dates use the correct format (YYYY-MM-DD)
        check_in = datetime.strptime(check_in, "%Y-%m-%d").strftime("%Y-%m-%d")
        check_out = datetime.strptime(check_out, "%Y-%m-%d").strftime("%Y-%m-%d")

        # **5. Calculate the Total Price (number of nights * price per day)**
        # Calculate the number of days between check_in and check_out
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        nights = (check_out_date - check_in_date).days

        if nights < 1:
            nights = 1  # Ensure at least 1 day if no valid date range

        # **Environmental Fee** per guest
        environmental_fee_per_guest = 20
        guest_count = 1  # Start at 1 for the booker
        while f'guestFirstName_{guest_count}' in request.form:
            guest_count += 1  # Count filled guest forms
        environmental_fee = environmental_fee_per_guest * guest_count

        # Calculate total price including environmental fee
        total_price = (nights * price_per_day) + environmental_fee

        # **6. Count guests dynamically (including booker)**
        guest_count = 1  # Start at 1 for the booker
        while f'guestFirstName_{guest_count}' in request.form:
            guest_count += 1  # Count filled guest forms
        guests = guest_count  # Total guests including booker

        # Insert transaction into `transactions` table
        cursor.execute("""
            INSERT INTO transactions (
                Booker_ID, Property_Code, Total_Num_of_Guests, Total_Num_of_Vehicles, 
                Date_of_Checkin, Date_of_Checkout, Total_Price
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (booker_id, property_code, guests, vehicles, check_in, check_out, total_price))

        # **Retrieve the `transaction_id` from the database**
        cursor.execute("SELECT LAST_INSERT_ID()")
        transaction_id = cursor.fetchone()[0]

        # **7. Insert Guest Details (if any)**
        guest_data = []
        guest_references = []

        guest_count = 1  # Start from the first guest
        while f'guestFirstName_{guest_count}' in request.form:
            guest_first = request.form.get(f'guestFirstName_{guest_count}')
            guest_middle = request.form.get(f'guestMiddleName_{guest_count}', '')  # Optional
            guest_last = request.form.get(f'guestLastName_{guest_count}')
            guest_gender = request.form.get(f'guestGender_{guest_count}')
            guest_age = int(request.form.get(f'guestAge_{guest_count}', 0))
            guest_contact = request.form.get(f'guestContact_{guest_count}')
            guest_email = request.form.get(f'guestEmail_{guest_count}')

            # Skip empty guest forms
            if guest_first.strip() and guest_last.strip() and guest_contact.strip() and guest_email.strip():
                guest_data.append((guest_first, guest_middle, guest_last, guest_gender, guest_age, guest_contact, guest_email))
                guest_count += 1  # Move to the next guest

        # Insert guests into `guestsinfo` table and associate them with the transaction
        guest_ids = []
        if guest_data:
            cursor.executemany("""
                INSERT INTO guestsinfo (First_Name, Middle_Name, Last_Name, Gender, Age, Contact_Number, Email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, guest_data)

            # Retrieve the last inserted guest ID (first guest)
            cursor.execute("SELECT LAST_INSERT_ID()")
            first_guest_id = cursor.fetchone()[0]

            # Generate guest IDs sequentially
            guest_ids = [first_guest_id + i for i in range(len(guest_data))]

            # Prepare guest references for `transaction_guest`
            for guest_id in guest_ids:
                guest_references.append((transaction_id, guest_id, "no"))  # "no" for non-bookers

        # Insert the booker into `transaction_guest`
        guest_references.append((transaction_id, booker_id, "yes"))  # "yes" for booker

        # Insert all guests and booker into `transaction_guest` table
        cursor.executemany("""
            INSERT INTO transaction_guest (Transaction_ID, Guest_ID, Is_Booker)
            VALUES (%s, %s, %s)
        """, guest_references)

        # **8. Commit changes and close connection**
        conn.commit()
        # After successful booking:
        flash("Booking Successful!", "success")
        return redirect(request.referrer)  # Redirect back to the previous page

    except Exception as e:
        # Rollback the transaction in case of an error
        conn.rollback()
        flash(f"Error: {str(e)}", "error")
        return redirect(request.referrer)  # Redirect back to the previous page

    finally:
        cursor.close()
        conn.close()




@app.route('/user_about_us')
def user_about_us():
    return render_template('user/about_us.html')

@app.route('/rentals_dashboard_login', methods=['GET', 'POST'])
def rentals_dashboard_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Validate username and password
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="@Eddielynjoy123",
            database="porto_laiya_database"
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT l.Username, r.Business_Name, l.Property_Code
            FROM login_credentials l
            JOIN rentals r ON l.Property_Code = r.Property_Code
            WHERE l.Username = %s AND l.Password = %s
        """, (username, password))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['username'] = user['Username']
            session['business_name'] = user['Business_Name']
            session['property_code'] = user['Property_Code']  # ✅ Store the correct property_code for rentals_dashboard

            return redirect(url_for('rentals_dashboard_home'))
        else:
            return "Invalid credentials, please try again."

    return render_template('rentals_dashboard/login.html')

@app.route('/rentals_dashboard_user_booking')
def rentals_dashboard_user_booking():
    property_code = session.get('property_code', None)  # Rentals dashboard session

    if not property_code:
        return "Property Code Not Found", 400  

    # Database Connection
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    cursor = conn.cursor()

    # Fetch resort info using property_code
    cursor.execute("SELECT * FROM rentals WHERE Property_Code = %s", (property_code,))
    resort_info = cursor.fetchone()

    cursor.close()
    conn.close()

    if resort_info:
        resort_name = resort_info[1]  # Assuming the 3rd column is Business_Name
        price = resort_info[7]        # Assuming the 9th column is the price
    else:
        resort_name = 'Unknown Resort'
        price = 'N/A'

    return render_template('rentals_dashboard/pop_up_add_transactions.html', resort_info=resort_info, resort_name=resort_name, price=price)


@app.route('/rentals_dashboard_bookings')
def rentals_dashboard_bookings():
    if 'username' not in session:
        return redirect(url_for('rentals_dashboard_login'))  # Redirect to login if not logged in
    
    username = session['username']
    business_name = session.get('business_name')  # Get business name from session

    if not business_name:
        return "Business name not found"
    
    # Fetch transactions for the logged-in user
    transactions = get_transactions(username)

    return render_template('rentals_dashboard/bookings.html', 
                           transactions=transactions, 
                           business_name=business_name)

@app.route('/update_transaction/<transaction_id>', methods=['POST'])
def update_transaction(transaction_id):
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 403

    username = session['username']

    # Get form data
    first_name = request.form['first_name']
    middle_name = request.form['middle_name']
    last_name = request.form['last_name']
    contact = request.form['contact']
    guests = request.form['guests']
    vehicles = request.form['vehicles']
    total_price = request.form['total_price']
    transaction_status = request.form['transaction_status']
    checkin_date = request.form['checkin_date']
    checkout_date = request.form['checkout_date']
    environmental_status = request.form['environmental_status']

    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor()

    try:
        # Update transaction details
        mycursor.execute("""
            UPDATE transactions
            SET 
                Total_Num_of_Guests = %s, 
                Total_Num_of_Vehicles = %s, 
                Total_Price = %s, 
                Transaction_Status = %s, 
                Date_of_Checkin = %s, 
                Date_of_Checkout = %s,  
                Environmental_Fee_Status = %s
            WHERE Transaction_ID = %s 
            AND Property_Code = (SELECT Property_Code FROM login_credentials WHERE Username = %s)
        """, (
            guests, vehicles, total_price, transaction_status, checkin_date, checkout_date, 
            environmental_status, transaction_id, username
        ))

        # Update the guest info
        mycursor.execute("""
            UPDATE guestsinfo
            SET 
                First_Name = %s, 
                Middle_Name = %s, 
                Last_Name = %s, 
                Contact_Number = %s
            WHERE Guest_ID = (SELECT Booker_ID FROM transactions WHERE Transaction_ID = %s)
        """, (first_name, middle_name, last_name, contact, transaction_id))

        mydb.commit()
        return jsonify({"status": "success", "message": "Transaction updated successfully!"})

    except Exception as e:
        mydb.rollback()
        return jsonify({"status": "error", "message": f"Error updating transaction: {str(e)}"})

    finally:
        mycursor.close()
        mydb.close()

@app.route('/popup/rentals_dashboard/transaction/<transaction_id>/<mode>')
def pop_up_transaction(transaction_id, mode):
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('rentals_dashboard_login'))  

    username = session['username']  

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch the transaction data
    mycursor.execute("""
        SELECT 
            t.Transaction_ID,
            g.First_Name,
            g.Middle_Name,
            g.Last_Name,
            t.Property_Code,
            g.Contact_Number,
            t.Total_Num_of_Guests,
            t.Total_Num_of_Vehicles,
            t.Date_of_Checkin,
            t.Date_of_Checkout,
            t.Total_Price,
            t.Transaction_Status,
            t.Environmental_Fee_Total,
            t.Environmental_Fee_Status
        FROM transactions t
        JOIN guestsinfo g ON t.Booker_ID = g.Guest_ID
        WHERE t.Transaction_ID = %s
    """, (transaction_id,))

    transaction = mycursor.fetchone()  
    mycursor.close()
    mydb.close()

    if not transaction:
        return "Transaction not found", 404  

    # Determine which template to use based on mode (view or edit)
    if mode == 'view':
        return render_template('rentals_dashboard/pop_up_view_transactions.html', transaction=transaction)
    elif mode == 'edit':
        return render_template('rentals_dashboard/pop_up_edit_transactions.html', transaction=transaction)
    else:
        return "Invalid mode", 400  # Handle incorrect mode values


@app.route('/popup/rentals_dashboard/add_transaction')
def pop_up_add_transactions():
    return render_template('rentals_dashboard/pop_up_add_transactions.html')


@app.route('/popup/pop_up_pay_fees_transactions', methods=['GET', 'POST'])
def pop_up_pay_fees_transactions():
    # Assuming the 'resort_property_code' is stored in session
    if 'property_code' not in session:
        return "Resort information is missing in the session.", 400  # Handle missing resort info in session

    property_code = session['property_code']  # Get the Property_Code from the session

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch transaction data based on `Property_Code` from session
    mycursor.execute("""
        SELECT 
            t.Transaction_ID,
            CONCAT(g.First_Name, ' ', g.Middle_Name, ' ', g.Last_Name) AS Booker,
            t.Total_Num_of_Guests,
            t.Environmental_Fee_Total,
            t.Environmental_Fee_Status
        FROM transactions t
        JOIN guestsinfo g ON t.Booker_ID = g.Guest_ID
        WHERE t.Environmental_Fee_Status = 'Not Paid'
        AND t.Property_Code = %s
    """, (property_code,))  # Pass the property code from session

    transactions = mycursor.fetchall()
    mycursor.close()
    mydb.close()

    return render_template('rentals_dashboard/pop_up_pay_fees_transactions.html', transactions=transactions)

@app.route('/pay_fees', methods=['POST'])
def pay_fees():
    if request.method == 'POST':
        # Get the selected transaction IDs from the form
        transaction_ids = request.form.getlist('transaction_ids')
        
        if not transaction_ids:
            flash("No transactions selected.", "warning")
            return redirect(request.referrer)  # Go back to the previous page

        # Connect to the database
        mydb = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="@Eddielynjoy123",
            database="porto_laiya_database"
        )
        mycursor = mydb.cursor()

        # Update the 'Environmental_Fee_Status' for the selected transactions
        for transaction_id in transaction_ids:
            mycursor.execute("""
                UPDATE transactions
                SET Environmental_Fee_Status = 'Paid'
                WHERE Transaction_ID = %s
            """, (transaction_id,))
        
        # Commit the changes
        mydb.commit()
        mycursor.close()
        mydb.close()

        flash(f'{len(transaction_ids)} transaction(s) marked as Paid.', 'success')

        return redirect(request.referrer)  # Go back to the previous page




@app.route('/rentals_dashboard_guests')
def rentals_dashboard_guests():
    if 'username' not in session:
        return redirect(url_for('rentals_dashboard_login'))  # Redirect to login if not logged in
    
    username = session['username']
    business_name = session.get('business_name')  # Get business name from session

    if not business_name:
        return "Business name not found"
    
    # Fetch guests for the logged-in user
    guests = get_guests(username)

    return render_template('rentals_dashboard/guests.html', 
                           guests=guests, 
                           business_name=business_name)

@app.route('/update_guest/<guest_id>', methods=['POST'])
def update_guest(guest_id):
    # Ensure the user is logged in
    if 'username' not in session:
        flash("Not logged in", "error")
        return "Not logged in", 400  # Show an error message if the user is not logged in

    username = session['username']

    # Get form data
    first_name = request.form['first_name']
    middle_name = request.form['middle_name']
    last_name = request.form['last_name']
    contact = request.form['contact_number']
    email = request.form['email']
    gender = request.form['gender']
    age = request.form['age']

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    try:
        # Update guest info
        mycursor.execute("""
            UPDATE guestsinfo
            SET 
                First_Name = %s, 
                Middle_Name = %s, 
                Last_Name = %s, 
                Contact_Number = %s, 
                Email = %s, 
                Gender = %s, 
                Age = %s
            WHERE Guest_ID = %s
        """, (first_name, middle_name, last_name, contact, email, gender, age, guest_id))

        mydb.commit()

        # Fetch the updated guest details to pass to the template
        mycursor.execute("""
            SELECT 
                First_Name, Middle_Name, Last_Name, Contact_Number, Email, Gender, Age
            FROM guestsinfo
            WHERE Guest_ID = %s
        """, (guest_id,))

        guest = mycursor.fetchone()

        # Flash a success message
        flash("Guest updated successfully!", "success")

        # Render the template with the updated guest data
        return render_template('rentals_dashboard/pop_up_edit_guests.html', guest=guest)

    except Exception as e:
        mydb.rollback()
        flash(f"Error updating guest: {str(e)}", "error")
        
        # In case of an error, render the page again with the error message
        return render_template('rentals_dashboard/pop_up_edit_guests.html')

    finally:
        mycursor.close()
        mydb.close()




@app.route('/popup/rentals_dashboard/add_guests')
def pop_up_add_guests():
    if 'property_code' not in session:
        return "Resort information is missing in the session.", 400  # Handle missing property code in session

    property_code = session['property_code']  # Get the property code from the session

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch transactions related to the logged-in resort
    mycursor.execute("""
        SELECT 
            t.Transaction_ID, 
            r.Price,
            t.Total_Price,
            t.Date_of_Checkin,
            t.Date_of_Checkout,
            t.Environmental_Fee_Total
        FROM transactions t 
        JOIN rentals r ON r.Property_Code = t.Property_Code
        WHERE t.Property_Code = %s
    """, (property_code,))

    transactions = mycursor.fetchall()  # Get all transactions
    mycursor.close()
    mydb.close()

    return render_template('rentals_dashboard/pop_up_add_guests.html', transactions=transactions)


@app.route('/rentals_dashboard_feedbacks')
def rentals_dashboard_feedbacks():
    if 'username' not in session:
        return redirect(url_for('rentals_dashboard_login'))  # Redirect to login if not logged in
    
    username = session['username']
    business_name = session.get('business_name')  # Get business name from session

    if not business_name:
        return "Business name not found"

    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch reviews including star ratings
    mycursor.execute("""
        SELECT 
            CONCAT(g.First_Name, ' ', g.Middle_Name, ' ', g.Last_Name) AS full_name, 
            r.Stars,
            r.Review_text
        FROM reviews r
        JOIN transactions t ON r.Transaction_ID = t.Transaction_ID
        JOIN guestsinfo g ON t.Booker_ID = g.Guest_ID
        JOIN login_credentials l ON t.Property_Code = l.Property_Code
        WHERE l.Username = %s
    """, (username,))

    reviews = mycursor.fetchall()
    
    mycursor.close()
    mydb.close()

    return render_template('rentals_dashboard/feedbacks.html', 
                           reviews=reviews, 
                           business_name=business_name)

@app.route('/popup/rentals_dashboard/guest/<int:guest_id>/<mode>', methods=['GET', 'POST'])
def pop_up_guest(guest_id, mode):
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('rentals_dashboard_login'))  # Redirect to login if session doesn't have username

    username = session['username']
    print("Session username:", username)  # Debugging session data

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch guest data
    mycursor.execute("""
        SELECT  
            t.Transaction_ID,
            g.Guest_ID,
            g.First_Name,
            g.Middle_Name,
            g.Last_Name,
            g.Contact_Number,
            g.Email,            
            g.Age,
            g.Gender,
            tg.Is_Booker,
            t.Transaction_ID,
            t.Date_of_Checkin,
            t.Date_of_Checkout
        FROM guestsinfo g
        LEFT JOIN transaction_guest tg ON g.Guest_ID = tg.Guest_ID
        LEFT JOIN transactions t ON t.Transaction_ID = tg.Transaction_ID
        WHERE g.Guest_ID = %s
    """, (guest_id,))

    guest = mycursor.fetchone()

    if not guest:
        return "Guest not found", 404

    # Check mode and process accordingly
    if mode == 'view':
        return render_template('rentals_dashboard/pop_up_view_guests.html', guest=guest)

    elif mode == 'edit':
        if request.method == 'POST':
            # Handle form submission to update guest details
            updated_first_name = request.form['first_name']
            updated_last_name = request.form['last_name']
            updated_contact = request.form['contact']
            updated_email = request.form['email']

            # Update guest details in the database
            mycursor.execute("""
                UPDATE guestsinfo 
                SET First_Name = %s, Last_Name = %s, Contact_Number = %s, Email = %s
                WHERE Guest_ID = %s
            """, (updated_first_name, updated_last_name, updated_contact, updated_email, guest_id))

            mydb.commit()

            # Flash a success message and ensure session isn't cleared
            flash('Guest details successfully updated!', 'success')

            # Ensure session isn't cleared, and redirect to the correct page
            return redirect(url_for('rentals_dashboard_guest_list'))  # Adjust the redirect as needed

        return render_template('rentals_dashboard/pop_up_edit_guests.html', guest=guest)

    else:
        return "Invalid mode", 400  # Handle incorrect mode values







# Admin Dashboard
from functools import wraps
from flask_login import login_required

# Dummy user for demonstration
users = {'admin@gmail.com': 'pass'}  # Replace with your user authentication logic

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_dashboard_login'))  # Redirect to login if not logged in
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin_dashboard_login', methods=['GET', 'POST'])
def admin_dashboard_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users and users[email] == password:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard_home'))
        else:
            flash('Invalid credentials, please try again.')
    return render_template('admin_dashboard/login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Remove the logged_in key from the session
    return redirect(url_for('admin_dashboard_login'))

@app.route('/admin_dashboard_home')
@login_required
def admin_dashboard_home():
    # Connect to the database
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )

    cursor = conn.cursor(dictionary=True)
    
    try:
        # Query 1: Guests for Today
        cursor.execute("""
            SELECT COUNT(*) AS BookingForToday
            FROM transactions t
            WHERE Date_of_Checkin = CURRENT_DATE;
        """)
        booking_for_today = cursor.fetchone()['BookingForToday']
        
        # Query 2: Total Upcoming Bookings of all Rentals
        cursor.execute("""
            SELECT COUNT(*) AS TotalUpcomingBookings
            FROM transactions t
            WHERE Date_of_Checkin >= CURRENT_DATE;
        """)
        total_upcoming_bookings = cursor.fetchone()['TotalUpcomingBookings']
        
        # Query 3: Unpaid Environmental Fee of all Rentals
        cursor.execute("""
            SELECT COUNT(*) AS UnpaidEnvironmentalFee
            FROM transactions t
            WHERE t.Environmental_Fee_Status = 'Not Paid';
        """)
        unpaid_environmental_fee = cursor.fetchone()['UnpaidEnvironmentalFee']
        
        # Query 4: Number of Transactions per Rental and Resort
        cursor.execute("""
            SELECT r.Business_Name, COUNT(*) AS NumberOfTransactions
            FROM transactions t
            JOIN rentals r ON r.Property_Code = t.Property_Code
            GROUP BY Business_Name;
        """)
        transactions_per_resort = cursor.fetchall()
        
        # Query 5: Overall Number of Guests per Month
        cursor.execute("""
            SELECT 
                EXTRACT(YEAR FROM t.Date_of_Checkin) AS Year,
                EXTRACT(MONTH FROM t.Date_of_CheckIn) AS Month,
                COUNT(DISTINCT tg.Guest_ID) AS NumberOfGuests
            FROM transactions t
            JOIN transaction_guest tg ON tg.Transaction_ID = t.Transaction_ID
            WHERE EXTRACT(YEAR FROM t.Date_of_Checkin) = 2025
            GROUP BY Year, Month
            ORDER BY Year, Month;
        """)
        guests_per_month = cursor.fetchall()
        
        # Close the connection
        conn.close()

        # Pass the data to the template
        return render_template('admin_dashboard/home.html', 
                               booking_for_today=booking_for_today,
                               total_upcoming_bookings=total_upcoming_bookings,
                               unpaid_environmental_fee=unpaid_environmental_fee,
                               transactions_per_resort=transactions_per_resort,
                               guests_per_month=guests_per_month)

    except Exception as e:
        conn.close()
        return str(e)




@app.route('/admin_dashboard_guests')
@login_required
def admin_dashboard_guests():
    # Connect to the database
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )

    cursor = conn.cursor(dictionary=True)

    try:
        # Execute the query to fetch the latest guest details
        cursor.execute("""
            WITH RankedGuests AS (
                SELECT 
                    g.Guest_ID, 
                    t.Property_Code,
                    t.Transaction_ID, 
                    CONCAT(g.First_Name, ' ', g.Middle_Name, ' ', g.Last_Name) AS Full_Name,
                    tg.Is_Booker,
                    g.Age, 
                    g.Gender,
                    g.Contact_Number, 
                    g.Email, 
                    t.Date_of_Checkin, 
                    t.Date_of_Checkout,
                    ROW_NUMBER() OVER (PARTITION BY g.Guest_ID ORDER BY t.Date_of_Checkin DESC) AS rn
                FROM guestsinfo g
                JOIN transaction_guest tg ON g.Guest_ID = tg.Guest_ID
                JOIN transactions t ON tg.Transaction_ID = t.Transaction_ID
            )
            SELECT Guest_ID, Property_Code, Transaction_ID, Full_Name, Is_Booker, Age, Gender, Contact_Number, Email, Date_of_Checkin, Date_of_Checkout
            FROM RankedGuests
            WHERE rn = 1;  -- Only keeps one row per guest
        """)

        # Fetch the results
        guests = cursor.fetchall()

        # Close the connection
        conn.close()

        # Pass the data to the template
        return render_template('admin_dashboard/guests.html', guests=guests)

    except Exception as e:
        conn.close()
        return str(e)



@app.route('/delete_guest/<int:guest_id>', methods=['DELETE'])
@login_required
def delete_guest(guest_id):
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 403

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor()

    try:
        # Step 1: Delete from transaction_guest where Guest_ID = guest_id
        mycursor.execute("""
            DELETE FROM transaction_guest WHERE Guest_ID = %s
        """, (guest_id,))

        # Step 2: Check if guest is a Booker in transactions
        mycursor.execute("""
            SELECT Transaction_ID FROM transactions WHERE Booker_ID = %s
        """, (guest_id,))
        transaction_ids = mycursor.fetchall()

        if transaction_ids:
            transaction_ids = [tid[0] for tid in transaction_ids]  # Extract transaction IDs

            # Delete related records from transaction_guest for those transactions
            mycursor.executemany("""
                DELETE FROM transaction_guest WHERE Transaction_ID = %s
            """, [(tid,) for tid in transaction_ids])

            # Delete transactions where the guest is the booker
            mycursor.executemany("""
                DELETE FROM transactions WHERE Transaction_ID = %s
            """, [(tid,) for tid in transaction_ids])

        # Step 3: Delete the guest from guestsinfo
        mycursor.execute("""
            DELETE FROM guestsinfo WHERE Guest_ID = %s
        """, (guest_id,))

        mydb.commit()

        return jsonify({"status": "success", "message": "Guest and related records deleted successfully!"})

    except Exception as e:
        mydb.rollback()
        return jsonify({"status": "error", "message": f"Error deleting guest: {str(e)}"})

    finally:
        mycursor.close()
        mydb.close()




@app.route('/popup/admin_dashboard/add_guests')
def admin_pop_up_add_guests():
    return render_template('admin_dashboard/pop_up_add_guests.html')



@app.route('/admin_dashboard_properties')
@login_required
def admin_dashboard_properties():
    if 'username' not in session:
        return redirect(url_for('admin_dashboard_login'))

    # Connect to database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch properties data
    mycursor.execute("""
        SELECT 
            *
        FROM rentals
    """)
    properties = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    # Pass data to the template
    return render_template('admin_dashboard/properties.html', properties=properties)


@app.route('/popup/admin_dashboard/properties/<int:property_id>/<mode>', methods=['GET', 'POST'])
@login_required
def admin_pop_up_properties(property_id, mode):
    if 'username' not in session:
        return redirect(url_for('admin_dashboard_login'))

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch property details
    mycursor.execute("""
        SELECT 
            *
        FROM rentals
        WHERE Property_Code = %s
    """, (property_id,))

    property_details = mycursor.fetchone()

    if not property_details:
        mycursor.close()
        mydb.close()
        return "Property not found", 404

    if mode == 'edit' and request.method == 'POST':
        # Get form data
        updated_business_name = request.form['business_name']
        updated_owner_name = request.form['owner_name']
        updated_has_pool = request.form['pool']
        updated_allows_pets = request.form['pets']
        updated_has_wifi = request.form['wifi']
        updated_price = request.form['price']
        updated_description = request.form['description']

        # Update property details in the database
        mycursor.execute("""
            UPDATE rentals 
            SET 
                Business_Name = %s,
                Owner_Name = %s,
                Pool = %s,
                Pets_Allowed = %s,
                Wifi = %s,
                Price = %s,
                Description = %s
            WHERE Property_Code = %s
        """, (
            updated_business_name, updated_owner_name, 
            updated_has_pool, updated_allows_pets, updated_has_wifi, updated_price, updated_description, property_id
        ))

        mydb.commit()
        flash('Property details successfully updated!', 'success')
        return redirect(url_for('admin_dashboard_properties'))

    mycursor.close()
    mydb.close()

    # Render the appropriate template based on mode
    if mode == 'view':
        return render_template('admin_dashboard/pop_up_view_properties.html', property=property_details)
    elif mode == 'edit':
        return render_template('admin_dashboard/pop_up_edit_properties.html', property=property_details)
    else:
        return "Invalid mode", 400


@app.route('/popup/admin_dashboard/add_properties', methods=['GET', 'POST'])
def admin_pop_up_add_properties():
    if request.method == 'POST':
        # Get the form data
        business_name = request.form['business_name']
        owner_name = request.form['owner_name']
        pool = 1 if request.form['pool'] == 'yes' else 0
        pets = 1 if request.form['pets'] == 'yes' else 0
        wifi = 1 if request.form['wifi'] == 'yes' else 0
        price = request.form['price']
        image_1 = request.form['image_1']
        image_2 = request.form['image_2']
        image_3 = request.form['image_3']
        description = request.form['description']

        # Add the new property to the database
        mydb = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="@Eddielynjoy123",
            database="porto_laiya_database"
        )
        mycursor = mydb.cursor()

        # Insert property details into the database
        mycursor.execute("""
            INSERT INTO rentals (Business_Name, Owner_Name, Pool, Pets_Allowed, Wifi, Price, Description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (business_name, owner_name, pool, pets, wifi, price, description))

        # Get the Property_Code of the newly inserted property
        property_code = mycursor.lastrowid

        # Insert images into the property_pictures table
        if image_1:
            mycursor.execute("""
                INSERT INTO property_pictures (Property_Code, Image)
                VALUES (%s, %s)
            """, (property_code, image_1))

        if image_2:
            mycursor.execute("""
                INSERT INTO property_pictures (Property_Code, Image)
                VALUES (%s, %s)
            """, (property_code, image_2))

        if image_3:
            mycursor.execute("""
                INSERT INTO property_pictures (Property_Code, Image)
                VALUES (%s, %s)
            """, (property_code, image_3))

        # Commit the changes
        mydb.commit()

        flash('Property added successfully!', 'success')
        return redirect(url_for('admin_dashboard_properties'))

    return render_template('admin_dashboard/pop_up_add_properties.html')









@app.route('/admin_dashboard_transactions')
@login_required
def admin_dashboard_transactions():
    if 'username' not in session:
        return redirect(url_for('admin_dashboard_login'))

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch transactions data
    mycursor.execute("""
        SELECT 
            t.Transaction_ID,
            t.Property_Code,
            CONCAT(g.First_Name, ' ', g.Middle_Name, ' ', g.Last_Name) AS Booker,
            t.Total_Num_of_Guests,
            t.Total_Num_of_Vehicles,
            t.Date_of_Checkin,
            t.Date_of_Checkout,
            t.Total_Price,
            t.Transaction_Status AS Status,
            t.Environmental_Fee_Total,
            t.Environmental_Fee_Status
        FROM transactions t
        JOIN guestsinfo g ON t.Booker_ID = g.Guest_ID
    """)
    transactions = mycursor.fetchall()

    mycursor.close()
    mydb.close()

    # Pass data to the template
    return render_template('admin_dashboard/transactions.html', transactions=transactions)


@app.route('/delete_transaction/<transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Not logged in"}), 403

    # Connect to database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor()

    try:
        # Step 1: Get all Guest_IDs related to this transaction
        mycursor.execute("""
            SELECT g.Guest_ID FROM transaction_guest tg
            JOIN guestsinfo g ON tg.Guest_ID = g.Guest_ID
            WHERE tg.Transaction_ID = %s
        """, (transaction_id,))
        guest_ids = mycursor.fetchall()

        if not guest_ids:
            return jsonify({"status": "error", "message": "Transaction not found!"}), 404

        # Step 2: Delete all related entries in the transaction_guest table
        mycursor.execute("""
            DELETE FROM transaction_guest WHERE Transaction_ID = %s
        """, (transaction_id,))

        # Step 3: Delete the transaction itself from the transactions table
        mycursor.execute("""
            DELETE FROM transactions WHERE Transaction_ID = %s
        """, (transaction_id,))

        # Step 4: For each guest, check if they are the booker and delete their guest info if necessary
        for guest_id in guest_ids:
            guest_id = guest_id[0]  # Extract the Guest_ID from the tuple

            # Check if this guest is the booker and if they have no other associated transactions
            mycursor.execute("""
                SELECT COUNT(*) FROM transactions WHERE Booker_ID = %s
            """, (guest_id,))
            transaction_count = mycursor.fetchone()[0]

            # If the guest has no other associated transactions, delete their guest info
            if transaction_count == 0:
                mycursor.execute("""
                    DELETE FROM guestsinfo WHERE Guest_ID = %s
                """, (guest_id,))

        # Commit the transaction
        mydb.commit()
        return jsonify({"status": "success", "message": "Transaction and corresponding guest info deleted successfully!"})

    except Exception as e:
        mydb.rollback()
        return jsonify({"status": "error", "message": f"Error deleting transaction and guest info: {str(e)}"})

    finally:
        mycursor.close()
        mydb.close()




@app.route('/popup/admin_dashboard/transactions/<int:transaction_id>/<mode>', methods=['GET', 'POST'])
@login_required
def admin_pop_up_transactions(transaction_id, mode):
    if 'username' not in session:
        return redirect(url_for('admin_dashboard_login'))

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch transaction data based on `transaction_id`
    mycursor.execute("""
        SELECT 
            t.Transaction_ID,
            t.Property_Code,
            CONCAT(g.First_Name, ' ', g.Middle_Name, ' ', g.Last_Name) AS Booker,
            t.Total_Num_of_Guests,
            t.Total_Num_of_Vehicles,
            t.Date_of_Checkin,
            t.Date_of_Checkout,
            t.Total_Price,
            t.Transaction_Status AS Status,
            t.Environmental_Fee_Total,
            t.Environmental_Fee_Status
        FROM transactions t
        JOIN guestsinfo g ON t.Booker_ID = g.Guest_ID
        WHERE t.Transaction_ID = %s
    """, (transaction_id,))

    transaction = mycursor.fetchone()

    if not transaction:
        mycursor.close()
        mydb.close()
        return "Transaction not found", 404  # Handle case where transaction doesn't exist

    if mode == 'edit' and request.method == 'POST':
        # Get form data for editing the transaction
        updated_booker = request.form['booker']
        updated_guests = request.form['guests']
        updated_vehicles = request.form['vehicles']
        updated_property_code = request.form['property_code']
        updated_contact = request.form['contact']
        updated_total_price = request.form['total_price']
        updated_status = request.form['transaction_status']
        updated_checkin_date = request.form['checkin_date']
        updated_checkin_time = request.form['checkin_time']
        updated_checkout_date = request.form['checkout_date']
        updated_checkout_time = request.form['checkout_time']
        updated_env_fee = request.form['env_fee']
        updated_env_status = request.form['env_status']

        # Update transaction details in the database
        mycursor.execute("""
            UPDATE transactions
            SET 
                Booker = %s,
                Total_Num_of_Guests = %s,
                Total_Num_of_Vehicles = %s,
                Property_Code = %s,
                Contact_Number = %s,
                Total_Price = %s,
                Transaction_Status = %s,
                Date_of_Checkin = %s,
                Time_of_Checkin = %s,
                Date_of_Checkout = %s,
                Time_of_Checkout = %s,
                Environmental_Fee_Total = %s,
                Environmental_Fee_Status = %s
            WHERE Transaction_ID = %s
        """, (
            updated_booker, updated_guests, updated_vehicles, updated_property_code, 
            updated_contact, updated_total_price, updated_status, updated_checkin_date, 
            updated_checkin_time, updated_checkout_date, updated_checkout_time, 
            updated_env_fee, updated_env_status, transaction_id
        ))

        mydb.commit()
        flash('Transaction details successfully updated!', 'success')
        return redirect(url_for('admin_dashboard_transactions'))

    mycursor.close()
    mydb.close()

    # Render the appropriate template based on mode (view or edit)
    if mode == 'view':
        return render_template('admin_dashboard/pop_up_view_transactions.html', transaction=transaction)
    elif mode == 'edit':
        return render_template('admin_dashboard/pop_up_edit_transactions.html', transaction=transaction)
    else:
        return "Invalid mode", 400  # Handle invalid mode

@app.route('/delete_property/<int:property_id>', methods=['POST'])
@login_required
def delete_property(property_id):
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 403

    # Connect to the database
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor()

    try:
        # Delete property from the rentals table
        mycursor.execute("DELETE FROM rentals WHERE Property_Code = %s", (property_id,))
        mydb.commit()

        # Optionally, delete associated images from the property_pictures table
        mycursor.execute("DELETE FROM property_pictures WHERE Property_Code = %s", (property_id,))
        mydb.commit()

        return jsonify({'status': 'success', 'message': 'Property deleted successfully'})
    
    except Exception as e:
        mydb.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
    
    finally:
        mycursor.close()
        mydb.close()


@app.route('/popup/admin_dashboard/add_transaction')
def admin_pop_up_add_transactions():
    return render_template('admin_dashboard/pop_up_add_transactions.html')

@app.route('/update_resort_details', methods=['GET', 'POST'])
def update_resort_details():
    if 'username' not in session:
        flash("Not logged in", "error")
        return redirect(url_for('login'))  # Ensure user is logged in

    username = session['username']
    mydb = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="@Eddielynjoy123",
        database="porto_laiya_database"
    )
    mycursor = mydb.cursor(dictionary=True)

    # Fetch resort details
    mycursor.execute("""
        SELECT r.Description, r.Price, p.Image
        FROM rentals r
        JOIN property_pictures p ON r.Property_Code = p.Property_Code
        JOIN login_credentials l ON r.Property_Code = l.Property_Code
        WHERE l.Username = %s
    """, (username,))

    resort_details = mycursor.fetchall()

    description = resort_details[0]['Description'] if resort_details else ''
    price_per_day = resort_details[0]['Price'] if resort_details else 0
    images = [row['Image'] for row in resort_details] if resort_details else []

    # Handle POST request to update details
    if request.method == 'POST':
        description = request.form['description']
        price_per_day = request.form['price_per_day']
        
        # Update the description and price in the database
        try:
            mycursor.execute("""
                UPDATE rentals
                SET Description = %s, Price = %s
                WHERE Property_Code = (SELECT Property_Code FROM login_credentials WHERE Username = %s)
            """, (description, price_per_day, username))

            # Save uploaded images (assuming the file input is included)
            if 'images' in request.files:
                images = request.files.getlist('images')
                for img in images:
                    if img:
                        img.save(os.path.join('static/uploads', img.filename))
                        mycursor.execute("""
                            INSERT INTO property_pictures (Property_Code, Image)
                            VALUES ((SELECT Property_Code FROM login_credentials WHERE Username = %s), %s)
                        """, (username, img.filename))

            mydb.commit()
            flash("Resort details updated successfully", "success")
        except Exception as e:
            mydb.rollback()
            flash(f"Error updating details: {str(e)}", "error")

    mycursor.close()
    mydb.close()

    # Redirect to the rentals dashboard home to show the updated information
    return redirect(url_for('rentals_dashboard_home'))  # Redirect to home after update




# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

