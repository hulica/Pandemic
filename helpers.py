from configparser import ConfigParser
import psycopg2
from psycopg2 import Error

import matplotlib.pyplot as plt
from countryinfo import CountryInfo
import wget
from flask import redirect, session
from functools import wraps
import os
import csv
import numpy as np


# helper funcion for progresql database connection
# on the basis of https://www.postgresqltutorial.com/postgresql-python/transaction/
def open_connection():
    # # The below outcommented part could be used to set up a connection to a local database if one creates a database.ini file:
    # def config(filename='database.ini', section='postgresql'):
    # create a parser
    #   parser = ConfigParser()
    # read config file
    #  parser.read(filename)

    # get section, default to postgresql
    # params = {}
    # if parser.has_section(section):
    #     parameters = parser.items(section)
    #     # takes out the section (postgresql) and puts the connection parameters in a dictionary as an output
    #     for parameter in parameters:
    #         params[parameter[0]] = parameter[1]
    # else:
    #     raise Exception(
    #         'Section {0} not found in the {1} file'.format(section, filename))

    # return params

    try:

        DATABASE_URL = os.environ['DATABASE_URL']
        #params = config()
        # Connect to postgreSQL database
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')

        # Create a cursor to perform database operations
        cursor = connection.cursor()
        connection.commit()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)

    return connection, cursor


def close_connection(connection, cursor):

    if (connection):
        cursor.close()
        connection.close()
        #print("PostgreSQL connection is closed")


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_player_hand(players):
    if players == 2:
        hand = 4
    elif players == 3:
        hand = 3
    else:  # 4 or 5 players
        hand = 2
    return hand


def get_difficulty(epidemic_cards):

    if epidemic_cards == 4:
        difficulty = "Easy"
    elif epidemic_cards == 5:
        difficulty = "Hard"
    elif epidemic_cards == 6:
        difficulty = "Heroic"
    else:  # 7 epidemic cards
        difficulty = "Legendary"
    return difficulty


def game_setup(players, epidemic_cards):
    # calculates the required number of cards for the setup

    # constants
    CITY_CARDS = 48
    BASIC_EVENTS = 5
    hand = get_player_hand(players)
    event_cards = players * 2
    difficulty = get_difficulty(epidemic_cards)

    # how many small decks you need to make:  as many decks as epidemic cards
    deck_no = epidemic_cards
    # this tells how many bigger part deck it is as the deck is not dividable by the nr of the epidemic cards
    pre_total_deck = - hand * players + CITY_CARDS + event_cards

    # calculates the number of rounds the players will play
    total_deck = pre_total_deck + epidemic_cards
    rounds = total_deck // (players * 2)

    # the default part decks card number
    default_part_deck = pre_total_deck // deck_no
    # if a default decks are up to the whole deck, it is fine. If not, some decks have to be bigger
    number_of_bigger_part_decks = pre_total_deck - \
        (default_part_deck * deck_no)

    if number_of_bigger_part_decks > 0:
        bigger_part_deck = default_part_deck + 1
    else:
        bigger_part_deck = default_part_deck
    # puts these into a dictionary so that only one variable has to be passed:
    game = {
        'players': players,
        'epidemic_cards': epidemic_cards,
        'difficulty': difficulty,
        'event_cards': event_cards,
        # the default card number for the part decks before mixing the epidemic card

        'hand': hand,
        'default_part_deck': default_part_deck,
        # if some part deck should be bigger than the smaller part deck
        'number_of_bigger_part_decks': number_of_bigger_part_decks,
        'bigger_part_deck': bigger_part_deck,
        'rounds': rounds
    }
    return game


