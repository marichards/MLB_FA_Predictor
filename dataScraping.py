# Load necessary packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup, Comment

# Function for getting payroll data
def scrapePayrollData(year):
    '''Given a starting year, get payroll data for that year to present'''

    # Specify the url and get the data
    url = "http://www.thebaseballcube.com/extras/payrolls/"
    results = requests.get(url).text
    payroll_soup = BeautifulSoup(results, 'html.parser')
    just_table = payroll_soup.find_all('table')[1]
    
    # Get data for all teams
    team_dict = {}
    for entry in just_table.contents[1:]:
        team = entry.find_all('td')[0].text
        post_2002 = [float(line.text) for line in entry.find_all('a')]
        pre_2003 = [float(line.text.split(' - ')[1]) for line in entry.find_all('td')[-1].find_all('option')]
        
        # Shorten the pre-2003 to just 5 years, back to 1998        
        all_salaries = post_2002 + pre_2003[0:5]
        all_salaries.reverse()
        team_dict[team] = all_salaries
        
    # Make it a dataframe
    payroll_df = pd.DataFrame(team_dict)
    payroll_df['Year'] = list(range(1998, 2018))
    payroll_df.set_index('Year', inplace=True)

    # Pull out just my years
    payroll_my_year = payroll_df.loc[year:]
    
    return payroll_my_year

# Function for getting one year of BB-ref FA data
def compileFAsForYear(year):
    
    # Build the URL given the year
    url = "https://www.baseball-reference.com/leagues/MLB/{}-free-agents.shtml".format(year)
    
    # Get the full page and then narrow down to the table
    results = requests.get(url).text
    free_agent_soup = BeautifulSoup(results, 'html.parser')
    fa_table = free_agent_soup.find(id = 'all_fa_signings').find(id = 'fa_signings').find('tbody')
    
    # Compile the players and destinations as list comprehensions
    fa_players = [player_info.find('td', {"data-stat":"player"}).text.strip() for player_info in fa_table.find_all('tr')]
    fa_destinations = [player_info.find('td',{"data-stat":"to_team_ID"}).text.strip() for player_info in fa_table.find_all('tr')]
    fa_origins = [player_info.find('td', {"data-stat":"from_team_ID"}).text.strip() for player_info in fa_table.find_all('tr')]
    fa_war = [player_info.find('td', {"data-stat":"WAR"}).text.strip() for player_info in fa_table.find_all('tr')]
    fa_age = [int(player_info.find('td', {"data-stat":"age"}).text.strip()) for player_info in fa_table.find_all('tr')]


    # Grab inner tables
    bat_soup = BeautifulSoup(free_agent_soup.find(id = 'all_fa_batting').findAll(text=lambda text:isinstance(text, Comment))[0], 'html.parser')
    bat_table = bat_soup.find('tbody')
    bat_players = [player_info.find('td', {"data-stat":"player"}).text.strip() for player_info in bat_table.find_all('tr')]
    bat_war = [player_info.find('td', {"data-stat":"WAR"}).text.strip() for player_info in bat_table.find_all('tr')]
    bat_age = [int(player_info.find('td', {"data-stat":"age"}).text.strip()) for player_info in bat_table.find_all('tr')]
    
    pitch_soup = BeautifulSoup(free_agent_soup.find(id = 'all_fa_pitching').findAll(text=lambda text:isinstance(text, Comment))[0], 'html.parser')
    pitch_table = pitch_soup.find('tbody')
    pitch_players = [player_info.find('td', {"data-stat":"player"}).text.strip() for player_info in pitch_table.find_all('tr')]
    pitch_war = [player_info.find('td', {"data-stat":"WAR"}).text.strip() for player_info in pitch_table.find_all('tr')]
    pitch_age = [int(player_info.find('td', {"data-stat":"age"}).text.strip()) for player_info in pitch_table.find_all('tr')]

    
    # Make a data frame from the lists
    fa_dict = {"Full_Name" : fa_players + bat_players + pitch_players,              
               "Age" : fa_age + bat_age + pitch_age,                         
               "WAR_3" : fa_war + bat_war + pitch_war
    }
    fa_df = pd.DataFrame(fa_dict)
    
    # Split the "Full Name" into First and Last
    ## Note: This also gets rid of the annoying 'HOF' tag that comes third
    fa_df['nameFirst'] = fa_df.Full_Name.str.split(" ").str.get(0)
    fa_df['nameLast'] = fa_df.Full_Name.str.split(" ").str.get(1)
    
    # Broadcast the year, which is for the data + 1
    fa_df['Year'] = year#pd.to_datetime(year, format = '%Y')
    
    # Convert WAR to a numeric and fill missing values with "0"
    fa_df['WAR_3'] = pd.to_numeric(fa_df['WAR_3'], errors='coerce')
    fa_df['WAR_3'] = fa_df['WAR_3'].fillna(0)
    
    return fa_df

# Function for getting ESPN FA data for 1 year
def assembleFAContractsForYear(year):
    '''Go fetch the correct FA contract data from ESPN for the given year'''
    
    # Assemble the URL and grab the data, isolating the table
    url = "http://www.espn.com/mlb/freeagents/_/year/{}".format(year)
    fa_data = requests.get(url).text
    free_agent_soup = BeautifulSoup(fa_data, 'html.parser')
    fa_table = free_agent_soup.find('table')
    
    # Grab the correct info with list comprehensions
    fa_names = [row.find_all('td')[0].text for row in fa_table.find_all('tr')[2:]]
    fa_positions = [row.find_all('td')[1].text for row in fa_table.find_all('tr')[2:]]
    fa_years = [row.find_all('td')[6].text for row in fa_table.find_all('tr')[2:]]
    fa_dollars = [row.find_all('td')[8].text for row in fa_table.find_all('tr')[2:]]
    
    # Assemble a data frame
    fa_full_data = pd.DataFrame({'Name' : fa_names,
                                 'Position' : fa_positions,
                                 'Length' : fa_years,
                                 'Dollars' : fa_dollars,
                                 'Year' : year})
    
    # Split the "Full Name" into First and Last
    ## Note: This also gets rid of the annoying 'HOF' tag that comes third
    fa_full_data['nameFirst'] = fa_full_data.Name.str.split(" ").str.get(0)
    fa_full_data['nameLast'] = fa_full_data.Name.str.split(" ").str.get(1)
    
    # Return the Data Frame
    return fa_full_data

