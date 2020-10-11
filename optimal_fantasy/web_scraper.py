import requests
import pprint
import json

def read_players(n):
    """Reads in the player stats, positions, index etc"""
    data = {}
    player_id = 1
    for player_id in range(1, n + 1):
        player_data = read_player_details(player_id)
        #projection_data = read_player_projections(player_id, auth)
        first_name = player_data["first_name"]
        last_name = player_data["last_name"]
        team = player_data["team"]["abbrev"]
        player_title = f"{first_name} {last_name} ({team})"
        print(player_id, player_title)
        data[player_title] = {
            "id": player_id,
            "first name": first_name,
            "last name": last_name,
            "team": team,
            "positions": [pos["position"] for pos in player_data["positions"]],
            "price": {
                r: x["price"]
                for r, x in enumerate(player_data["player_stats"])
                if r > 0
            },
            "points": {
                r: x["points"]
                for r, x in enumerate(player_data["player_stats"])
                if r > 0
            },
            "ownership": {
                r: x["owned"]
                for r, x in enumerate(player_data["player_stats"])
                if r > 0
            },
        }
    return data


def read_player_details(player_id):
    """Read info such as player name, team, positions, injury status from the first link"""
    link = f"https://supercoach.heraldsun.com.au/2020/api/afl/classic/v1/players/{player_id}?embed=notes,odds,player_stats,player_match_stats,positions,trades"
    return requests.get(link).json()

if __name__ == "__main__":
    num_players = 826
    file = "data/" + "player_data2020.json"
    data = read_players(num_players)
    with open(file, "w") as f:
        json.dump(data, f, indent=4)
