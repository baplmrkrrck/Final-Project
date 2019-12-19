import requests
import pymysql
import scipy.stats as st
import numpy as np
import random
import matplotlib.pyplot as plt

conn = pymysql.connect(host='mysql.clarksonmsda.org', port=3306, user='palmerba', passwd='1Netherspell', db='palmerba') #setup our credentials
cur = conn.cursor()

r = requests.get("http://www.nfl.com/schedules")

lines = r.text.split("\n")

print "Getting Match Ups"
i = 0
match_ups = []
temp = ''
for line in lines:
    if "team-name away" in line:
        temp = line.split(">")[1].split("<")[0]
    elif "team-name home" in line:
        match_ups.append({"Away": temp, "Home": line.split(">")[1].split("<")[0]})
        temp = ''
        i += 1
        if i > 16:
            break

for match_up in match_ups:
    print match_up["Home"] + " vs " + match_up["Away"]
    
games_headers = ['Rush_Attempts', 'Rush_Yards', 'Rush_TDs', 'Passing_Completions', 'Passing_Attempts', 'Pass_Yards', 'Pass_TDs', 'Interceptions', 'Sacks_Allowed', 'Sacked_Yards', 'Fumbles', 'Penalties', 'Penalty_Yards']
games_select_query = '''SELECT * FROM (SELECT id, {field} FROM palmerba_nfl_game_offense as off WHERE Team_Name LIKE %s) AS Offense UNION (SELECT id, {field} FROM palmerba_nfl_game_defense as def WHERE Team_Name LIKE %s) '''
time_query = '''SELECT id, `Time_Of_Possession` FROM palmerba_nfl_game_offense WHERE Team_Name LIKE %s '''

def format_sql_return(fetched, index):
    temp = []
    for value in fetched:
        temp.append(value[index])
    return temp

print "Getting Stats"
team_stats = []
for match_up in match_ups:
    home_offensive_stats = []
    away_offensive_stats = []
    for header in games_headers:
        if header == "Time_Of_Possession":
            break
        query = games_select_query.format(field=header)
        cur.execute(query, ("%" + match_up["Home"] + "%", "%" + match_up["Away"]+ "%"))
        home_offensive_stats.append(format_sql_return(cur.fetchall(), 1))
        cur.execute(query, ("%" + match_up["Away"]+ "%", "%" + match_up["Home"] + "%"))
        away_offensive_stats.append(format_sql_return(cur.fetchall(), 1))


    cur.execute(time_query, ("%" + match_up["Home"] + "%"))
    home_offensive_stats.append(format_sql_return(cur.fetchall(), 1))
    cur.execute(time_query, ("%" + match_up["Away"]+ "%"))
    away_offensive_stats.append(format_sql_return(cur.fetchall(), 1))

    team_stats.append({"Team": match_up["Home"], "Stats": home_offensive_stats})
    team_stats.append({"Team": match_up["Away"], "Stats": away_offensive_stats})

print "Building means, totals, stds"
aggregated_team_stats = []
for team in team_stats:
    rush_averages = []
    rush_total_att = 0
    i = 0
    for rush_att in team["Stats"][0]:
        rush_total_att += rush_att
        rush_yards = team["Stats"][1][i]
        rush_averages.append(rush_yards/float(rush_att))
        i += 1

    pass_averages = []
    pass_total_comp = 0
    i = 0
    for pass_comp in team["Stats"][3]:
        pass_total_comp += pass_comp
        pass_averages.append(team["Stats"][5][i]/float(pass_comp))
        i += 1

    pass_total_att = 0
    int_averages = []
    sack_averages = []
    penalty_averages = []
    fumble_averages = []
    play_time = []
    i = 0
    for pass_att in team["Stats"][4]:
        int_averages.append(team["Stats"][7][i]/float(pass_att))
        sack_averages.append(team["Stats"][8][i]/float(pass_att))
        pass_total_att += pass_att
        total_plays = pass_att + team["Stats"][0][i]
        fumble_averages.append(team["Stats"][10][i]/float(total_plays))
        penalty_averages.append(team["Stats"][11][i]/float(total_plays))
        if i < len(team["Stats"][13]):
            t_o_p = int(team["Stats"][13][i][0:2])*60 + int(team["Stats"][13][i][3:5])
            play_time.append(t_o_p/float(total_plays))
        i += 1

    sack_yards_average = []
    i = 0
    for sacks in team["Stats"][8]:
        if int(sacks) != 0:
            sack_yards_average.append(team["Stats"][9][i]/float(sacks))
        else:
            sack_averages.append(0)

    team_stats_all = {"Team": team["Team"], "Rush_Stats": {"Mean_Rush": np.mean(rush_averages), "Std_Rush": np.std(rush_averages), "Rush_Attempts": rush_total_att}, "Passing_Stats": {"Mean_Pass": np.mean(pass_averages), "Std_Pass": np.std(pass_averages), "Passing_Completions": pass_total_comp, "Passing_Attempts": pass_total_att, "Mean_Int": np.mean(int_averages), "Std_Int": np.std(int_averages), "Mean_Sack": np.mean(sack_averages), "Std_Sack": np.std(sack_averages), "Mean_Sack_Yards": np.mean(sack_yards_average), "Std_Sack_Yards": np.mean(sack_yards_average)}, "Per_Play_Stats": {"Mean_Fumbles": np.mean(fumble_averages), "Std_Fumbles": np.std(fumble_averages), "Mean_TOP": np.mean(play_time), "Std_TOP": np.std(play_time), "Rush_To_Pass": rush_total_att/ float(total_plays)}}

    aggregated_team_stats.append(team_stats_all)

