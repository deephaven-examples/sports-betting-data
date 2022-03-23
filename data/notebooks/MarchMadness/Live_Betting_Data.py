from deephaven import DynamicTableWriter
import deephaven.conversion_utils as cu
import deephaven.Types as dht

from datetime import datetime
import urllib.request
import numpy as np
import threading
import time
import sys
import re

# Enter the date you'd like to inspect here
date_of_games = datetime.today().strftime("%Y-%m-%d")

# Enter the number of times you'd like to pull here
total_num_pulls = 2

url = "https://www.scoresandodds.com/ncaab?date=" + date_of_games

ndp = 6
nml = 2

column_names = [
    "Matchup", "AwayTeam_Score", "HomeTeamScore", 
    "OU_Open", "OU_Movements", "OU_Current", "OU_Live",
    "OU_Risk_Open", "OU_Risk_Movements", "OU_Risk_Current", "OU_Risk_Live",
    "Spread_Open", "Spread_Movements", "Spread_Current", "Spread_Live",
    "Spread_Risk_Open", "Spread_Risk_Movements", "Spread_Risk_Current", "Spread_Risk_Live",
    "Away_Moneyline", "Home_Moneyline",
    "AwayTeam_Record", "HomeTeam_Record"
]

column_types = [
    dht.string, dht.int_, dht.int_, 
    dht.string, dht.string_array, dht.string, dht.string, 
    dht.int_, dht.int_array, dht.int_, dht.int_,
    dht.double, dht.double_array, dht.double, dht.double,
    dht.int_, dht.int_array, dht.int_, dht.int_,
    dht.int_, dht.int_,
    dht.string, dht.string
]

table_writer = DynamicTableWriter(
    column_names, column_types
)

ncaab_betting_data = table_writer.getTable()

