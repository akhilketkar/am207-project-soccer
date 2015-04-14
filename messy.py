__author__ = 'Akhil'

import urllib2
import pandas as pd
import numpy as np
import math
import os


### GLOBAL VARIABLES ###
leagues = {"E0":"English Premier League","I1":"Seria A","SP1":"La Liga Premiera"}
base_link = "http://www.football-data.co.uk/mmz4281/"

def get_data(year,league="E0",base_link=base_link):
    """

    Get's data for a given league and year from the football data website
    base_link : base link for all data
    year : usually something like 1213 representing 2012-13
    league : code for the league, E0 is premier league, I1 is Italy and so on
    """

    if not os.path.isdir("./Data/"):
        os.mkdir("./Data/")

    final_link = base_link + year + "/" + league
    filename = "./Data/" + year + "_" + league + ".csv"

    datafile = urllib2.urlopen(final_link)
    output = open(filename,'wb')
    output.write(datafile.read())
    output.close()
    return pd.read_csv(filename)

def clean_data(matchdata,add_outcomes=True):
    """
    Returns a table of unique teams and a cleaned version of the match results

    matchdata : one row per match of results
    """
    # get teams
    t = matchdata.HomeTeam.unique()
    t = pd.DataFrame(t, columns=['team'])
    t['i'] = t.index
    # teams.head()

    # merge into original dataframe
    df = matchdata[["HomeTeam","AwayTeam","FTHG","FTAG"]].copy()
    df = pd.merge(df, t, left_on='HomeTeam', right_on='team', how='left')
    df = df.rename(columns = {'i': 'i_home'}).drop('team', 1)
    df = pd.merge(df, t, left_on='AwayTeam', right_on='team', how='left')
    df = df.rename(columns = {'i': 'i_away'}).drop('team', 1)
    df = df.rename(columns = {'FTHG': 'home_goals','FTAG': 'away_goals'})

    if add_outcomes:
        df['home_outcome'] = df.apply(lambda x: 'win' if x['home_goals'] > x['away_goals']
                                 else 'loss' if x['home_goals'] < x['away_goals'] else 'draw',axis = 1)
        df['away_outcome'] = df.apply(lambda x: 'win' if x['home_goals'] < x['away_goals']
                                 else 'loss' if x['home_goals'] > x['away_goals'] else 'draw',axis = 1)

        df = df.join(pd.get_dummies(df.home_outcome, prefix='home'))
        df = df.join(pd.get_dummies(df.away_outcome, prefix='away'))

    return t,df

def create_season_table(season,teams):
    """
    Create a summary dataframe with wins, losses, goals for, etc.

    """
    g = season.groupby('i_home')
    home = pd.DataFrame({'home_goals': g.home_goals.sum(),
                         'home_goals_against': g.away_goals.sum(),
                         'home_wins': g.home_win.sum(),
                         'home_draws': g.home_draw.sum(),
                         'home_losses': g.home_loss.sum()
                         })
    g = season.groupby('i_away')
    away = pd.DataFrame({'away_goals': g.away_goals.sum(),
                         'away_goals_against': g.home_goals.sum(),
                         'away_wins': g.away_win.sum(),
                         'away_draws': g.away_draw.sum(),
                         'away_losses': g.away_loss.sum()
                         })
    df = home.join(away)
    df['wins'] = df.home_wins + df.away_wins
    df['draws'] = df.home_draws + df.away_draws
    df['losses'] = df.home_losses + df.away_losses
    df['points'] = df.wins * 3 + df.draws
    df['gf'] = df.home_goals + df.away_goals
    df['ga'] = df.home_goals_against + df.away_goals_against
    df['gd'] = df.gf - df.ga
    df = pd.merge(teams, df, left_on='i', right_index=True)
    df = df.sort_index(by='points', ascending=False)
    df = df.reset_index()
    df['position'] = df.index + 1
    df['champion'] = (df.position == 1).astype(int)
    df['qualified_for_CL'] = (df.position < 5).astype(int)
    df['relegated'] = (df.position > 17).astype(int)
    return df

