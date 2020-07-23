import datetime
import argparse
import player


def read_data(data_file):
    """Reads in all the information for the current data file. Returns a list of players"""
    with open(data_file, "r") as f_data:
        rows = f_data.read().splitlines()
        rows = filter(None, rows)  # Removes blank spaces
        # Initialise variables
        players = player.Players()
        for index, row in enumerate(rows):
            info = row.split(",")
            first_name = info[0].split(" ", 1)[0].lower().strip()
            last_name = info[0].split(" ", 1)[1].lower().strip()
            last_name = last_name.replace(" ", "-")
            team = info[1].strip()
            position1 = info[2].strip()
            position2 = info[3].strip()
            positions = [position1, position2]
            actual_positions = []
            for position in positions:
                if "Midfield" in position or "MID" in position:
                    actual_positions.append("MID")
                elif "Forward" in position or "FWD" in position:
                    actual_positions.append("FWD")
                elif "Defender" in position or "DEF" in position:
                    actual_positions.append("BAC")
                elif "Ruck" in position or "RUC" in position:
                    actual_positions.append("RUC")
            positions = actual_positions
            price = []
            points = []
            for column in range(4, 27):
                if info[column] != "-":
                    points.append(int(info[column]))
                else:
                    points.append(0)
            for column in range(27, 50):
                price.append(int(info[column]))
            players.append(
                player.Player(first_name, last_name, team, positions, points, price)
            )
        print("There are {} players".format(len(players)))
        return players

