from mlb_flask_app import app # Bring in the app
from flask import render_template, request # Bring in template and request functionality
from sqlalchemy import create_engine # Bring in DB connection ability
from sqlalchemy_utils import database_exists, create_database # More DB
import pandas as pd # DFs
import psycopg2 # Postgres language specifics

# Bring in my user-defined models
import mlb_flask_app.models as models
import mlb_flas_app.buildFeatureMatrix as bfm


# Set postgres username/password, and connection specifics
username = 'matt'
password = 'trena'     # change this
host     = 'localhost'
port     = '5432'            # default port that postgres listens on
db_name  = 'mlb_fa_db'

engine = create_engine( 'postgresql://{}:{}@{}:{}/{}'.format(username, password, host, port, db_name) )

con = None
con = psycopg2.connect(database = db_name,
                       user = username,
                       password = password,
                       host = host)

def index():
    # Use user Miguel on the main and index pages

    return render_template("index.html",
                           title = 'Home',
                           user = {'nickname' : 'Miguel'})

# Add the database page
@app.route('/2017')
def page_2017():
    sql_query = """

SELECT * FROM free_agents where "Year" = 2017;

"""

    query_results = pd.read_sql_query(sql_query, con)
    free_agents = ""
    for i in range(0,10):
        free_agents += query_results.iloc[i]['Full_Name']
        free_agents += "<br>"

    return free_agents

# Add a fancy database page
@app.route('/2017_fancy')
def page_2017_fancy():
    sql_query = """

SELECT * FROM free_agents WHERE "Year" = 2017;

"""
    query_results = pd.read_sql_query(sql_query, con)
    free_agents = []

    # Go through all rows
    for i in range(0, query_results.shape[0]):

        free_agents.append(dict(name = query_results.iloc[i]['Full_Name'],
                           age = query_results.iloc[i]['Age'],
                           destination = query_results.iloc[i]['Destination']))

    return render_template('cesareans.html', free_agents = free_agents)

# Add "Input" and make it the home page too
@app.route('/input')
@app.route('/')  
@app.route('/index')
def fa_input():
    return render_template('input.html')

# Add "Output"
@app.route('/output')
def fa_output():
    # pull 'fa_year' from input field and store it as an integer
    fa_year = int(request.args.get('fa_year'))

    # Load and prepare the datasets
    pitcher_all, position_all = models.loadAllData()
    pitcher_prepped = models.prepareFreeAgentData(pitcher_all)
    position_prepped = models.prepareFreeAgentData(position_all)

    # Use year to split dataset
    X_train_pitch, y_train_pitch, X_test_pitch, y_test_pitch = models.splitDataByYear(pitcher_prepped, fa_year, 'pitcher')
    X_train_pos, y_train_pos, X_test_pos, y_test_pos = models.splitDataByYear(position_prepped, fa_year, 'position')

    # Predict whether they'll get contracts
    _, contract_pitch = models.predictContract(X_train_pitch, y_train_pitch, X_test_pitch)
    _, contract_pos = models.predictContract(X_train_pos, y_train_pos, X_test_pos)

    # Predict contract length
    _, length_pitch = models.predictLength(X_train_pitch, y_train_pitch, X_test_pitch)
    _, length_pos = models.predictLength(X_train_pos, y_train_pos, X_test_pos)

    # Predict contract dollars
    _, dollars_pitch = models.predictDollars(X_train_pitch, y_train_pitch, X_test_pitch)
    _, dollars_pos = models.predictDollars(X_train_pos, y_train_pos, X_test_pos)

    # Grab the inflation factor
    inflation_factor = pitcher_prepped[pitcher_prepped.Year == fa_year]['Inflation_Factor'].unique()[0]

    # select free agents for that year
    query = 'SELECT * FROM free_agents WHERE "Year" = {}'.format(fa_year)

    query_results = pd.read_sql_query(query, con)

    free_agents = []
    for i in range(0, query_results.shape[0]):

        free_agents.append(dict(name = query_results.iloc[i]['Full_Name'],
                                age = query_results.iloc[i]['Age'],
                                destination = query_results.iloc[i]['Destination'],
                                length = query_results.iloc[i]['Length'],
                                dollars = query_results.iloc[i]['Dollars']))
    return render_template('output.html', free_agents = free_agents)

# Add a "Contact" page
@app.route('/db_fancy#contact')

def contacts():
    ''' Put a simple contact info'''
    

    return render_template("index.html",
                           title = 'Contacts',
                           user = {'nickname' : 'Miguel'})

@app.route('/jumbo')
def home_page():
    '''Organize the home page with the Jumbotron template'''

    return render_template("jumbotron.html")
