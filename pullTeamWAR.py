# Pull Team WAR apart from AWS
from dataScraping import *
import pandas as pd

# Grab both pitcher and position player team WAR data
pitcher_war = pd.concat([getTeamPitcherWar(year) for year in range(2006,2018)])

positions = ['c', '1b', '2b', '3b', 'ss', 'lf', 'rf', 'cf', 'dh']
position_war = pd.concat([getTeamPosWar(position, year) for position in positions for year in range(2006,2018)])

# Save them to pickle files
pitcher_war.to_pickle('pitcher_war.pickle')
position_war.to_pickle('position_war.pickle')
