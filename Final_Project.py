import requests
import pymysql



conn = pymysql.connect(host='mysql.clarksonmsda.org', port=3306, user='palmerba', passwd='1Netherspell', db='palmerba') #setup our credentials
cur = conn.cursor()

print "Beginning Setup"
r = requests.get("https://www.pro-football-reference.com/years/2019/index.htm")

split = r.text.split("AFC Standings")

lines = split[3].split("\n")


print "Building Teams"
itr = 0
urls = []
teams = []
for line in lines:
    if itr > 16:
        break
    if "href" in line:
        url = "/teams/" + line.split("/teams/")[1].split("\"")[0]
        urls.append(url)

        team = line.split("/teams/")[1].split(">")[1].split("<")[0]
        winloss = line.split('win_loss_perc" >')[1].split("<")[0]
        teams.append((team, winloss))
        itr += 1
lines = split[3].split("NFC Standings")[3].split("\n")



itr = 0
temp_teams = []
for line in lines:
    if itr > 15:
        break
    if "href" in line:
        url = "/teams/" + line.split("/teams/")[1].split("\"")[0]
        if url not in urls:
            urls.append(url)

        team = line.split("/teams/")[1].split(">")[1].split("<")[0]
        winloss = line.split('win_loss_perc" >')[1].split("<")[0]

        teams.append((team, winloss))
        itr += 1


dropquery = '''DROP TABLE IF EXISTS palmerba_nfl_teams'''
createquery = '''CREATE TABLE IF NOT EXISTS `palmerba_nfl_teams` (
    `Team_Name` varchar(50) NOT NULL,
    `Record` decimal(4, 3) NOT NULL,
    PRIMARY KEY (`Team_Name`))
        ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=1;
        '''
cur.execute(dropquery)
cur.execute(createquery)

insertquery = ''' INSERT INTO palmerba_nfl_teams(`Team_Name`, `Record`) VALUES (%s,%s)'''

teams.pop(16)
cur.executemany(insertquery, teams)


print "Building Overall Stats"
games = []

overall_stats = []

dropquery = '''DROP TABLE IF EXISTS palmerba_nfl_team_stats'''
createquery = '''CREATE TABLE IF NOT EXISTS `palmerba_nfl_team_stats` (
    `id` int(10) NOT NULL AUTO_INCREMENT,
    `Points` int(3) NOT NULL,
    `Total_Yards` int(4) NOT NULL,
    `Offensive_Plays` int(4) NOT NULL,
    `Per_Off_Play` decimal(3, 2) NOT NULL,
    `Turnovers` int(2) NOT NULL,
    `Passing_Completions` int(4) NOT NULL,
    `Passing_Attempts` int(4) NOT NULL,
    `Pass_Yards` int(4) NOT NULL,
    `Pass_TD` int(2) NOT NULL,
    `Interceptions` int(2) NOT NULL,
    `Rush_Attempts` int(4) NOT NULL,
    `Rush_Yards` int(4) NOT NULL,
    `Rush_TD` int(2) NOT NULL,
    `Num_Penalities` int(3) NOT NULL,
    `Penalty_Yards` int(4) NOT NULL,
    `Points_Per_Drive` decimal(3, 2),
    `Offense` char(7) NOT NULL,
    `Team_Name` varchar(50) NOT NULL,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`Team_Name`) REFERENCES palmerba_nfl_teams(`Team_Name`))
        ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=1;
        '''

cur.execute(dropquery)
cur.execute(createquery)

insertquery = '''INSERT INTO palmerba_nfl_team_stats(`Points`, `Total_Yards`, `Offensive_Plays`, `Per_Off_Play`, `Turnovers`, `Passing_Completions`, `Passing_Attempts`,
    `Pass_Yards`, `Pass_TD`, `Interceptions`, `Rush_Attempts`, `Rush_Yards`, `Rush_TD`, `Num_Penalities`, `Penalty_Yards`, `Points_Per_Drive`, `Offense`, `Team_Name`)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '''

needed_rows = [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16, 17, 20, 21, 30]

