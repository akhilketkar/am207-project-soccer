__author__ = 'Akhil'
#For the following extensions:
#Baseball, Basketball, HomeEffects, Midweek

import urllib2
import pandas as pd
import numpy as np
import math
import os
import datetime
from fractions import Fraction


### GLOBAL VARIABLES ###
leagues = {"E0":"English Premier League","I1":"Seria A","SP1":"La Liga Premiera"}
base_link = "http://www.football-data.co.uk/mmz4281/"

team_lookup ={'Manchester United':'Man United',
              'Newcastle United':'Newcastle',
              'Queens Park Rangers':'QPR',
              'West Bromwich Albion':'West Brom',
              'West Ham United':'West Ham',
              'Manchester City':'Man City',
              'Tottenham Hotspur':'Tottenham'}

team_lookup_NBA ={'Los Angeles Lakers' : 'LAL',
                  'Chicago Bulls' : 'CHI',
                  'Charlotte Bobcats' : 'CHA',
                  'San Antonio Spurs' : 'SAS',
                  'Philadelphia 76ers' : 'PHI',
                  'Detroit Pistons' : 'DET',
                  'Boston Celtics' : 'BOS',
                  'Miami Heat' : 'MIA',
                  'Orlando Magic' : 'ORL',
                  'Portland Trail Blazers' : 'POR',
                  'Golden State Warriors' : 'GSW',
                  'New York Knicks' : 'NYK',
                  'Washington Wizards' : 'WAS',
                  'Utah Jazz' : 'UTA',
                  'Dallas Mavericks' : 'DAL',
                  'Minnesota Timberwolves' : 'MIN',
                  'Los Angeles Clippers' : 'LAC',
                  'Oklahoma City Thunder' : 'OKC',
                  'Milwaukee Bucks' : 'MIL',
                  'Memphis Grizzlies' : 'MEM',
                  'Toronto Raptors' : 'TOR',
                  'Houston Rockets' : 'HOU',
                  'Phoenix Suns' : 'PHX',
                  'Sacramento Kings' : 'SAC',
                  'New Orleans Pelicans' : 'NOP',
                  'Cleveland Cavaliers' : 'CLE',
                  'Atlanta Hawks' : 'ATL',
                  'Brooklyn Nets' : 'BKN',
                  'Indiana Pacers' : 'IND',
                  'Denver Nuggets' : 'DEN'}

def month2num(month):
    return{'Jan' : 1,
           'Feb' : 2,
           'Mar' : 3,
           'Apr' : 4,
           'May' : 5,
           'Jun' : 6,
           'Jul' : 7,
           'Aug' : 8,
           'Sep' : 9, 
           'Oct' : 10,
           'Nov' : 11,
           'Dec' : 12
           }[month]

def dayofweek(date_raw):
    day, month, year = (int(x) for x in date_raw.split('/'))
    date = datetime.date(year, month, day)
    return date.weekday() #0:Mon, 1:Tues, etc.

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


