# Bring in packages and connect to database
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import psycopg2
import math
import pandas as pd
from scipy.stats import zscore


def db_connect():
    # Set postgres username/password, and connection specifics
    username = 'postgres'
    password = 'S@ndw1ches'     # change this
    host     = 'localhost'
    port     = '5432'            # default port that postgres listens on
    db_name  = 'mlb_fa_db'
    
    engine = create_engine( 'postgresql://{}:{}@{}:{}/{}'.format(username, password, host, port, db_name) )

    return engine

# Make a quick querying function
def pullFullTable(table, engine):
    '''Quick little function for pulling a full table'''
    
    query = 'select * from {}'.format(table)
    
    # Execute the query with context manager
    with engine.connect() as con:
        results = con.execute(query)
        fetched_data = pd.DataFrame(results.fetchall())
        fetched_data.columns = results.keys()
        
    return fetched_data

def createBattingTable(engine):
    '''Grab all the batting data, compute stats, and return the finished, normalized form'''
   
    # Create our query
    batting_data = pullFullTable('batting', engine)
    
    # Drop non-numeric team/league columns
    batting_data.drop(['teamID','lgID'], axis = 1)
    
    # Add data from players who had multiple stints and 
    batting_totals = batting_data.groupby(['playerID','yearID'], as_index= False).sum()
    
    # Create new variables and select only them (fill NaN with 0)
    batting_totals['OBP'] = (batting_totals['H'] + 
                             batting_totals['BB'] + 
                             batting_totals['HBP']).divide(batting_totals['AB'] + 
                                                           batting_totals['BB'] + 
                                                           batting_totals['HBP'] + 
                                                           batting_totals['SF']).fillna(0)

    batting_totals['SLG'] = (batting_totals['H'] + 
                             batting_totals['2B'] + 
                             2 * batting_totals['3B'] + 
                             3 * batting_totals['HR']).divide(batting_totals['AB']).fillna(0)

    batting_trimmed = batting_totals[['playerID', 'yearID', 'G', 'OBP', 'SLG', 'HR', 'RBI', 'SB']]
    
    # Standardize the numerical columns by year
    numerical = ['G', 'OBP', 'SLG', 'HR', 'RBI', 'SB']

    batting_trimmed[numerical] = batting_trimmed.groupby('yearID')[numerical].transform(zscore)
    
    return batting_trimmed


# Define function for pulling pitching data
def createPitchingTable(engine):
    '''Grab all the pitching data, compute stats, and return the finished, normalized form'''
   
    # Create our query
    pitching_data = pullFullTable('pitching', engine)
    
    # Select only the final, counting-stat columns (drop ERA, other things)
    pitching_trimmed = pitching_data[['playerID', 'yearID', 'W', 'SV', 'IPouts', 
                                      'H', 'ER' , 'HR', 'BB', 'SO']]
    
    # Add data from players who had multiple stints
    pitching_totals = pitching_data.groupby(['playerID','yearID'], as_index= False).sum()
    
    # Remove players with 0 IPouts
    pitching_totals = pitching_totals[pitching_totals.IPouts > 0]
    
    # Create new variables (ERA, WHIP, K/9)
    pitching_totals['ERA'] = pitching_totals['ER'].divide(pitching_totals['IPouts']/27)#.fillna(math.inf)
    pitching_totals['WHIP'] = (pitching_totals['H'] + 
                               pitching_totals['BB']).divide(pitching_totals['IPouts']/3)#.fillna(math.inf)
    pitching_totals['K_9'] = pitching_totals['SO'].divide(pitching_totals['IPouts']/27).fillna(0)
    pitching_totals['HR_9'] = pitching_totals['HR'].divide(pitching_totals['IPouts']/27)#.fillna(math.inf)

    pitching_final = pitching_totals[['playerID', 'yearID', 'ERA', 'WHIP', 
                                      'K_9', 'HR_9','IPouts', 'W', 'SV']]
    
    # Standardize the numerical columns by year
    numerical = ['ERA', 'WHIP', 'K_9', 'HR_9','IPouts', 'W', 'SV']
    pitching_final[numerical] = pitching_final.groupby('yearID')[numerical].transform(zscore, )
    
    return pitching_final

# Add free agent data to a stats dataframe
def addFilterFreeAgents(stats_df, engine):

    '''Given a data frame of stats, add the FA stats to it'''

    # Bring in people and free agents
    people = pullFullTable('people', engine)
    free_agents = pullFullTable('free_agents', engine)

    # Trim the "people" to only the first/last name and playerID, which is for joining
    people_trimmed = people[['playerID', 'nameFirst', 'nameLast']]
    
    # Join to the table of interest
    stats_w_people = pd.merge(stats_df, people_trimmed, on = 'playerID', how = 'inner')
    
    # Join to free agents based on nameFirst/nameLast
    free_agents_trimmed = free_agents[['Age', 'Destination', 'WAR_3', 'nameFirst', 'nameLast',
                                       'Year', 'Dollars', 'Length', 'Position']]
    free_agent_stats = pd.merge(free_agents_trimmed, stats_w_people, 
                                left_on = ['nameFirst', 'nameLast', 'Year'],
                                right_on = ['nameFirst', 'nameLast', 'yearID'])
    
    return free_agent_stats

