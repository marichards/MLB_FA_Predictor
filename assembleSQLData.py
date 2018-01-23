# Import everything from dataScraping
from dataScraping import *
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import psycopg2
import pandas as pd
import pickle

## Step 1: Assemble Web Data

# Create a list of years and use it to create the free agent data
all_years = list(range(2006,2018))
all_fa_data = getAllFAData(all_years)

# Grab payroll data for 2006 to present
team_payrolls = scrapePayrollData(2006)

# Simply load the Team WAR data
with open('position_war.pickle', 'rb') as file:
    position_war = pickle.load(file)

with open('pitcher_war.pickle', 'rb') as file:
    pitcher_war = pickle.load(file)    

## Step 2: Load Local CSV data
all_batting = pd.read_csv("../baseballdatabank/core/Batting.csv")
all_pitching = pd.read_csv("../baseballdatabank/core/Pitching.csv")
all_salary = pd.read_csv("../baseballdatabank/core/Salaries.csv")
all_people = pd.read_csv("../baseballdatabank/core/People.csv")
all_appearances = pd.read_csv("../baseballdatabank/core/Appearances.csv")
all_teams = pd.read_csv("../baseballdatabank/core/Teams.csv")

## Step 3: Connect to the database (create it if necessary)

# Set postgres username/password, and connection specifics
username = 'matt'
password = 'trena'     # change this
host     = 'localhost'
port     = '5432'            # default port that postgres listens on
db_name  = 'mlb_fa_db'

engine = create_engine( 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(username, password, host, port, db_name) )
print(engine.url)

## create a database (if it doesn't exist)
if not database_exists(engine.url):
    create_database(engine.url)
print(database_exists(engine.url))


## Step 4: Write the tables

# Filter Lahman tables
batting_2004, pitching_2004, salary_2004, teams_2004, appearances_2004 = [
df[df.yearID >= 2004] for df in [all_batting, all_pitching, all_salary, all_teams, all_appearances]]

# Insert all tables into SQL

# 1-6 (Lahman tables)
batting_2004.to_sql('batting', engine, if_exists='replace')
pitching_2004.to_sql('pitching', engine, if_exists = 'replace')
salary_2004.to_sql('salary', engine, if_exists='replace')
all_people.to_sql('people', engine, if_exists = 'replace')
appearances_2004.to_sql('appearances', engine, if_exists = 'replace')
teams_2004.to_sql('teams', engine, if_exists = 'replace')

# 7-9 The other 4 tables
position_war.to_sql("position_team_war", engine, if_exists = 'replace')
pitcher_war.to_sql("pitcher_team_war", engine, if_exists = 'replace')
team_payrolls.to_sql("payrolls", engine, if_exists= 'replace')
all_fa_data.to_sql("free_agents", engine, if_exists = 'replace')