# Function for getting + combining all FA data (ESPN + BB-ref)
def getAllFAData(year_list):

    # Get BB-ref data for all years in the list and make one DF
    full_fa_outcomes = pd.concat([compileFAsForYear(year) for year in year_list])
    
    # Get ESPN data for all years in the list and make one DF
    all_fa_contracts = pd.concat([assembleFAContractsForYear(year) for year in range(2006,2018)])

    # Remove 'YRS' rows and Length = "--" values with 0, then convert to numeric
    all_fa_contracts_real = all_fa_contracts[all_fa_contracts.Length != 'YRS']
    all_fa_contracts_real.Length.replace({"" : 0}, inplace=True)
    all_fa_contracts_real['Length'] = pd.to_numeric(all_fa_contracts_real['Length'])
    
    # Replace "--" and "Minor Lg" with "0" in Dollars, then convert to money
    all_fa_contracts_real['Dollars'].replace({'--' : 0, 'Minor Lg':0}, inplace = True)
    all_fa_contracts_real['Dollars'] = pd.to_numeric(all_fa_contracts_real['Dollars'].str.strip('$').str.replace(',',''))    
    
    # Join to full free agent outcomes 
    all_fa_data = pd.merge(full_fa_outcomes, all_fa_contracts_real,
                           on = ['nameFirst', 'nameLast', 'Year'])

    # Return the full data
    return all_fa_data

# Function for getting all Fangraphs Team WAR for each position
def getTeamPosWar(position, year):
    
    # Create the URL
    url = ("http://www.fangraphs.com/leaders.aspx?pos={}"
           "&stats=bat&lg=all&qual=0&type=8&season={}&month=0&season1={}"
           "&ind=0&team=0,ts&rost=0&age=0&filter=&players=0").format(position, year, year)

    # Open the page and grab the soup
    results = requests.get(url).text
    team_war_soup = BeautifulSoup(results, 'html.parser')
    
    # Turn the soup into just the table for convenience
    stat_table = team_war_soup.find('table', {'class' : 'rgMasterTable'}).find('tbody').find_all('tr')
    
    # Make a dictionary with team as key and WAR as value
    team_war_dict = {team_row.find('a').text : [float(team_row.find_all('td')[-1].text)] for team_row in stat_table}
    
    # Make the dictionary into a data frame (1 row), add year and position
    team_war_df = pd.DataFrame(team_war_dict)
    team_war_df['Position'] = position.upper()
    team_war_df['Year'] = year #pd.to_datetime(year, format = '%Y')
    
    # Catch any columns that aren't the right names and change them
    # Devil Rays --> Rays
    # Expos --> Nationals
    team_war_df = team_war_df.rename(columns={"Devil Rays": "Rays", 
                                              "Expos": "Nationals"}
                                    )
    
    return team_war_df

# Function for getting all Team WAR for pitchers
# Make a similar function for pitchers
def getTeamPitcherWar(year):
    '''Define the starter and reliever data separately, then get both and combine them'''
    
    # Create the URL
    starter_url = ("http://www.fangraphs.com/leaders.aspx?pos=all&stats=sta&lg=all&qual=0"
                   "&type=8&season={}&month=0&season1={}"
                   "&ind=0&team=0,ts&rost=0&age=0&filter=&players=0").format(year, year)
    
    reliever_url = ("http://www.fangraphs.com/leaders.aspx?pos=all&stats=rel&lg=all&qual=0"
                    "&type=8&season={}&month=0&season1={}"
                    "&ind=0&team=0,ts&rost=0&age=0&filter=&players=0").format(year, year)

    # Create another function that opens a given URL and fills in the correct position
    def getWARForRole(url, position):
    
        # Open the page and grab the soup
        results = requests.get(url).text
        team_war_soup = BeautifulSoup(results, 'html.parser')
    
        # Turn the soup into just the table for convenience
        stat_table = team_war_soup.find('table', {'class' : 'rgMasterTable'}).find('tbody').find_all('tr')
    
        # Make a dictionary with team as key and WAR as value
        role_war_dict = {team_row.find('a').text : [float(team_row.find_all('td')[-1].text)] for team_row in stat_table}
    
        # Make the dictionary into a data frame (1 row), add year and position
        role_war_df = pd.DataFrame(role_war_dict)
        role_war_df['Position'] = position.upper()
    
        return role_war_df
    
    # Use it to get the team pitcher WAR values for relievers and starters
    starter_df = getWARForRole(starter_url, 'sp')
    reliever_df = getWARForRole(reliever_url, 'rp')
    
    # Combine them and add the year
    all_pitching_war = pd.concat([starter_df, reliever_df])
    
    all_pitching_war['Year'] = year #pd.to_datetime(year, format = '%Y')
    
    # Catch any columns that aren't the right names and change them
    # Devil Rays --> Rays
    # Expos --> Nationals
    all_pitching_war = all_pitching_war.rename(columns={"Devil Rays": "Rays", 
                                                        "Expos": "Nationals"}
                                              )
    
    return all_pitching_war


