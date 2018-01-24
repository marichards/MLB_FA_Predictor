# Import important packages (mostly sklearn)
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import numpy as np
# Import LogisticRegression
from sklearn.linear_model import LogisticRegression
# Import xgboost
import xgboost as xgb
# Import RSME
from sklearn.metrics import mean_squared_error
# Import Classification metrics
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix

# Load the saved data
def loadAllData():
    '''Load both saved data frames for use in the models'''

    # Load pitchers
    with open('pitching_data.pickle', 'rb') as file:
        pitcher_all = pickle.load(file)

    # Load position players
    with open('position_data.pickle', 'rb') as file:
        position_all = pickle.load(file)

    return pitcher_all, position_all

# Define data preparation function
def prepareFreeAgentData(df):
    '''Given one of the 2 player data frames, prepare it for ML'''

    # Create position one-hot configuration
    df = pd.get_dummies(df, columns = ['Position'], prefix= ['Pos'])

    # Create Contract logical variable
    df['Contract'] = df.Dollars.notnull()

    return df

# Define the data splitting function
def splitDataByYear(df, year, player_type):

    # Break them into data frames and drop 2017 from training
    df_test = df[df.Year == year]
    df_train = df[(df.Year != year) & (df.Year != 2017)]

    # Determine the features
    if player_type == 'pitcher':
        features = ['Age', 'WAR_3', 'ERA', 'WHIP', 'K_9', 'HR_9', 'IPouts',
                    'W', 'SV', 'Med_WAR', 'Min_WAR', 'Pos_SP', 'Pos_RP']
    else:
        features = ['Age', 'WAR_3', 'G', 'OBP', 'SLG', 'HR', 'RBI', 'SB',
                    'Med_WAR', 'Min_WAR', 'Pos_C', 'Pos_1B', 'Pos_2B', 'Pos_3B',
                    'Pos_SS', 'Pos_LF', 'Pos_CF', 'Pos_RF', 'Pos_DH']

    # Create the 4 sets of data; X's are arrays, y's are DFs for now
    X_train = df_train[features].values
    X_test = df_test[features].values
    y_train = df_train[['Dollars_2006','Length','Contract']]
    y_test = df_test[['Dollars_2006','Length','Contract']]

    return X_train, y_train, X_test, y_test    

# Define the contract function (LogisticRegression)
def predictContract(X_train, y_train, X_test):

    # Grab the y values
    y_train_values = y_train['Contract'].values
    
    # Designate a logistic regression model
    logr = LogisticRegression()

    # Train the  model
    logr.fit(X_train, y_train_values)

    y_pred = logr.predict(X_test)    
    
    return logr, y_pred

# Define the length function (xgboost classification)
def predictLength(X_train, y_train, X_test):

    # Shorten training to only non-null dollars
    idx = y_train.Dollars_2006.notnull()
    y_train = y_train[idx]
    X_train = X_train[idx]
    
    # Grab the y values
    y_train_values = y_train['Length'].values
    
    # Designate a logistic regression model
    xgc = xgb.XGBClassifier()

    # Train the  model
    xgc.fit(X_train, y_train_values)

    y_pred = xgc.predict(X_test)    
    
    return xgc, y_pred

# Define the dollars function (xgboost regression)
def predictDollars(X_train, y_train, X_test):

    # Shorten training to only non-null dollars
    idx = y_train.Dollars_2006.notnull()
    y_train = y_train[idx]
    X_train = X_train[idx]

    # Grab the y values
    y_train_values = y_train['Dollars_2006'].values
    
    # Designate a logistic regression model
    xgr = xgb.XGBRegressor()

    # Train the  model
    xgr.fit(X_train, y_train_values)

    y_pred = xgr.predict(X_test)    
    
    return xgr, y_pred
