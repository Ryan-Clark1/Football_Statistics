from bs4 import BeautifulSoup
import pandas as pd
import requests
from colorama import Fore, Back
import openpyxl
from snap_count import snap_count
from datetime import datetime
from tqdm import tqdm
# Building date range #
Years = [2020]
year_range = input("How many years would you like to search? ")
z = 0
while z < int(year_range):
    if z == 0:
        z += 1
    else:
        new_year = Years[0] - z
        Years.append(new_year)
        z += 1
Weeks = []
i = 18
x = 1
while x < i:
    Weeks.append(x)
    x += 1

# Laying framework for link collector shells #
link_list_sb = []
link_list_gl = []

# Looping through date range to collect all scoreboard links #
for year in Years:
    for week in Weeks:
        link = 'https://www.pro-football-reference.com/years/'+str(year)+'/week_'+str(week)+'.htm'
        link_list_sb.append(link)
        print(Fore.RED + 'Scoreboard Links Collected '+str(len(link_list_sb))+ ' of ' + str(len(Weeks)*len(Years)) + ' games collected --- '+ str(len(link_list_sb)/(len(Weeks)*len(Years))*100)+ '%')
print(Back.LIGHTGREEN_EX + Fore.BLACK + 'DONE GETTING SCOREBOARD LINKS')

# Using links of scoreboards in date range to collect game log links #
for l in tqdm(link_list_sb):
    html = requests.get(l).content
    soup = BeautifulSoup(html, 'html.parser')
    ob = soup.find('div', class_='game_summaries')
    links = ob.find_all('td', class_='right gamelink')
    for http in links:
        gl_link = 'https://www.pro-football-reference.com'+http.find('a').get('href')
        link_list_gl.append(gl_link)
    print(Back.RESET + Fore.RESET + Fore.YELLOW + 'Game Log Links Collected ' + str(link_list_sb.index(l)) + " of: " + str(len(link_list_sb)) + " games collected --- "+ str(link_list_sb.index(l)/len(link_list_sb)*100)+ "%")
print(Back.LIGHTGREEN_EX + Fore.BLACK + 'DONE GETTING GAMELOG LINKS')

# Using first link to set framework for tables -- Creating headers #
tlink = link_list_gl[0]
html = requests.get(tlink).content
soup = BeautifulSoup(html, 'html.parser')
t2 = soup.find('div', class_='content_grid')
tables = soup.find_all('table')
offensive_stats = soup.find('table', id='player_offense')
headers_html = offensive_stats.find_all('th')
headers_offensive_stats = []
for header in headers_html:
    headers_offensive_stats.append(header.get_text())
for header in range(8,16,1):
    headers_offensive_stats[header] = 'Pass '+headers_offensive_stats[header]
for header in range(16,20,1):
    headers_offensive_stats[header] = 'Rushing '+headers_offensive_stats[header]
for header in range(20,25,1):
    headers_offensive_stats[header] = 'Receiving '+headers_offensive_stats[header]
headers_offensive_stats = headers_offensive_stats[5:27]
snap_headers = ['Player', 'Position', 'Snaps', 'Snap_Percentage']
print("Headers established")
details_grouped = []
stats_grouped = []
snap_data = []
snap_headers = ['Player', 'Position', 'Snaps', 'Snap_Percentage']
pbp_master_list = []
pbp_headers = ['quarter', 'time_left', 'down', 'to_go', 'field_pos', 'player', 'second_player', 'result', 'away_score', 'home_score',
               'expected_points_before', 'expected_points_after', 'Game_ID']
# Begin of looping through game log links #
## Segmented into html sections of website, one load per link cuts down on search effort by 75% ##
for tlink in link_list_gl:
    start_clock = datetime.now()
    html = requests.get(tlink).content
    soup = BeautifulSoup(html, 'html.parser')
# Getting game detail data, date, time, stadium, creation of Primary Key for later DB use #
    t1 = soup.find('div', class_='scorebox')
    game_details = t1.find('div', class_='scorebox_meta')
    temp_hold = []
    for point in game_details:
        try:
            temp_hold.append(point.get_text())
        except:
            pass
    Date = temp_hold[0]
    Start_Time = temp_hold[1]
    Stadium = temp_hold[2]
    Attendance = temp_hold[3]
    Game_ID = Date + Stadium
    game_info = [Date, Start_Time, Stadium, Attendance, Game_ID]
    details_grouped.append(game_info)
# Getting player stats to fill header framework #
    offensive_stats = soup.find('table', id='player_offense')
    datarows_html = offensive_stats.find_all('tr')
    temp_list = []
    for point in datarows_html:
        temp_list.append(point)
# filter out unwanted data
    for data in temp_list:
        if len(data) >30:
            pass
        elif len(data) <12:
            pass
        else:
            test_list = []
            for point in data:
                test_list.append(point.get_text())
            test_list.append(Game_ID)
            test_list.append(Date)
            stats_grouped.append(test_list)
