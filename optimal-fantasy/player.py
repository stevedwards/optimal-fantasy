# player class
import collections

class Players:
    def __init__(self):
        self.players = []

    def __iter__(self):
        for player in self.players:
            yield player

    def __len__(self):
        return len(self.players)

    def append(self, player):
        self.players.append(player)

    def remove_duplicates(self):
        """The data is a bit messy. In order to remove duplicates we assume that if two players have the same last, 
        player for the same team """

        players = set(self.players)
        print("After removing duplicates there are only {} players".format(len(players)))

        # We also need to delete the
        banned_players = []
        for player in players:
            if "BYE" in player.played:
                banned_players.append(player)
                #print(player.first_name, player.last_name)

        for cheat in banned_players:
            players.remove(cheat)

        print("After removing banned players there are only {} players".format(len(players)))
        self.players = list(players)

    def set_prices(self):
        for player in self.players:
            player.determine_prices()

    def print_all(self):
        for player in self.players:
            print("{} {} {} - {}".format(player.first_name, player.last_name, player.team, player.positions))

class Player:
    def __init__(self, first_name, last_name, team, positions, init_price, price_change, total_points, games, played, points):
        self.first_name = first_name
        self.last_name = last_name
        self.team = team
        self.positions = positions
        self.init_price = init_price
        self.price_change = price_change
        self.total_points = total_points
        self.games = games
        self.played = played
        self.points = points
        self.price = []


    def __init__(self, first_name, last_name, team, positions, points, price):
        self.first_name = first_name
        self.last_name = last_name
        self.team = team
        self.positions = positions
        self.points = points
        self.price = price


    def __eq__(self, other):
        return self.last_name == other.last_name and self.positions == other.positions and self.team == other.team

    def __hash__(self):
        return hash(('last name', self.last_name,
                     'team', self.team,
                     'positions', self.positions))

    def determine_prices(self):
        """Determines the price of each player using the formula given on the Jock Reynolds Stats Spreadsheat"""


        last_three_games = collections.deque([],3)
        self.price.append(self.init_price - self.price_change)

        for round, played in enumerate(self.played):

            if played:
                last_three_games.append(self.points[round])

                if len(last_three_games) == 3:

                    price_change = ((sum(last_three_games)/3*5140)-self.price[round])/4

                    self.price.append(self.price[-1] + price_change)

                else:
                    self.price.append(self.price[round])

            else:
                self.price.append(self.price[round])