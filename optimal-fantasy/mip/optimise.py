import datetime
import argparse
import Player, MIP

"""
Code written by Steven J Edwards, September 2017
Contact steven.edwards17@outlook.com for questions
"""


def read_data2018(data_file):
    """Reads in all the information for the current data file. Returns a list of players"""

    with open(data_file, 'rU') as f_data:
        rows = f_data.read().splitlines()
        rows = filter(None, rows)  # Removes blank spaces

        # Initialise variables
        players = Player.Players()

        for index, row in enumerate(rows):

            info = row.split(',')

            player_string = info[0]
            team = info[1].strip()

            #positions
            positions = [info[2].strip()]
            if info[3].strip():
                positions.append(info[3].strip())

            price = {}
            points = {}
            for index, column in enumerate(range(4, 27)):
                if info[column] != "-":
                    points[index+1] = int(info[column])
                else:
                    points[index+1] = int(0)

            for index, column in enumerate(range(27, 50)):
                price[index+1] = int(info[column])


            players.append(
                Player.Player(player_string, team, positions, points, price))


        print("There are {} players".format(len(players)))
        return players


def read_team(team_file):

    with open(team_file, 'r') as f_in:

        rows = f_in.read().splitlines()
        rows = filter(None, rows)  # Removes blank spaces

        # Read file row by row
        team = []
        for row in rows:

            if "Rounds completed" in row:
                round = int(row.split(',')[3]) # reads the 3rd column

            if "Remaining Budget" in row:
                budget = int(row.split(',')[3])
                print(budget)

            if "Remaining number of trades" in row:
                trades = row.split(',')[3]

            if any([pos in row for pos in ["DEF", "MID", "RUC", "FWD"]]):
                team.append(row.split(',')[3])

        return team, round, budget, trades




if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument('-t', "--threads", type=int, help="increase output verbosity")

    parser.add_argument("projected_data", type=str, help="The player data")
    parser.add_argument("team_data", type=str, help="The input team to read as a starting point")

    args = parser.parse_args()

    threads = args.threads if args.threads else 4
    print "You have specified {} threads".format(threads) #args.threads_spec)

    team, round, budget, trades = read_team(args.team_data)
    players = read_data2018(args.projected_data)


    current_time = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    output_file = 'Output/' + current_time + "-ProjectedTeam.txt"
    mip = MIP.MIP(players, team, round, budget, trades)

    mip.solve(threads, output_file)