# Getting snap count data #
    t3 = soup.find('div', id='all_home_snap_counts')
    t4 = soup.find('div', id='all_vis_snap_counts')
    temp_list = []
    temp_list2 = []
    for line in t3:
        temp_list.append(line)
    for line in t4:
        temp_list2.append(line)
    temp_list.remove('\n')
    test = temp_list[3].split('tr')
    for line in test:
        try:
            s = line.index('00.htm') + 8
            e = line.index('</a')
            player = line[s:e].rstrip()
            target = line[e:]
            s = target.index('data-stat="pos" >') + 17
            e = target.index('</td>')
            position = target[s:e]
            target = target[e + 1:]
            s = target.index('data-stat="offense"') + len('data-stat="offense"') + 1
            e = target.index('</td>')
            osnaps = target[s:e]
            osnaps = osnaps.replace('>', '')
            osnaps.rstrip()
            target = target[e + 1:]
            s = target.index('data-stat="off_pct') + len('data-stat="off_pct') + 1
            e = target.index('</td>')
            snap_percent = target[s:e]
            snap_percent = snap_percent.replace('>', '')
            snap_percent.rstrip()
            # print('player is: '+ player + ', position is: '+ position + ' with: ' + str(osnaps) + ' snaps on offense. Equating to: '+ str(snap_percent)+' of plays')
            snap_d = [player, position, osnaps, snap_percent, Game_ID]
            snap_data.append(snap_d)
        except:
            pass
    temp_list2.remove('\n')
    test2 = temp_list2[3].split('tr')
    for line in test2:
        try:
            s = line.index('00.htm') + 8
            e = line.index('</a')
            player = line[s:e].rstrip()
            target = line[e:]
            s = target.index('data-stat="pos" >') + 17
            e = target.index('</td>')
            position = target[s:e]
            target = target[e + 1:]
            s = target.index('data-stat="offense"') + len('data-stat="offense"') + 1
            e = target.index('</td>')
            osnaps = target[s:e]
            osnaps = osnaps.replace('>', '')
            osnaps.rstrip()
            target = target[e + 1:]
            s = target.index('data-stat="off_pct') + len('data-stat="off_pct') + 1
            e = target.index('</td>')
            snap_percent = target[s:e]
            snap_percent = snap_percent.replace('>', '')
            snap_percent.rstrip()
            # print('player is: '+ player + ', position is: '+ position + ' with: ' + str(osnaps) + ' snaps on offense. Equating to: '+ str(snap_percent)+' of plays')
            snap_d = [player, position, osnaps, snap_percent, Game_ID]
            snap_data.append(snap_d)
        except:
            pass
# Getting play by play data #
    t6 = soup.find('div', id='all_pbp')
    temp_list = []
    for x in t6:
        temp_list.append(x)
    test_list = temp_list[4].split("\n")
    for x in test_list:
        try:
            target = x
            s = target.index('quarter') + 10
            e = target.index('</th>')
            quarter = target[s:e]
            target = target[s:]
            s = target.index('.000">') + 6
            e = target.index('</a>')
            time_left = target[s:e]
            target = target[s:]
            s = target.index('data-stat="down"') + len('data-stat="down"') + 2
            e = target.index('data-stat="down"') + len('data-stat="down"') + 3
            down = target[s:e]
            target = target[s:]
            s = target.index('"yds_to_go"') + len('"yds_to_go"') + 2
            e = target[s:].index('</td>') + s
            to_go = target[s:e]
            target = target[s:]
            s = target.index('csk=') + len('csk=') + 1
            e = target[s:].index('" ') + s
            e2 = target[s:].index('</td>') + s
            field_pos = target[e + 3:e2]
            target = target[s:]
            s = target.index('00.htm"') + len('00.htm"') + 1
            e = target[s:].index('</a>') + s
            player = target[s:e]
            target = target[s:]
            s = target.index('</a>') + len('</a>') + 1
            if target[s:].index('<a href') > 0:
                e = target[s:].index('<a href') + s
                result = target[s:e]
                target = target[s:]
                s = target.index('00.htm') + len('00.htm') + 2
                e = target.index('</a>')
                second_player = target[s:e]
            else:
                e = target[s:].index('</td>') + s
                result = target[s:e]
                second_player = 'none'
            target = target[s:]
            s = target.index('score_aw"') + len('score_aw"') + 2
            e = target[s:].index('</td>') + s
            away_score = target[s:e]
            target = target[s:]
            s = target.index('score_hm"') + len('score_hm"') + 2
            e = target[s:].index('</td>') + s
            home_score = target[s:e]
            target = target[s:]
            s = target.index('exp_pts_before"') + len('exp_pts_before"') + 2
            e = target[s:].index('</td>') + s
            expected_points_before = target[s:e]
            target = target[s:]
            s = target.index('exp_pts_after"') + len('exp_pts_after"') + 2
            e = target[s:].index('</td>') + s
            expected_points_after = target[s:e]
            play_by_play = [quarter, time_left, down, to_go, field_pos, player, second_player, result, away_score, home_score,
                            expected_points_before, expected_points_after, Game_ID]
            pbp_master_list.append(play_by_play)
        except:
            pass
# Loop conclusion, giving update to user #
    end_clock = datetime.now()
    split = end_clock - start_clock
    est_time = split * (len(link_list_gl) - link_list_gl.index(tlink))
    print(Back.RESET + Fore.RESET+ Fore.GREEN+'Game: '+ str(link_list_gl.index(tlink)) + " of: "
          + str(len(link_list_gl)) + " games collected --- "+ str(round(link_list_gl.index(tlink)/len(link_list_gl)*100,2)) +
          "%. Time Remaining: "+ str(est_time))

# Building of Pandas dataframes to save to excel. Date used in saving convention #
stamp = datetime.today()
stamp = str(stamp)[:10]
headers_offensive_stats.append("Game ID")
snap_headers.append("Game ID")
headers_offensive_stats.append("Date")
df = pd.DataFrame(stats_grouped, columns=headers_offensive_stats)
df.to_excel(File path)
df_snap_count = pd.DataFrame(snap_data, columns=snap_headers)
df_snap_count.to_excel(File path)
df_pbp = pd.DataFrame(pbp_master_list, columns=pbp_headers)
df_pbp.to_excel(File path)
print('Done')
