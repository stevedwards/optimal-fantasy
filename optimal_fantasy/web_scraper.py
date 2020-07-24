import requests
from bs4 import BeautifulSoup


class Player:
    def __init__(self, name, team):
        self.name = name
        self.team = team


class Players:
    def __init__(self):
        self.players = []

    def add(self, player):
        self.players.append(player)


FIRST_NAME = "first_name"
LAST_NAME = "last_name"
NUM_PLAYERS = 807
PLAYER_IDS = range(1, NUM_PLAYERS + 1)
POSITIONS = ["DEF", "MID", "RUC", "FWD"]
NUM_ROUNDS = 23
ROUNDS = range(1, 24)


def get_players2018(auth, output):
    """Reads in the player stats, positions, index etc"""
    # Clear data file
    open(output, "w").close()
    for player_id in range(1, NUM_PLAYERS + 1):
        # Scrape info
        player_data, player_string = read_player_details(player_id)
        projection_data = read_player_projections(player_id, auth)
        # Read info
        print(player_id, player_string)
        first_name = player_data["first_name"]
        last_name = player_data["last_name"]
        team = player_data["team"]["abbrev"]
        if "deledio" not in last_name.lower():
            actual_price = {
                index: round_data["price"]
                for index, round_data in enumerate(player_data["player_stats"])
            }
            actual_points = {
                index: round_data["points"]
                for index, round_data in enumerate(player_data["player_stats"])
            }
            current_round = len(player_data["player_stats"]) - 1
            positions = [pos["position"] for pos in player_data["positions"]]
            points = [projection_data[round]["points"] for round in range(NUM_ROUNDS)]
            price = [projection_data[round]["price"] for round in range(NUM_ROUNDS)]
            with open(output, "a") as f_out:
                f_out.write("{}, {},".format(player_string, team))
                f_out.write(
                    "{}, {},".format(
                        positions[0], positions[1] if len(positions) == 2 else ""
                    )
                )
                for round in ROUNDS:
                    if round < current_round:
                        f_out.write("{},".format(actual_points[round]))
                    else:
                        f_out.write("{},".format(points[round - 1]))
                for round in ROUNDS:
                    if round <= current_round:
                        f_out.write("{},".format(actual_price[round - 1]))
                    else:
                        f_out.write("{},".format(price[round - 1]))
                f_out.write("\n")


def read_player_details(player_id):
    """Read info such as player name, team, positions, injury status from the first link"""

    link = "https://supercoach.heraldsun.com.au/2020/api/afl/classic/v1/players/{}?embed=notes,odds,player_stats,player_match_stats,positions,trades".format(
        player_id
    )

    page = requests.get(link)
    data = page.json()
    player_string = "{} {} ({})".format(
        data[FIRST_NAME], data[LAST_NAME], data["team"]["abbrev"]
    )

    return data, player_string


def read_player_projections(player_id, auth):
    """Read player projections from the other link with the authentification"""

    url = "https://supercoach.heraldsun.com.au/2020/api/afl/classic/v1/players/{}/projected_stats".format(
        player_id
    )
    page = requests.get(url, headers={"authorization": auth})
    data = page.json()

    return data


def write_player_positions(output_file, player_data):
    with open(output_file, "w") as f_out:
        for pos in POSITIONS:
            f_out.write("\n{}\n".format(pos))
            for player_id in PLAYER_IDS:
                for player_pos in player_data[player_id]["positions"]:
                    if pos == player_pos["position"]:
                        f_out.write(
                            "{} {} ({})\n".format(
                                player_data[player_id][FIRST_NAME],
                                player_data[player_id][LAST_NAME],
                                player_data[player_id]["team"]["abbrev"],
                            )
                        )


if __name__ == "__main__":
    file = "data2020-SC.csv"
    auth = "Bearer fdfdb8d7a08e19ee20f9c8df080bc35da23c5d2e"
    get_players2018(auth, file)
