
import csv
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime


from helpers import game_setup, login_required, draw_covid_graph, open_connection, close_connection

import logging


# log = logging.getLogger('werkzeug')


# Configure application
app = Flask(__name__)
# app.debug = False

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)


@app.route("/statistics", methods=["GET", "POST"])
@login_required
def statistics():
    user_id = session["user_id"]  # get user id from the session:

    if request.method == "GET":  # display form
        message = "Fill in the below data"
        # database query on recorded games
        connection, cursor = open_connection()
        select_query = "SELECT game_id, player_nr, epidemic_nr, result, lost_due_to, character, comment, datum FROM games WHERE user_id = %s"
        cursor.execute(select_query, (user_id,))
        connection.commit()
        game_history = cursor.fetchall()  # game_history will be a tuple (list of lists)

        select_query = "SELECT username FROM users WHERE user_id = %s"
        cursor.execute(select_query, (user_id,))

        connection.commit()
        result = cursor.fetchall()

        username = result[0][0].capitalize()

        print("username", username)

        close_connection(connection, cursor)  # close PostgreSQL connection
        return render_template("statistics.html", message=message, game_history=game_history, result=result, username=username)

    else:  # the form has been posted, the user registers its recent game into the database
        message = "Your game has been registered."

        player_nr = request.form.get('player_nr')
        epidemic_nr = request.form.get('epidemic_nr')
        result = request.form.get('result')
        if result == "Loss":
            lost_due_to = request.form.get('lost_due_to')
        else:
            lost_due_to = "N/A"
        character = request.form.get('character')
        comment = request.form.get('comment')
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not player_nr or not epidemic_nr or not result:
            message = "Missing fields: please fill in number of players, epidemic cards and Win / Loss, at least."

            connection, cursor = open_connection()
            select_query = "SELECT game_id, player_nr, epidemic_nr, result, lost_due_to, character, comment, datum FROM games WHERE user_id = %s"
            cursor.execute(select_query, (user_id,))
            connection.commit()
            game_history = cursor.fetchall()  # game_history will be a tuple (list of lists)

            select_query = "SELECT username FROM users WHERE user_id = %s"  # get username
            cursor.execute(select_query, (user_id,))

            connection.commit()

            result = cursor.fetchall()

            username = result[0][0].capitalize()

            print("username", username)

            close_connection(connection, cursor)  # close PostgreSQL connection
            return render_template("statistics.html", message=message, game_history=game_history, result=result, username=username)

        else:
            # insert game into games table

            connection, cursor = open_connection()  # open database connection
            insert_query = 'INSERT INTO games (user_id, player_nr, epidemic_nr, result, lost_due_to, character, comment, datum) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'

            cursor.execute(insert_query, (user_id, player_nr, epidemic_nr,
                           result, lost_due_to, character, comment, date_now))

            select_query = "SELECT game_id, player_nr, epidemic_nr, result, lost_due_to, character, comment, datum FROM games WHERE user_id = %s"
            cursor.execute(select_query, (user_id,))
            connection.commit()
            game_history = cursor.fetchall()  # game_history will be a tuple (list of lists)

            select_query = "SELECT username FROM users WHERE user_id = %s"  # get username
            cursor.execute(select_query, (user_id,))

            connection.commit()
            result = cursor.fetchall()

            username = result[0][0].capitalize()

            # print("username", username)

            close_connection(connection, cursor)  # close PostgreSQL connection
            return render_template("statistics.html", message=message, game_history=game_history, result=result, username=username)