def scrap_teams(url):
    offensive_stats = []
    defensive_stats = []
    r = requests.get("https://www.pro-football-reference.com" + url)
    split = r.text.split("Team Stats and Rankings")
    stat_lines = split[3].split("tbody")[1].split("data-stat")
    itr = 0
    i = 0
    for stat_line in stat_lines:
        if "td" in stat_line:
            if i in needed_rows and itr < 32:
                offensive_stats.append(stat_line.split(">")[1].split("<")[0])
            elif i in needed_rows:
                defensive_stats.append(stat_line.split(">")[1].split("<")[0])
            itr += 1
            i += 1
            if i >= 31 and itr < 32:
                offensive_stats.append("Offense")
                offensive_stats.append(teams[urls.index(url)][0])
                cur.execute(insertquery, offensive_stats)
                i = 0
        if itr > 62:
            defensive_stats.append("Defense")
            defensive_stats.append(teams[urls.index(url)][0])
            cur.execute(insertquery, defensive_stats)
            break

for url in urls:
    scrap_teams(url)


print "Building Game Stats"
dropquery = '''DROP TABLE IF EXISTS palmerba_nfl_game_offense'''
createquery = '''CREATE TABLE IF NOT EXISTS `palmerba_nfl_game_offense` (
    `id` int(10) NOT NULL AUTO_INCREMENT,
    `Team_Name` varchar(50) NOT NULL,
    `Rush_Attempts` int(2) NOT NULL,
    `Rush_Yards` int(3) NOT NULL,
    `Rush_TDs` int(1) NOT NULL,
    `Passing_Completions` int(2) NOT NULL,
    `Passing_Attempts` int(2) NOT NULL,
    `Pass_Yards` int(3) NOT NULL,
    `Pass_TDs` int(1) NOT NULL,
    `Interceptions` int(1) NOT NULL,
    `Sacks_Allowed` int(1) NOT NULL,
    `Sacked_Yards` int(2) NOT NULL,
    `Fumbles` int(1) NOT NULL,
    `Penalties` int(2) NOT NULL,
    `Penalty_Yards` int(3) NOT NULL,
    `Time_Of_Possession` varchar(10) NOT NULL,
    PRIMARY KEY(`id`),
    FOREIGN KEY (`Team_Name`) REFERENCES palmerba_nfl_teams(`id`))
        ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=1;'''

cur.execute(dropquery)
cur.execute(createquery)

dropquery = '''DROP TABLE IF EXISTS palmerba_nfl_game_defense'''
createquery = '''CREATE TABLE IF NOT EXISTS `palmerba_nfl_game_defense` (
    `id` int(10) NOT NULL AUTO_INCREMENT,
    `Team_Name` varchar(50) NOT NULL,
    `Rush_Attempts` int(2) NOT NULL,
    `Rush_Yards` int(3) NOT NULL,
    `Rush_TDs` int(1) NOT NULL,
    `Passing_Completions` int(2) NOT NULL,
    `Passing_Attempts` int(2) NOT NULL,
    `Pass_Yards` int(3) NOT NULL,
    `Pass_TDs` int(1) NOT NULL,
    `Interceptions` int(1) NOT NULL,
    `Sacks_Allowed` int(1) NOT NULL,
    `Sacked_Yards` int(2) NOT NULL,
    `Fumbles` int(1) NOT NULL,
    `Penalties` int(2) NOT NULL,
    `Penalty_Yards` int(3) NOT NULL,
    PRIMARY KEY(`id`),
    FOREIGN KEY (`Team_Name`) REFERENCES palmerba_nfl_teams(`Team_Name`))
        ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=1;'''

cur.execute(dropquery)
cur.execute(createquery)


game_urls = []
week = 15
i = 1
while i <= week:
    r = requests.get("https://www.pro-football-reference.com/years/2019/week_" + str(i) + ".htm")
    box_lines = r.text.split("game_summaries")[1].split("Players of the week")[0].split('\n')
    itr = 0
    team_itr = 0
    box_url = ''
    team_one = ''
    team_two = ''
    for box_line in box_lines:
        #print box_url.split("/boxscore/")[1].split('">')[0]
        if "href" in box_line and "/boxscores/" in box_line:
            box_url = box_line.split("/boxscores/")[1].split('">')[0]
            itr += 1
        elif "href" in box_line and "/teams/" in box_line:
            if team_itr == 0:
                team_one = box_line.split(">")[2].split("<")[0]
                if team_one == "Teams":
                    break
                team_itr += 1
            elif team_itr == 1:
                team_two = box_line.split(">")[2].split("<")[0]
                team_itr = 0
                if {"url": box_url, "team_one": team_one, "team_two": team_two} not in game_urls:
                    game_urls.append({"url": box_url, "team_one": team_one, "team_two": team_two})
                if itr > 15:
                    itr = 0
                    break
    i += 1