# Add team WAR values for each position (including pitchers!)
def allPositionWAR(fa_stats, engine):
    
    # Pull the data but drop the index
    position_only_war = pullFullTable('position_team_war', engine).drop(['index'], axis = 1)
    pitching_war = pullFullTable('pitcher_team_war', engine).drop(['index'], axis = 1)
    
    # Put them together
    position_war = pd.concat([position_only_war, pitching_war])
    
    # Change the Year to "yearID"
    position_war['yearID'] = position_war.Year
    position_war = position_war.drop(['Year'], axis = 1)
    
    # Create a dictionary for converting these to abbreviations
    team_dict = {'Angels' : 'LAA', 'Astros' : 'HOU', 'Athletics' : 'OAK', 'Blue Jays' : 'TOR', 
                 'Braves' : 'ATL', 'Brewers': 'MIL', 'Cardinals' : 'STL', 'Cubs' : 'CHN',
                 'Diamondbacks' : 'ARI', 'Dodgers' : 'LAN', 'Giants' : 'SFN', 'Indians' : 'CLE',
                 'Mariners' : 'SEA', 'Marlins' : 'MIA', 'Mets' : 'NYN', 'Nationals' : 'WAS',
                 'Orioles' : 'BAL', 'Padres' : 'SDN', 'Phillies' : 'PHI', 'Pirates' : 'PIT', 
                 'Rangers' : 'TEX', 'Rays' : 'TBR', 'Red Sox' : 'BOS', 'Reds' : 'CIN', 
                 'Rockies' : 'COL', 'Royals' : 'KCR', 'Tigers' : 'DET', 'Twins' : 'MIN', 
                 'White Sox' : 'CHA', 'Yankees' : 'NYA'}

    # Alter it to include WAR and Change the actual data frame
    team_dict = {key : value + "_WAR" for key, value in team_dict.items()}
    position_war = position_war.rename(columns = team_dict)
    
    # Create stats for non-position/Year categories
    position_war['Med_WAR'] = position_war.drop(['yearID', 'Position'], axis = 1).median(axis = 1)
    position_war['Min_WAR'] = position_war.drop(['yearID', 'Position'], axis = 1).min(axis = 1)

    # Shrink to only the Year/Position/Median/Min WAR stats
    position_war_small = position_war[['yearID', 'Position', 'Med_WAR', 'Min_WAR']]
    
    # Merge the 2 data frames
    fa_w_team_war = pd.merge(fa_stats, position_war_small, how = 'inner',
                               on = ['Position', 'yearID'], )
    
    return fa_w_team_war

# Add payroll data inflation info and compute 2006 dollars
def addInflation(df_money, engine):
    '''Grab the payroll table and use it to add inflation to a table with money'''

    # Grab the table, grab just the relevent data, and set the Year index
    payrolls = pullFullTable('payrolls', engine)
    payrolls_2006 = payrolls[payrolls.Year >= 2006]
    payrolls_2006.set_index('Year', inplace=True)
    payrolls_2006.drop(['index'], axis = 1, inplace=True)

    # Compute the total and inflation factor, then grab just those in a DF
    payrolls_2006['Total'] = payrolls_2006.sum(axis = 1)
    payrolls_2006['Inflation_Factor'] = payrolls_2006['Total'].divide(payrolls_2006['Total'].min())
    inflation = payrolls_2006[['Inflation_Factor', 'Total']]

    # Fix the final year by projecting using mean percent change
    per_year = inflation.loc[2006:2016, 'Inflation_Factor'].pct_change().mean()
    inflation.loc[2017] = inflation.loc[2016] * (1 + per_year)

    # Bring back the year and merge with the other table
    inflation = inflation.reset_index()
    data_w_inflation = pd.merge(df_money, inflation, on = 'Year')

    # Add in the 2006 Dollars Column
    data_w_inflation['Dollars_2006'] = data_w_inflation['Dollars'].divide(data_w_inflation['Inflation_Factor'])

    return data_w_inflation

def main():

    '''If called from the terminal, compute and save the feature matrix'''

    # Connect to database
    engine = db_connect()    
    
    # Pull individual stats
    batting_df = createBattingTable(engine)
    pitching_df = createPitchingTable(engine)

    # Add free agent data
    all_batting = addFilterFreeAgents(batting_df, engine)
    only_pos = all_batting[all_batting.Position.isin(['SP','RP']) == False]
    pitching_fa = addFilterFreeAgents(pitching_df, engine)

    # Add Team WAR values
    pitching_war = allPositionWAR(pitching_fa, engine)
    position_war = allPositionWAR(only_pos, engine)

    # Add Inflation Data
    position_adjusted = addInflation(position_war, engine)
    pitching_adjusted = addInflation(pitching_war, engine)

    # Save them as a pickle file
    pitching_adjusted.to_pickle('pitching_data.pickle')
    position_adjusted.to_pickle('position_data.pickle')


if __name__ == '__main__':
    main()