@ app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username") or not request.form.get("password"):
            message = "Please fill in both username and password."
            return render_template("login.html", message=message)

        # Query database for username
        username = request.form.get("username")

        connection, cursor = open_connection()  # open PostgreSQL database connection
        select_query = "SELECT user_id, hash FROM users where username = %s"

        cursor.execute(select_query, (username,))
        connection.commit()
        result = cursor.fetchall()
        close_connection(connection, cursor)  # close PostgreSQL connection

        # Ensure username exists and password is correct
        if len(result) != 1 or not check_password_hash(result[0][1], request.form.get("password")):
            message = "Incorrect username or password."
            return render_template("login.html", message=message)

        # Remember which user has logged in
        # user result[0][3] is the user_id of the first (and only) match
        session["user_id"] = result[0][0]
        print(result[0][0])

        # Redirect user to statistics
        return redirect("/statistics")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@ app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@ app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        confirmation = request.form.get("confirmation")

        # Checking username and password requirements

        # Ensure username was submitted
        if not username:
            message = "must provide username"
            return render_template("register.html", message=message)

            # Ensure both password and confirmation was submitted and they are matching
        elif not password or not confirmation or password != confirmation:
            message = "must provide password and matching confirmation"
            return render_template("register.html", message=message)

        else:  # if username, password and confirmation was submitted, the program checks whether the username is already taken in the database
            # run a select query against the table to see if any record exists
            # (if there is more than 0 records, the username is taken)

            connection, cursor = open_connection()  # open PostgreSQL database connection

            select_query = 'SELECT username FROM users WHERE username = %s'
            cursor.execute(select_query, (username,))
            connection.commit()
            result = cursor.fetchone()

            if result:
                message = "username is already taken"

                # close PostgreSQL connection
                close_connection(connection, cursor)

                return render_template("register.html", message=message)

            else:

                # Register: create hash for password and insert into database along with username
                hashed_pwd = generate_password_hash(password)

                insert_query = 'INSERT INTO users (username, hash, email) VALUES (%s,%s,%s)'
                # !!! itt debuggingból kicseréltem a hashed pwd-t passwordre, ezt majd vissza kell cserélni!!!
                cursor.execute(insert_query, (username, hashed_pwd, email))
                connection.commit()
                # close PostgreSQL connection
                close_connection(connection, cursor)

                # Redirect user to login page
                message = "Thank you for registering, please log in!"
                #message = username + " volt a username, a password pedig " + password
                return render_template("login.html", message=message)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@ app.route("/", methods=["GET", "POST"])
def set_up():
    if request.method == "GET":  # display form

        return render_template("index.html")

    else:  # the form has been posted
        players = request.form.get("players")
        epidemic_cards = request.form.get("epidemic_cards")

        if not players or not epidemic_cards:
            message = "Fill in the number of players and epidemic cards."
            return render_template("index.html", message=message)
        else:
            # the form will get a string which needs to be transformed to int
            game = game_setup(int(players), int(epidemic_cards))
            return render_template("setup.html", game=game)


@ app.route("/covid", methods=["GET", "POST"])
def covid():
    """Get countries for checking covid data"""

    # get list of all the reported countries from a csv. This will be used by the form as the potential countries, from where the user can choose
    country_file = "countries.csv"
    countries = []
    with open(country_file) as f:
        reader = csv.reader(f)
        for line in reader:  # the countries are a list in one line
            for country in line:
                countries.append(country)

    # this is reported to Johns Hopkins but no population data exists so cannot be displayed in per capita graphs

    if request.method == "GET":  # display form
        message = ""
        return render_template("covid.html", message=message, countries=countries)

    else:  # the form has been posted
        country_list = []

        # collect countries from the form
        country1 = request.form.get("country1")
        country2 = request.form.get("country2")
        country3 = request.form.get("country3")

        if not not country1:  # ez tudom h nagyon csúnya, egyesével appendálom, ha submittáltak ilyet
            country_list.append(country1)

        if not not country2:
            country_list.append(country2)

        if not not country3:
            country_list.append(country3)

        for country in country_list:
            # if not a valid country, they should be dropped. after this step, the country_ist countains the valid country choices of the user
            if country == '' or country not in countries:
                country_list.remove(country)

        # makes one single string from the selected countries separated with comas to display it on the website
        countrystring = ""
        for i in range(len(country_list)):

            if i == len(country_list)-1:
                countrystring += " " + country_list[i]
            elif i == len(country_list)-2:  # there are other countries coming, we need a coma
                countrystring += " " + country_list[i] + " and"
            else:
                countrystring += " " + country_list[i] + ","

        message = "COVID status for " + countrystring
        graph_infect, graph_death = draw_covid_graph(country_list)

        return render_template("covid_results.html", message=message, countries=countries, graph_infect=graph_infect, graph_death=graph_death)