def pull_ncaab_betting_data(url):

    num_pulls = 0

    while(num_pulls < total_num_pulls):

        start = time.time()

        with urllib.request.urlopen(url) as response:
            html = response.read().decode().lower()

        line_movement_indices = [i.start() for i in re.finditer("line movement", html)]

        num_matchups = len(line_movement_indices)
        num_teams = num_matchups * 2
        team_names = [""] * num_teams
        team_wins = [0] * num_teams
        team_losses = [0] * num_teams

        o_u_predictions = np.zeros((num_matchups, 6), dtype = "<U6")
        spread_predictions = np.zeros((num_matchups, 6), dtype = np.double)
        away_line_predictions = np.zeros((num_matchups, 6), dtype = np.intc)
        home_line_predictions = np.zeros((num_matchups, 6), dtype = np.intc)
        moneyline_predictions = np.zeros((num_matchups, 2), dtype = np.intc)
        away_team_scores = np.zeros(num_matchups, dtype = np.intc)
        home_team_scores = np.zeros(num_matchups, dtype = np.intc)

        team_indices = [i.start() for i in re.finditer('<a href="/ncaab/teams/', html)]

        # Get all of the team names
        for i, team_index in enumerate(team_indices):
            tempstr = html[team_index + 22:team_index + 50]
            team_names[i] = tempstr[:tempstr.find('"')]

        # Split into home and away teams
        away_teams = [team_names[i] for i in range(num_teams) if i % 2 == 0]
        home_teams = [team_names[i] for i in range(num_teams) if i % 2 == 1]

        # Get all of the other information on a per-matchup basis
        for matchup_index, html_index in enumerate(team_indices[::2]):
            # Home and away team names
            away_team_index = 2 * matchup_index
            home_team_index = 2 * matchup_index + 1
            away_team_name = team_names[away_team_index]
            home_team_name = team_names[home_team_index]
            # Grab the chunk of html that corresponds to this matchup data
            if matchup_index < num_matchups - 1:
                chunk_len = team_indices[home_team_index + 1] - team_indices[away_team_index]
            else:
                chunk_len = 2 * team_indices[home_team_index] - team_indices[away_team_index]
            html_chunk = html[team_indices[away_team_index]:team_indices[away_team_index] + chunk_len]
            # Wins/losses
            w_l_indices = [[k.start(), k.end() + 1] for k in re.finditer("\d+-\d", html_chunk)][0:2]
            away_team_record = html_chunk[w_l_indices[0][0]:w_l_indices[0][1]].replace("<", "").split("-")
            home_team_record = html_chunk[w_l_indices[1][0]:w_l_indices[1][1]].replace("<", "").split("-")
            team_wins[away_team_index] = int(away_team_record[0])
            team_losses[away_team_index] = int(away_team_record[1])
            team_wins[home_team_index] = int(home_team_record[0])
            team_losses[home_team_index] = int(home_team_record[1])
            # Score, over/under, spread, line, and moneyline
            score_indices = [k.end() for k in re.finditer('event-card-score tbd', html_chunk)]
            o_u_spread_indices = [k.end() for k in re.finditer('<span class="data-value">', html_chunk)]
            line_indices = [k.end() for k in re.finditer('<small class="data-odds">', html_chunk)]
            moneyline_indices = [k.end() for k in re.finditer('<span class="data-moneyline">', html_chunk)]
            score_index = 0
            o_u_index = 0
            spread_index = 0
            line_index = 0
            moneyline_index = 0
            # Scores
            for i, index in enumerate(score_indices):
                content = re.sub("[^0-9]", "", html_chunk[index:index + 7])
                if content:
                    if i == 0:
                        away_team_scores[matchup_index] = int(content)
                    else:
                        home_team_scores[matchup_index] = int(content)
                else:
                    if i == 0:
                        away_team_scores[matchup_index] = 0
                    else:
                        home_team_scores[matchup_index] = 0
            # Over/unders
            for i, index in enumerate(o_u_spread_indices):
                content = html_chunk[index:index + 8].strip(" </spmlan")
                if content == "k":
                    content = "0"
                is_o_u = re.search("[o|u]", content)
                if is_o_u:
                    o_u_predictions[matchup_index][o_u_index] = content
                    o_u_index += 1
                else:
                    spread_predictions[matchup_index][spread_index] = float(content)
                    spread_index += 1
            # Lines
            for i, index in enumerate(line_indices):
                content = html_chunk[index:index + 10].strip(" </small>")
                if content == "even":
                    content = "0"
                if i < ndp:
                    away_line_predictions[matchup_index][i] = int(content)
                else:
                    home_line_predictions[matchup_index][i - ndp] = int(content)
            # Moneylines
            for i, index in enumerate(moneyline_indices):
                content = re.sub("[^0-9]", "", html_chunk[index:index + 7])
                if not content:
                    content = "0"
                moneyline_predictions[matchup_index][i] = int(content)

        # Fix matchup data for games missing data
        for i in range(num_matchups):
            # Over/under
            over_unders = o_u_predictions[i]
            n_valid_o_u = np.count_nonzero(over_unders)
            if 0 < n_valid_o_u < ndp:
                max_idx = np.max(np.nonzero(over_unders))
                over_unders[-2], over_unders[max_idx] = over_unders[max_idx], over_unders[-2]
                o_u_predictions[i] = over_unders
            # Spread
            spreads = spread_predictions[i]
            n_valid_spreads = np.count_nonzero(spreads)
            if 0 < n_valid_spreads < ndp:
                max_idx = np.max(np.nonzero(spreads))
                spreads[-2], spreads[max_idx] = spreads[max_idx], spreads[-2]
                spread_predictions[i] = spreads
            # Line
            away_lines = away_line_predictions[i]
            n_valid_lines = np.count_nonzero(away_lines)
            if 0 < n_valid_lines < ndp:
                max_idx = np.max(np.nonzero(away_lines))
                away_lines[-2], away_lines[max_idx] = away_lines[max_idx], away_lines[-2]
                away_line_predictions[i] = away_lines
            home_lines = home_line_predictions[i]
            n_valid_lines = np.count_nonzero(home_lines)
            if 0 < n_valid_lines < ndp:
                max_idx = np.max(np.nonzero(home_lines))
                home_lines[-2], home_lines[max_idx] = home_lines[max_idx], home_lines[-2]
                home_line_predictions[i] = home_lines

        # Write the data to the live table
        for i in range(num_matchups):
            away_team_index = 2 * i
            home_team_index = 2 * i + 1
            # Team names, scores, wins, and losses
            matchup = " - ".join([away_teams[i], home_teams[i]])
            away_score = away_team_scores[i].item()
            home_score = home_team_scores[i].item()
            # Over/under
            over_unders = o_u_predictions[i]
            o_u_open = over_unders[0].item()
            o_u_moves = jpy.array("java.lang.String", [over_unders[i].item() for i in range(1, 4)])
            o_u_curr = over_unders[4].item()
            o_u_live = over_unders[5].item()
            # Over/under risk
            o_u_risks = away_line_predictions[i]
            o_u_risk_open = o_u_risks[0].item()
            o_u_risk_moves = jpy.array("int", [o_u_risks[i].item() for i in range(1, 4)])
            o_u_risk_curr = o_u_risks[4].item()
            o_u_risk_live = o_u_risks[5].item()
            # Spread
            spreads = spread_predictions[i]
            spread_open = spreads[0].item()
            spread_moves = jpy.array("double", [spreads[i].item() for i in range(1, 4)])
            spread_curr = spreads[4].item()
            spread_live = spreads[5].item()
            # Spread risk
            spread_risks = home_line_predictions[i]
            spread_risk_open = spread_risks[0].item()
            spread_risk_moves = jpy.array("int", [spread_risks[i] for i in range(1, 4)])
            spread_risk_curr = spread_risks[4].item()
            spread_risk_live = spread_risks[5].item()
            # Moneylines
            money_lines = moneyline_predictions[i]
            away_moneyline = money_lines[0].item()
            home_moneyline = money_lines[1].item()
            # Team records
            away_team_record = " - ".join([str(team_wins[away_team_index]), str(team_losses[away_team_index])])
            home_team_record = " - ".join([str(team_wins[home_team_index]), str(team_losses[home_team_index])])

            table_writer.logRow(
                matchup, away_score, home_score,
                o_u_open, o_u_moves, o_u_curr, o_u_live,
                o_u_risk_open, o_u_risk_moves, o_u_risk_curr, o_u_risk_live,
                spread_open, spread_moves, spread_curr, spread_live, 
                spread_risk_open, spread_risk_moves, spread_risk_curr, spread_risk_live,
                away_moneyline, home_moneyline,
                away_team_record, home_team_record
            )
    
        end = time.time()

        time.sleep(15 - (end - start))

        num_pulls += 1

thread = threading.Thread(target = pull_ncaab_betting_data, args = (url,))
thread.start()