def build_stats(bulk_stats, team):
    temp = []
    temp.append(team)
    temp.append(bulk_stats[1].split("-")[0])
    temp.append(bulk_stats[1].split("-")[1])
    temp.append(bulk_stats[1].split("-")[2])
    temp.append(bulk_stats[2].split("-")[0])
    temp.append(bulk_stats[2].split("-")[1])
    temp.append(bulk_stats[2].split("-")[2])
    temp.append(bulk_stats[2].split("-")[3])
    temp.append(bulk_stats[2].split("-")[4])
    temp.append(bulk_stats[3].split("-")[0])
    temp.append(bulk_stats[3].split("-")[1])
    temp.append(bulk_stats[6].split("-")[0])
    temp.append(bulk_stats[8].split("-")[0])
    temp.append(bulk_stats[8].split("-")[1])
    temp.append(str(bulk_stats[11]))
    return temp

for game in game_urls:
    r = requests.get("https://www.pro-football-reference.com/boxscores/" + game["url"])
    stats_lines = r.text.split("\n")
    i = 0
    vistor_stats = []
    home_stats = []
    for stat_line in stats_lines:
        if "vis_stat" in stat_line and "<tr >" in stat_line:
            i += 1
            vistor_stats.append(stat_line.split('vis_stat" >')[1].split("<")[0])
            home_stats.append(stat_line.split('home_stat" >')[1].split("<")[0])
        elif "</table>" in stat_line and i != 0:
            break
    insertquery = ''' INSERT INTO palmerba_nfl_game_offense(`Team_Name`, `Rush_Attempts`, `Rush_Yards`, `Rush_TDs`, `Passing_Completions`, `Passing_Attempts`, `Pass_Yards`, `Pass_TDs`, `Interceptions`, `Sacks_Allowed`, `Sacked_Yards`, `Fumbles`, `Penalties`, `Penalty_Yards`, `Time_Of_Possession`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
    tokens = []

    temp_vis = build_stats(vistor_stats, game["team_one"])
    temp_home = build_stats(home_stats, game["team_two"])

    cur.execute(insertquery, (temp_vis[0],temp_vis[1],temp_vis[2],temp_vis[3],temp_vis[4],temp_vis[5],temp_vis[6],temp_vis[7],temp_vis[8],temp_vis[9],temp_vis[10],temp_vis[11],temp_vis[12],temp_vis[13],temp_vis[14]))
    cur.execute(insertquery, (temp_home[0],temp_home[1],temp_home[2],temp_home[3],temp_home[4],temp_home[5],temp_home[6],temp_home[7],temp_home[8],temp_home[9],temp_home[10],temp_home[11],temp_home[12],temp_home[13],temp_home[14]))

    insertquery = ''' INSERT INTO palmerba_nfl_game_defense(`Team_Name`, `Rush_Attempts`, `Rush_Yards`, `Rush_TDs`, `Passing_Completions`, `Passing_Attempts`, `Pass_Yards`, `Pass_TDs`, `Interceptions`, `Sacks_Allowed`, `Sacked_Yards`, `Fumbles`, `Penalties`, `Penalty_Yards`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
    tokens = []
    temp_vis[0] = game["team_two"]
    temp_home[0] = game["team_one"]

    cur.execute(insertquery, (temp_vis[0],temp_vis[1],temp_vis[2],temp_vis[3],temp_vis[4],temp_vis[5],temp_vis[6],temp_vis[7],temp_vis[8],temp_vis[9],temp_vis[10],temp_vis[11],temp_vis[12],temp_vis[13]))
    cur.execute(insertquery, (temp_home[0],temp_home[1],temp_home[2],temp_home[3],temp_home[4],temp_home[5],temp_home[6],temp_home[7],temp_home[8],temp_home[9],temp_home[10],temp_home[11],temp_home[12],temp_home[13]))


print "Complete"