def clean_data(matchdata,add_outcomes=True, midweek=True, relegation=True, champ=True):
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
    
    df['home_goals'] = df['home_goals'].astype(int)
    df['away_goals'] = df['away_goals'].astype(int)
    
    if add_outcomes:
        df['home_outcome'] = df.apply(lambda x: 'win' if x['home_goals'] > x['away_goals']
                                 else 'loss' if x['home_goals'] < x['away_goals'] else 'draw',axis = 1)
        df['away_outcome'] = df.apply(lambda x: 'win' if x['home_goals'] < x['away_goals']
                                 else 'loss' if x['home_goals'] > x['away_goals'] else 'draw',axis = 1)

        df = df.join(pd.get_dummies(df.home_outcome, prefix='home'))
        df = df.join(pd.get_dummies(df.away_outcome, prefix='away'))
    
    if midweek:
        midweek=[]
        for i in matchdata.index:
            day=dayofweek(matchdata["Date"][i])
            if (day >=1) and (day<=3):
                marker=True
            else:
                marker=False
            midweek.append(marker)
        df["midweek"] = midweek 
    
    if relegation or champ:
        home_wins_total=[]
        home_draws_total=[]
        home_games_total=[]
        away_wins_total=[]
        away_draws_total=[]
        away_games_total=[]
        for i in df.index:
            #Cumulative wins - home
            home_wins = np.sum(df['home_win'][(df['i_home']==df['i_home'][i])&(df.index<i)])+ \
                        np.sum(df['away_win'][(df['i_away']==df['i_home'][i])&(df.index<i)])
            home_wins_total.append(home_wins)
            #Cumulative draws - home
            home_draws = np.sum(df['home_draw'][(df['i_home']==df['i_home'][i])&(df.index<i)])+ \
                         np.sum(df['away_draw'][(df['i_away']==df['i_home'][i])&(df.index<i)])
            home_draws_total.append(home_draws)
            #Cumulative games - home
            home_games = np.sum((df['i_home']==df['i_home'][i])&(df.index<i))+ \
                         np.sum((df['i_away']==df['i_home'][i])&(df.index<i))
            home_games_total.append(home_games)            
            #Cumulative wins - away
            away_wins = np.sum(df['home_win'][(df['i_home']==df['i_away'][i])&(df.index<i)])+ \
                        np.sum(df['away_win'][(df['i_away']==df['i_away'][i])&(df.index<i)])
            away_wins_total.append(away_wins)
            #Cumulative draws - away
            away_draws = np.sum(df['home_draw'][(df['i_home']==df['i_away'][i])&(df.index<i)])+ \
                         np.sum(df['away_draw'][(df['i_away']==df['i_away'][i])&(df.index<i)])
            away_draws_total.append(away_draws)   
            #Cumulative games - away
            away_games = np.sum((df['i_home']==df['i_away'][i])&(df.index<i))+ \
                         np.sum((df['i_away']==df['i_away'][i])&(df.index<i))
            away_games_total.append(away_games)         
            
        df['home_wins_total'] = home_wins_total
        df['home_draws_total'] = home_draws_total
        df['home_games_total'] = home_games_total
        df['away_wins_total'] = away_wins_total
        df['away_draws_total'] = away_draws_total
        df['away_games_total'] = away_games_total
        
        #Cumulative points
        home_points_total=[]
        away_points_total=[]
        winpts=3.
        drawpts=1.
        for i in df.index:
            home_points = winpts*df['home_wins_total'][i] + drawpts*df['home_draws_total'][i]
            away_points = winpts*df['away_wins_total'][i] + drawpts*df['away_draws_total'][i]
            home_points_total.append(home_points)
            away_points_total.append(away_points)
        df['home_points_total'] = home_points_total
        df['away_points_total'] = away_points_total
    return t,df

def get_baseball_data(year=2014):
    fname = "./Data/GL"  + str(year) + ".TXT"
    df = pd.read_csv(fname,header=None)[[0,3,6,9,10]]
    df = df.rename(columns = {0:"Date",3:"AwayTeam",6:"HomeTeam",9:"FTAG",10:"FTHG"})
    return df

def get_NBA_data(year):
    fname = "./Data/NBA" + str(year) + ".TXT" #Year format example (2013-2014 season) -> 1314
    df = pd.read_csv(fname,header=None)[[0,2,3,4,5]]
    df = df.rename(columns = {0:"Date_raw", 2:"AwayTeam_raw", 3:"FTAG" , 4:"HomeTeam_raw", 5:"FTHG"})
    df = df.ix[1:]
    
    HomeNames = df["HomeTeam_raw"].copy()
    AwayNames = df["AwayTeam_raw"].copy()
    home = []
    away = []
    for t1 in HomeNames:
        t1 = clean_team_name_NBA(t1)
        home.append(t1)
    for t2 in AwayNames:
        t2 = clean_team_name_NBA(t2)
        away.append(t2)  
    df["HomeTeam"] = home
    df["AwayTeam"] = away
    
    dates = []
    
    for entry in df.index:
        date_split = df["Date_raw"][entry].split(" ")
        date = str(date_split[3]) + str(month2num(str(date_split[1]))) + str(date_split[2])
        dates.append(date)
    df["Date"] = dates
    return df[["Date","AwayTeam","FTAG","HomeTeam","FTHG"]].copy()


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

def create_season_table_baseball(season,teams):
    """
    Create a summary dataframe with wins, losses, goals for, etc.

    """
    g = season.groupby('i_home')
    home = pd.DataFrame({'home_goals': g.home_goals.sum(),
                         'home_goals_against': g.away_goals.sum(),
                         'home_wins': g.home_win.sum(),
                         'home_losses': g.home_loss.sum()
                         })
    g = season.groupby('i_away')
    away = pd.DataFrame({'away_goals': g.away_goals.sum(),
                         'away_goals_against': g.home_goals.sum(),
                         'away_wins': g.away_win.sum(),
                         'away_losses': g.away_loss.sum()
                         })
    df = home.join(away)
    df['wins'] = df.home_wins + df.away_wins
    df['losses'] = df.home_losses + df.away_losses
    df['gf'] = df.home_goals + df.away_goals
    df['ga'] = df.home_goals_against + df.away_goals_against
    df['gd'] = df.gf - df.ga
    df = pd.merge(teams, df, left_on='i', right_index=True)
    df = df.sort_index(by='wins', ascending=False)
    df = df.reset_index()
    df['position'] = df.index + 1
    return df

