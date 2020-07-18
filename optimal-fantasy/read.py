import datetime
import argparse
import Player, MIP


def read_data2016(data_file):
    """Reads in all the information for the current data file. Returns a list of players"""

    with open(data_file, 'rU') as f_data:
        rows = f_data.read().splitlines()
        rows = filter(None, rows)  # Removes blank spaces

        # Initialise variables
        players = Player.Players()

        for index, row in enumerate(rows):

            info = row.split(',')

            if index == 0:
                print (info[0])
                continue

            counter = 0

            first_name = info[0].split(' ', 1)[0].lower()
            last_name = info[0].split(' ', 1)[1].lower()


            team = info[1]
            positions = tuple(info[2].split('- '))
            init_price = int(info[4])

            if info[5]:
                price_change = int(info[5])

            if info[6]:
                total_points = int(info[6])

            if info[7]:
                games = int(info[7])

            played = []
            points = []
            for column in range(8, 31):
                if info[column]:

                    if info[column] == "Bye":
                        played.append("BYE")
                        points.append(0)
                    else:
                        played.append(True)
                        points.append(int(info[column]))

                else:
                    played.append(False)
                    points.append(0)

            #print(first_name, last_name, team, positions, init_price, price_change, total_points, games, played, points)
            players.append(Player.Player(first_name, last_name, team, positions, init_price, price_change, total_points, games, played, points))

        print("There are {} players".format(len(players)))
        players.remove_duplicates()
        players.set_prices()
        return players

def read_data2017(data_file):
    """Reads in all the information for the current data file. Returns a list of players"""

    with open(data_file, 'r') as f_data:
        rows = f_data.read().splitlines()
        rows = filter(None, rows)  # Removes blank spaces

        # Initialise variables
        players = Player.Players()

        for index, row in enumerate(rows):

            info = row.split(',')

            #print(info)

            first_name = info[0].split(' ', 1)[0].lower().strip()
            last_name = info[0].split(' ', 1)[1].lower().strip()
            last_name = last_name.replace(" ", "-")

            team = info[1].strip()

            #positions
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

            #print(positions)
            price = []
            points = []
            for column in range(4, 27):
                if info[column] != "-":

                    points.append(int(info[column]))
                else:
                    points.append(0)

            #print(points)
            #print(len(points))

            for column in range(27, 50):
                price.append(int(info[column]))


            #print(price)
            #print(len(price))


            # print(first_name, last_name, team, positions, init_price, price_change, total_points, games, played, points)
            players.append(
                Player.Player(first_name, last_name, team, positions, points, price))



        print("There are {} players".format(len(players)))
        return players

if __name__ == "__main__":

    parser = argparse.ArgumentParser()


    parser.add_argument('-t', "--threads", help="increase output verbosity",
                        action="store_true")
    args = parser.parse_args()

    if args.threads:
        threads = 4
        print("You have specified {} threads".format(threads) )
        #args.threads_spec)
        #threads = args.threads_spec

    #data_file = "2016Data.csv"
    #data_file = "data2018-round22.csv"
    data_file = "data2019-Final.csv"
    round = 23
    #players = read_data2016(data_file)
    players = read_data2017(data_file)

    current_time = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    output_file = current_time + "-SuperCoachOutput.txt"

    mip = MIP.MIP(players, 2017, round, "SC")

    mip.model.update()
    #mip.model.write("without_constraints.lp")

    mip.solve(threads, output_file)

