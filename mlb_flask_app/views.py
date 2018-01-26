from mlb_flask_app import app # Bring in the app
from flask import render_template, request # Bring in template and request functionality
from sqlalchemy import create_engine # Bring in DB connection ability
from sqlalchemy_utils import database_exists, create_database # More DB
import pandas as pd # DFs
import numpy as np # Numpy
import psycopg2 # Postgres language specifics

# Bring in my user-defined models
import mlb_flask_app.models as models
import mlb_flask_app.buildFeatureMatrix as bfm


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

# Debug the navbar
@app.route('/navbar')
def navbar():
    '''Make a working navbar'''
    return render_template("navbar.html")

@app.route('/')  
@app.route('/index')
def index():
    '''Organize the home page with the Jumbotron template'''

    return render_template("jumbotron.html")

@app.route('/about_me')
def aboutme():
    '''Return info about me'''

    return render_template("aboutme.html")

@app.route('/algorithm')
def algorithm():
    '''Information about how it works'''

    return render_template("algorithm.html")

@app.route('/validation')
def validation():
    '''Plots and tables showing validation, with text in between'''

    return render_template("validation.html")

# Add "Input" and make it the home page too
@app.route('/input')
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

    # Create 2 data frames
    pitchers_df =  pd.DataFrame({'nameFirst' : pitcher_prepped[pitcher_prepped.Year == fa_year]['nameFirst'].values,
                                 'nameLast' : pitcher_prepped[pitcher_prepped.Year == fa_year]['nameLast'].values,
                                 'position' : pitcher_all[pitcher_prepped.Year == fa_year]['Position'],
                                 'contract_pred' : contract_pitch,
                                 'contract_actual' : y_test_pitch['Contract'],
                                 'length_pred' : length_pitch,
                                 'length_actual': y_test_pitch['Length'],
                                 'dollars_pred' : np.round(dollars_pitch * length_pitch * inflation_factor, decimals = -5),
                                 'dollars_actual' : y_test_pitch['Dollars']})

    position_df =  pd.DataFrame({'nameFirst' : position_prepped[position_prepped.Year == fa_year]['nameFirst'].values,
                                 'nameLast' : position_prepped[position_prepped.Year == fa_year]['nameLast'].values,
                                 'position' : position_all[position_prepped.Year == fa_year]['Position'],
                                 'contract_pred' : contract_pos,
                                 'contract_actual' : y_test_pos['Contract'],
                                 'length_pred' : length_pos,
                                 'length_actual': y_test_pos['Length'],
                                 'dollars_pred' : np.round(dollars_pos * length_pos * inflation_factor, decimals = -5),
                                 'dollars_actual' : y_test_pos['Dollars']})

    # Put them together via stacking
    full_df = pd.concat([pitchers_df, position_df])

    # Catch negatives
    full_df.loc[full_df['dollars_pred'] < 0, 'dollars_pred'] = 0
    # Do some more formatting
    full_df['dollars_actual'] = full_df['dollars_actual'].apply(lambda x: '{:,.2f}'.format(x))
    full_df['dollars_pred'] = full_df['dollars_pred'].apply(lambda x: '{:,.2f}'.format(x))
    full_df['dollars_actual'].replace({'nan': '0'}, inplace = True)
    full_df.loc[full_df.contract_pred == False,'dollars_pred'] = '0'
    full_df.loc[full_df.contract_pred == False,'length_pred'] = 0

    return render_template('output.html', free_agents = full_df)