def create_season_table_NBA(season, teams):
    """
    Create a summary dataframe with wins, losses, goals for, etc.

    """
    g = season.groupby('i_home')
    home = pd.DataFrame({'home_goals': g.home_goals.sum(),
                         'home_goals_against': g.away_goals.sum(),
                         'home_wins': g.home_win.sum(),
                         'home_losses': g.home_loss.sum()
                         })
    g = season.groupby('i_away')
    away = pd.DataFrame({'away_goals': g.away_goals.sum(),
                         'away_goals_against': g.home_goals.sum(),
                         'away_wins': g.away_win.sum(),
                         'away_losses': g.away_loss.sum()
                         })
    df = home.join(away)
    df['wins'] = df.home_wins + df.away_wins
    df['losses'] = df.home_losses + df.away_losses
    df['gf'] = df.home_goals + df.away_goals
    df['ga'] = df.home_goals_against + df.away_goals_against
    df['gd'] = df.gf - df.ga
    df = pd.merge(teams, df, left_on='i', right_index=True)
    df = df.sort_index(by='wins', ascending=False)
    df = df.reset_index()
    df['position'] = df.index + 1
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
        s = simulate_season_home(df,atts,defs,home,intercept)
        t = create_season_table(s,teams)
        t['iteration'] = i
        dfs.append(t)
    return pd.concat(dfs, ignore_index=True)

# summarize parameters for all teams
def create_team_param_table(teams,atts,defs,home,intercept=None):
    """
    Show the means of the posterior distributions for each team

    teams: a pandas dataframe containing teams
    atts: a pymc object representing the attacking strength of a team
    defs: a pymc object representing the defensive strength of a team
    home: a pymc object representing home field advantage
    intercept: a pymc object representing the mean goals (not present in some models)
    """
    if intercept is None:
        intercept_mean = 0
    else:
        intercept_mean = intercept.stats()['mean']

    df_avg = pd.DataFrame({'avg_att': atts.stats()['mean'],
                       'avg_def': defs.stats()['mean'],
                       'avg_home': home.stats()['mean'],
                       'avg_intercept': intercept_mean
                       })

    tpt = pd.merge(teams,df_avg,left_index=True,right_index=True)

    # # remove columns
    # tpt['i'] = None
    # tpt['class'] = None
    return tpt

def clean_team_name(t):
    if t in team_lookup.keys():
        t = team_lookup[t]
    else:
        t = t.replace(" City","")
    return t

def clean_team_name_NBA(t):
    if t in team_lookup_NBA.keys():
        t = team_lookup_NBA[t]
    return t

# get fixtures for league
def get_epl_fixtures():
    df = pd.read_table("./Data/epl_fixtures.txt",names=['Date','Time','Matchup'])
    df['Date'] = pd.to_datetime(df['Date'],dayfirst=True)
    df.drop('Time',axis=1,inplace=True)

    matches = df['Matchup'].copy()
    home = []
    away = []
    for m in matches:
        t1,t2 = m.split(" v ")
        t1 = clean_team_name(t1)
        t2 = clean_team_name(t2)
        home.append(t1)
        away.append(t2)

    df['home'] = home
    df['away'] = away
    return df[['Date','home','away']].copy()

def simulate_match(row, atts, defs, home, intercept=None, n=1000):

    output_row = pd.Series()

    home_team = row['home_i']
    away_team = row['away_i']

    # save in the output
    # output_row['date'] = row['Date']
    output_row['home_i'] = home_team
    output_row['away_i'] = away_team
    output_row['home'] = row['home']
    output_row['away'] = row['away']

    num_samples = atts.trace().shape[0]

    home_goals = np.zeros(n)
    away_goals = np.zeros(n)
    home_wins = 0.
    away_wins = 0.
    draws = 0.

    for i in range(n):
        draw = np.random.choice(num_samples)
        home_theta = np.exp(home.trace()[draw] +
                            intercept.trace()[draw,home_team] +
                            atts.trace()[draw,home_team] +
                            defs.trace()[draw,away_team])

        away_theta = np.exp(
                            intercept.trace()[draw,away_team] +
                            atts.trace()[draw,away_team] +
                            defs.trace()[draw,home_team])

        home_goals[i] = np.random.poisson(home_theta)
        away_goals[i] = np.random.poisson(away_theta)

        if home_goals[i] > away_goals[i]: home_wins += 1.
        elif home_goals[i] < away_goals[i]: away_wins += 1.
        else: draws += 1.

    output_row['p_home_win'] = home_wins*1./n
    output_row['p_away_win'] = away_wins*1./n
    output_row['p_draw'] = draws*1./n

    odds = lambda p: np.round(1./p,2)
    # odds = lambda p: str(Fraction(p*1./(1.-p)).limit_denominator(20).numerator) + "/" + \
    #                 str(Fraction(p*1./(1.-p)).limit_denominator(20).denominator)

    output_row['odds_home_win'] = odds(output_row['p_home_win'])
    output_row['odds_away_win'] = odds(output_row['p_away_win'])
    output_row['odds_draw'] = odds(output_row['p_draw'])


    output_row['mean_home_goals'] = np.mean(home_goals)
    output_row['mean_away_goals'] = np.mean(away_goals)


    output_row['l_home_goals'] = np.percentile(home_goals,2.5)
    output_row['h_home_goals'] = np.percentile(home_goals,97.5)
    output_row['l_away_goals'] = np.percentile(away_goals,2.5)
    output_row['h_away_goals'] = np.percentile(away_goals,97.5)

    return output_row