# function to simulate a season
def simulate_season(df,atts,defs,home,intercept=None):
    """
    Simulate a season once, using one random draw from the mcmc chain.

    df: a pandas dataframe containing the schedule for a season
    atts: a pymc object representing the attacking strength of a team
    defs: a pymc object representing the defensive strength of a team
    home: a pymc object representing home field advantage
    intercept: a pymc object representing the mean goals (not present in some models)
    """
    num_samples = atts.trace().shape[0]
    draw = np.random.randint(0, num_samples)
    atts_draw = pd.DataFrame({'att': atts.trace()[draw, :],})
    defs_draw = pd.DataFrame({'def': defs.trace()[draw, :],})
    home_draw = home.trace()[draw]

    if intercept is not None:
        id = intercept.trace()[draw]
        if id.shape != ():
            intercept_draw = pd.DataFrame({'intercept': intercept.trace()[draw],})
        else:
            intercept_draw = id

    season = df[['i_home','i_away']].copy()
    season = pd.merge(season, atts_draw, left_on='i_home', right_index=True)
    season = pd.merge(season, defs_draw, left_on='i_home', right_index=True)
    season = season.rename(columns = {'att': 'att_home', 'def': 'def_home'})
    season = pd.merge(season, atts_draw, left_on='i_away', right_index=True)
    season = pd.merge(season, defs_draw, left_on='i_away', right_index=True)
    season = season.rename(columns = {'att': 'att_away', 'def': 'def_away'})

    ## check if the model uses an intercept term
    if intercept is not None:

        ## check if it is one intercept term for all teams
        if id.shape == ():
            season['intercept_home'] = intercept_draw
            season['intercept_away'] = intercept_draw
        else:
            season = pd.merge(season,intercept_draw,left_on = 'i_home',right_index=True)
            season = season.rename(columns = {'intercept': 'intercept_home'})
            season = pd.merge(season,intercept_draw,left_on = 'i_away',right_index=True)
            season = season.rename(columns = {'intercept': 'intercept_away'})

    ## model does not use an intercept
    else:
        season['intercept_home'] = 0
        season['intercept_away'] = 0


    season['home'] = home_draw
    season['home_theta'] = season.apply(lambda x: math.exp(x['intercept_home'] +
                                                           x['home'] +
                                                           x['att_home'] +
                                                           x['def_away']), axis=1)
    season['away_theta'] = season.apply(lambda x: math.exp(x['intercept_away'] +
                                                           x['att_away'] +
                                                           x['def_home']), axis=1)
    season['home_goals'] = season.apply(lambda x: np.random.poisson(x['home_theta']), axis=1)
    season['away_goals'] = season.apply(lambda x: np.random.poisson(x['away_theta']), axis=1)
    season['home_outcome'] = season.apply(lambda x: 'win' if x['home_goals'] > x['away_goals'] else
                                                    'loss' if x['home_goals'] < x['away_goals'] else 'draw', axis=1)
    season['away_outcome'] = season.apply(lambda x: 'win' if x['home_goals'] < x['away_goals'] else
                                                    'loss' if x['home_goals'] > x['away_goals'] else 'draw', axis=1)
    season = season.join(pd.get_dummies(season.home_outcome, prefix='home'))
    season = season.join(pd.get_dummies(season.away_outcome, prefix='away'))
    return season

# simulate many seasons
def simulate_seasons(df,teams,atts,defs,home,intercept=None,n=100):
    """
    Simulate a season once, using one random draw from the mcmc chain.

    df: a pandas dataframe containing the schedule for a season
    teams: a pandas dataframe containing teams
    atts: a pymc object representing the attacking strength of a team
    defs: a pymc object representing the defensive strength of a team
    home: a pymc object representing home field advantage
    intercept: a pymc object representing the mean goals (not present in some models)
    """
    dfs = []
    for i in range(n):
        s = simulate_season(df,atts,defs,home,intercept)
        t = create_season_table(s,teams)
        t['iteration'] = i
        dfs.append(t)
    return pd.concat(dfs, ignore_index=True)