print "Begin Simulations"



def get_team_stats(all_stats, team):
    for stats in all_stats:
        if stats["Team"] == team:
            return stats

def sim_play(team_stats, yardline):
    has_poss = True
    down = 1
    first_down_line = yardline + 10
    drive_time = 0
    while has_poss:
        if down >= 4:
            if yardline > 60:
                return "Score@3@Kick@" + str(drive_time)
            else:
                return "Turnover@25@Down@" + str(drive_time)
        run_pass = random.random()
        if run_pass <= team_stats["Per_Play_Stats"]["Rush_To_Pass"]:
            yardline += random.normalvariate(team_stats["Rush_Stats"]["Mean_Rush"], team_stats["Rush_Stats"]["Std_Rush"])
            drive_time += random.normalvariate(team_stats["Per_Play_Stats"]["Mean_TOP"], team_stats["Per_Play_Stats"]["Std_TOP"])
            if random.normalvariate(team_stats["Per_Play_Stats"]["Mean_Fumbles"], team_stats["Per_Play_Stats"]["Std_Fumbles"]) > 1:
                return "Turnover@" + str(yardline)+ "@Fumble@" + str(drive_time)
            else:
                down += 1
                if yardline >= 100:
                    return "Score@7@Rush@" + str(drive_time)
                elif yardline >= first_down_line:
                    down = 1
                    first_down_line = yardline + 10
        else:
            if random.normalvariate(team_stats["Passing_Stats"]["Mean_Sack"], team_stats["Passing_Stats"]["Std_Sack"]) > 1:
                yardline -= random.normalvariate(team_stats["Passing_Stats"]["Mean_Sack_Yards"], team_stats["Passing_Stats"]["Std_Sack_Yards"])
                drive_time += random.normalvariate(team_stats["Per_Play_Stats"]["Mean_TOP"], team_stats["Per_Play_Stats"]["Std_TOP"])
                if random.normalvariate(team_stats["Per_Play_Stats"]["Mean_Fumbles"], team_stats["Per_Play_Stats"]["Std_Fumbles"]) > 1:
                    return "Turnover@" + str(yardline) + "@Fumble@" + str(drive_time)
                down += 1
            elif random.random() > team_stats["Passing_Stats"]["Passing_Completions"]/float(team_stats["Passing_Stats"]["Passing_Attempts"]):
                drive_time += 5
                down += 1
            elif random.normalvariate(team_stats["Passing_Stats"]["Mean_Int"], team_stats["Passing_Stats"]["Std_Int"]) > 1:
                return "Turnover@" + str(yardline) + "@Interception@" + str(drive_time)
            else:
                yardline += random.normalvariate(team_stats["Passing_Stats"]["Mean_Pass"], team_stats["Passing_Stats"]["Std_Pass"])
                drive_time += random.normalvariate(team_stats["Per_Play_Stats"]["Mean_TOP"], team_stats["Per_Play_Stats"]["Std_TOP"])
                if random.normalvariate(team_stats["Per_Play_Stats"]["Mean_Fumbles"], team_stats["Per_Play_Stats"]["Std_Fumbles"]) > 1:
                    return "Turnover@" + str(yardline) + "@Fumble@" + str(drive_time)
                else:
                    down += 1
                    if yardline >= 100:
                        return "Score@7@Pass@" + str(drive_time)
                    elif yardline >= first_down_line:
                        down = 1
                        first_down_line = yardline + 10

num_of_sim = 20
for match_up in match_ups:
    home = get_team_stats(aggregated_team_stats, match_up["Home"])
    away = get_team_stats(aggregated_team_stats, match_up["Away"])
    i = 0
    home_score = []
    away_score = []
    for i in range(num_of_sim):
        game_time = 0
        kick_off = random.random()

        score = { match_up["Home"]: 0, match_up["Away"]: 0}
        curr_possession = match_up["Home"]
        if kick_off > .5:
            curr_possession = match_up["Away"]
        yardline = 25
        while game_time <= 3600:
            if curr_possession == match_up["Home"]:
                possession_outcome = sim_play(home, yardline)
                split = possession_outcome.split("@")
                if split[0] == "Turnover":
                    if int(split[1]) >= 100:
                        yardline = 25
                        game_time += float(split[3])
                    else:
                        yardline = int(split[1])
                        game_time += float(split[3])
                else:
                    score[curr_possession] += int(split[1])
                    yardline = 25
                    game_time += float(split[3])
                curr_possession = match_up["Away"]
            else:
                possession_outcome = sim_play(away, yardline)
                split = possession_outcome.split("@")
                if split[0] == "Turnover":
                    if int(split[1]) >= 100:
                        yardline = 25
                        game_time += float(split[3])
                    else:
                        yardline = int(split[1])
                        game_time += float(split[3])
                else:
                    score[curr_possession] += int(split[1])
                    yardline = 25
                    game_time += float(split[3])
                curr_possession = match_up["Home"]
        home_score.append(score[match_up["Home"]])
        away_score.append(score[match_up["Away"]])
        i += 1
    plt.plot(home_score, away_score, 'bo')

    plt.xlabel(match_up["Home"])
    plt.ylabel(match_up["Away"])

    plt.plot(np.arange(40), np.arange(40), 'b')
    #plt.show()
    plt.savefig("Graphs/Home:" + match_up["Home"] + " Away:" + match_up["Away"]+".png")
    plt.clf()


print "Done!"