def simulate_matches(fixtures, atts, defs, home, intercept=None, n=1000):
    results = fixtures.apply(simulate_match,axis=1,args=(atts,defs,home,intercept,n))
    return results

# function to simulate a season
def simulate_season_home(df,atts,defs,home,intercept=None):
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
    home_draw = pd.DataFrame({'home':home.trace()[draw, :],})

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
    season = pd.merge(season,home_draw,left_on = 'i_home',right_index=True)

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
def simulate_seasons_home(df,teams,atts,defs,home,intercept=None,n=100):
    """
    Simulate a season once, using one random draw from the mcmc chain.

    df: a pandas dataframe containing the schedule for a season
    teams: a pandas dataframe containing teams
    atts: a pymc object representing the attacking strength of a team
    defs: a pymc object representing the defensive strength of a team
    home: a pymc object representing home field advantage, unique for each team
    intercept: a pymc object representing the mean goals (not present in some models)
    """
    dfs = []
    for i in range(n):
        s = simulate_season_home(df,atts,defs,home,intercept)
        t = create_season_table(s,teams)
        t['iteration'] = i
        dfs.append(t)
    return pd.concat(dfs, ignore_index=True)

def simulate_match_home(row, atts, defs, home, intercept=None, n=1000):

    output_row = pd.Series()

    home_team = row['home_i']
    away_team = row['away_i']

    # save in the output
    # output_row['date'] = row['Date']
    output_row['home_i'] = home_team
    output_row['away_i'] = away_team
    output_row['home'] = row['home']
    output_row['away'] = row['away']

    num_samples = atts.trace().shape[0]

    home_goals = np.zeros(n)
    away_goals = np.zeros(n)
    home_wins = 0.
    away_wins = 0.
    draws = 0.

    for i in range(n):
        draw = np.random.choice(num_samples)
        home_theta = np.exp(home.trace()[draw,home_team] +
                            intercept.trace()[draw,home_team] +
                            atts.trace()[draw,home_team] +
                            defs.trace()[draw,away_team])

        away_theta = np.exp(
                            intercept.trace()[draw,away_team] +
                            atts.trace()[draw,away_team] +
                            defs.trace()[draw,home_team])

        home_goals[i] = np.random.poisson(home_theta)
        away_goals[i] = np.random.poisson(away_theta)

        if home_goals[i] > away_goals[i]: home_wins += 1.
        elif home_goals[i] < away_goals[i]: away_wins += 1.
        else: draws += 1.

    output_row['p_home_win'] = home_wins*1./n
    output_row['p_away_win'] = away_wins*1./n
    output_row['p_draw'] = draws*1./n

    odds = lambda p: np.round(1./p,2)
    # odds = lambda p: str(Fraction(p*1./(1.-p)).limit_denominator(20).numerator) + "/" + \
    #                 str(Fraction(p*1./(1.-p)).limit_denominator(20).denominator)

    output_row['odds_home_win'] = odds(output_row['p_home_win'])
    output_row['odds_away_win'] = odds(output_row['p_away_win'])
    output_row['odds_draw'] = odds(output_row['p_draw'])


    output_row['mean_home_goals'] = np.mean(home_goals)
    output_row['mean_away_goals'] = np.mean(away_goals)


    output_row['l_home_goals'] = np.percentile(home_goals,2.5)
    output_row['h_home_goals'] = np.percentile(home_goals,97.5)
    output_row['l_away_goals'] = np.percentile(away_goals,2.5)
    output_row['h_away_goals'] = np.percentile(away_goals,97.5)

    return output_row

def simulate_matches_home(fixtures, atts, defs, home, intercept=None, n=1000):
    results = fixtures.apply(simulate_match_home,axis=1,args=(atts,defs,home,intercept,n))
    return results