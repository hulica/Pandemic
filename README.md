
# Pandemic Game Assistant WebApp

#### Video demo: https://youtu.be/seAECzwYRk8
The web application is related to my favorite board game: ***Pandemic: on the brink***. It is a cooperative game where players work as a team to treat infections around the world while gathering resources for cures.  

The purpose of this app is to make the setup of the game quicker and to keep track of the wins and defeats of users.  

The app is deployed on Heroku and is available under https://pandemic-setup.herokuapp.com/.




## Features

The app has three functions as follows. 

### 1. Game start calculations

On the default page, the user can select the player number and the number of epidemic cards they wish to play with.  

Then the page outputs all the data the players need to know to put together the players' deck: number of event cards, players' starting hands, shuffle decks and calculates the maximum number of rounds until the end of the game.  

![setup2](https://user-images.githubusercontent.com/77074609/132104446-023def05-3fc9-4106-b139-a0a7b465a805.jpg)

This can be used without registration / logging in. 

### 2. Game history

Registered users can record their games under statistics and then check out their game history.  
 
![Game_history](https://user-images.githubusercontent.com/77074609/132104087-aa52fa4c-54f6-4b65-8845-9a4e8864cd48.jpg)  

### 3. Show real-time COVID data

The app builds population proportionate COVID infection and fatality graphs based on the data provided by Johns Hopkins University Coronavirus Research Center.
Users can pick one or two countries from the two dropdown menu and the app builds the graphs and displays in a png format.  

![nagycovid](https://user-images.githubusercontent.com/77074609/132104324-ef3856b9-78d8-4654-9f8e-dd56625341be.jpg)

  
## Main elements of the project

The project uses Flask framework and consists of the following files:

- **application.py** is the main application covering all the routes, while its helper functions are put in **helpers.py**. 

- User data and recorded games are stored in a **PostgreSQL database**, hosted by Heroku (Heroku Postgres). Initially, I started with a sqlite3 database, however at deployment I realized that with sqlite3 the application would lose the database every 24 hours, so I changed to PostgreSQL instead.    

    - *Users table* stores the users' id, name, email and hash of password. Passwords themselves are not stored. Hash is generated with help of the werkzeug library and the user's session is created by flask_session's Session object.   
    - *Games table* stores the id of the game, user id, number of epidemic cards and players, result of the game and on which account did the player lose, played character and some comments.   
    - The database address is stored as an environment variable. Opening (and closing) a database connection are put into separate functions and called for prior (and after) each Select / Insert query to save on connection pool. Queries are constructed with SQL parameters in order to prevent injections.  

- **HTML files** can be found in the template folder and rely on layout.html as a template. Styling is completed with Bootstrap classes and a styles.css stylesheet. Flask requires that images are located in the static/img folder.  

- **Building COVID graphs** is the most complex part of the project from python point of view and it is done by prepare_infect_graph() function in **helpers.py**. 
    - First, the program downloads the raw data from Johns Hopkins University's Github repository in csv files. 
    - Then the program filters the data for the countries required by the user, gets the population data from the countryinfo library and calculates the population relative data. Some country names in Johns Hopkins' data slightly differ from that of countryinfo, so this is taken care of before getting the population data. 
    - A numpy array populates proper date format for the time series and pyplot builds and saves the graphs in png format which will be displayed in covid.html. The data files are deleted once they are not needed any more. 
- For deployment on Heroku, the application uses **gunicorn** as web server and this is reflected in the **Procfile**, required by Heroku. 

  
## Documentation

[Documentation](https://github.com/hulica/Pandemic)

  
## Run Locally

Clone the project

```bash
  git clone https://github.com/hulica/Pandemic.git
```

Go to the project directory

```bash
  cd Pandemic
```

Install dependencies from requirements.txt

```bash
  pip install -r requirements.txt
```

Create a Heroku Postgres database for project
- If you login to Heroku, you can go to its web interface (Dashboard), where you can create a new project (New / Create new app) and then in the Resources menu of your new app add the Heroku Postgres add-on in the add-ons. This generates a DATABASE_URL (stored as an evironment variable in your Heroku environment)
- Alternatively you can create your new project and add Heroku Postgres in the Heroku CLI, as well: 

```bash
  heroku create <my_project>
  heroku addons:create heroku-postgresql:hobby-dev --app <my_project>
  heroku config --app <my_project>
```


Add DATABASE_URL to your local environment variable:

```bash
  export DATABASE_URL=<my_DATABASE_URL>
```

To add the tables, go to the postgres CLI:

```bash
  heroku pg:psql --app <my_project>
```

This connects you to the database and you can create the tables: 

```bash
  CREATE TABLE IF NOT EXISTS public.users
(
    user_id SERIAL NOT NULL,
    username text,
    hash text,
    email text,
    PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS public.games
(
    game_id SERIAL NOT NULL,
    user_id integer NOT NULL,
    epidemic_nr integer,
    result character varying,
    lost_due_to character varying,
    comment text,
    "character" text,
    player_nr integer,
    datum timestamp without time zone,
    PRIMARY KEY (game_id)
);
```

Now your Heroku Postgres database has the necessary tables, so you can start the app locally: 
```bash
  flask run
```
## Tech Stack

Python, Flask, PostgreSQL, Heroku

  
## License

[MIT](https://choosealicense.com/licenses/mit/)

## Authors

- Linczer Andrea [@hulica](https://github.com/hulica)


## 🚀 About Me
I'm in finance in the phase of changing my career and learning how to code. 

  
## How to develop further this project?

It may be useful to include further functionalities:

- Add functionalities such as changing password, reset forgotten passwords
- Enhance statistics: add dashboard to user's own statistic so that user can filter / check success ratio specific to various difficulty levels.
- Add pie-charts to statistics to give users a more visual feedback. 

  
