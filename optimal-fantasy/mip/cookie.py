from gurobipy import *
from datetime import datetime
from collections import  defaultdict
"""
Code written by Steven J Edwards, September 2017
Contact steven.edwards17@outlook.com for questions
"""


DEF = "DEF"
SUB_DEF = "Sub-DEF"
MID = "MID"
SUB_MID = "Sub-MID"
RUCK = "RUC"
SUB_RUCK = "Sub-RUC"
FOR = "FWD"
SUB_FOR = "Sub-FWD"
CAP = "captain"
VICE = "vice"

BUDGET_VARS = 'budget_vars'
PLAYER_VARS = 'player_vars'
TRADE_IN_VARS = 'trade_in_vars'
TRADE_OUT_VARS = 'trade_out_vars'
POS_VARS = 'pos_vars'
CAPTAIN_VARS = 'captain_vars'
SCORING_VARS = 'scoring_vars'
ROOKIE_PRICE = 200000
PREMIUM_PRICE = 600000
MAX_REMAINING_BUDGET = 50000
MAX_PRICE = 650000

def pairwise(iterable):
	"""s -> (s0,s1), (s1,s2), (s2, s3), ..."""
	a, b = itertools.tee(iterable)
	next(b, None)
	return itertools.izip(a, b)

class MIP:

    def __init__(self,players):
        self.players = players
        self.positions = [DEF, SUB_DEF, MID, SUB_MID, RUCK, SUB_RUCK, FOR, SUB_FOR]
        self.scoring_positions = [DEF, MID, RUCK, FOR]
        self.num_players = len(players.players)
        self.variables = {}
        self.model = Model("cookie")
        self.current_round = 0
        self.capacities = {DEF:6, SUB_DEF: 2, MID: 8, SUB_MID: 3, RUCK: 2, SUB_RUCK: 1, FOR: 6, SUB_FOR: 2}
        self.budget = 10000000
        #self.budget = 5137200

        self.position2players = {position : [player for player in self.players if any(player_pos in position for player_pos in player.positions)] for position in self.positions}
        self.playerID2positions = {player.id : [pos for scoring_pos in player.positions for pos in ["Sub-"+scoring_pos, scoring_pos]] for player in self.players}
        self.playerID2subpositions = {player.id : ["Sub-" + pos for pos in player.positions] for player in self.players}
        self.scoringpos2subpos = {playing_pos : "Sub-" + playing_pos for playing_pos in self.scoring_positions}



        # VARIABLES
        self.player_vars = self.create_player_vars()

        # CONSTRAINTS
        self.add_pos_cover_constraints()
        self.add_unique_player_constraints()
        self.add_budget_constraint()
        #self.add_at_least_one_premium()
        self.add_rooke_bench_contraints()
        self.add_flexibility_constraints()
        self.add_remaining_salary_constraints()
        #self.add_max_price_constraints()
        #self.no_injuries()

        self.model.modelSense = GRB.MAXIMIZE
        #self.model.write('cookie.mps')


        print "model built"



    ###########################
    # VARIABLES
    ###########################

    print("Creating variables")
    def create_player_vars(self):
        """x_p,q"""

        player_vars = defaultdict(dict)
        for player in self.players:
            for pos in self.playerID2positions[player.id]:
                player_vars[player.id][pos] = self.model.addVar(vtype=GRB.BINARY,
                                  obj=player.ownership)
        return player_vars

    ###########################
    # CONSTRAINTS
    ###########################

    def add_max_price_constraints(self):

        for player in self.players:
            if player.price[1] >= MAX_PRICE:
                self.model.addConstr(
                    sum(self.player_vars[player.id][pos] for pos in self.playerID2positions[player.id]) <= 0
                )

    def add_pos_cover_constraints(self):
        print("position cover constraints")

        for pos in self.positions:
            self.model.addConstr(
                sum(self.player_vars[player.id][pos] for player in self.position2players[pos]) == self.capacities[pos]
            )

    def add_unique_player_constraints(self):
        print("unique player constraints")

        for player in self.players:

            self.model.addConstr(
                sum(self.player_vars[player.id][pos] for pos in self.playerID2positions[player.id]) <= 1
            )

    def add_budget_constraint(self):

        self.model.addConstr(
            sum(player.price[1] * sum(self.player_vars[player.id][pos] for pos in self.playerID2positions[player.id]) for player in self.players) <= self.budget
        )

    def add_rooke_bench_contraints(self):
        """Only rookies on the bench"""

        for player in self.players:

            if player.price[1] >= ROOKIE_PRICE:

                self.model.addConstr(
                    sum(self.player_vars[player.id][pos] for pos in self.playerID2subpositions[player.id]) == 0
                )

    def add_at_least_one_premium(self):

        self.model.addConstr(
            sum(self.player_vars[player.id][pos] for player in self.players if player.price[1] >= PREMIUM_PRICE for pos in self.playerID2positions[player.id] ) >= 1
        )


    def add_remaining_salary_constraints(self):
        self.model.addConstr(
            sum(player.price[1] * sum(self.player_vars[player.id][pos] for pos in self.playerID2positions[player.id])
                for player in self.players) >= self.budget - MAX_REMAINING_BUDGET
        )

    def add_flexibility_constraints(self):

        def_mid = [player for player in self.players if DEF in player.positions and MID in player.positions]
        self.model.addConstr(
            sum(self.player_vars[player.id][MID] + self.player_vars[player.id][SUB_MID] for player in def_mid) >= 1
        )

        self.model.addConstr(
            sum(self.player_vars[player.id][DEF] + self.player_vars[player.id][SUB_DEF] for player in def_mid) >= 1
        )

        mid_fwd = [player for player in self.players if FOR in player.positions and MID in player.positions]
        self.model.addConstr(
            sum(self.player_vars[player.id][MID] + self.player_vars[player.id][SUB_MID] for player in mid_fwd) >= 1
        )

        self.model.addConstr(
            sum(self.player_vars[player.id][FOR] + self.player_vars[player.id][SUB_FOR] for player in mid_fwd) >= 1
        )

        fwd_ruck = [player for player in self.players if RUCK in player.positions and FOR in player.positions]
        self.model.addConstr(
            sum(self.player_vars[player.id][FOR] + self.player_vars[player.id][SUB_FOR] for player in fwd_ruck) >= 1
        )

        self.model.addConstr(
            sum(self.player_vars[player.id][RUCK] + self.player_vars[player.id][SUB_RUCK] for player in fwd_ruck) >= 1
        )

        fwd_def = [player for player in self.players if DEF in player.positions and FOR in player.positions]
        self.model.addConstr(
            sum(self.player_vars[player.id][FOR] + self.player_vars[player.id][SUB_FOR] for player in fwd_def) >= 1
        )

        self.model.addConstr(
            sum(self.player_vars[player.id][DEF] + self.player_vars[player.id][SUB_DEF] for player in fwd_def) >= 1
        )


        return 0

    ###########################
    # OTHER
    ###########################

    def write_results_to_file(self, output_file):
        """Prints information about the model to the command line

        -------------
        Round 1
        Points X
        Available Budget {}
        Captain {} {}
        Trade in {} {} and {} {}
        Trade out {} {} and {} {}

        Defenders
        {} {} - Points
        ...

        SubDefenders
        {} {} - Points
        """

        with open(output_file, 'a') as f:

            self.model.printStats()

            # Team Value
            team_value = 0
            for player in self.players:
                if any(self.player_vars[player.id][pos].x > 0.5 for pos in self.playerID2positions[player.id]):
                    team_value = team_value + player.price[1]

            f.write("Team Value {}\n".format(team_value))

            # Budget
            f.write("Remaining budget {}\n".format(self.budget - team_value))
            f.write("-----------------\n")

            f.write("-----------------\n")

            for pos in self.positions:

                players_in_round = []
                for player in self.position2players[pos]:
                    if self.player_vars[player.id][pos].x > 0.5:
                        players_in_round.append(player)
                players_in_round.sort(key=lambda x: x.ownership, reverse=True)

                for player in players_in_round:

                    player_name = player.first_name + " " + player.last_name
                    suffix = ""
                    f.write("{:30} - {:4} - {:6} - ${:5} - {:4} {}\n".format(player_name, player.team, player.ownership, player.price[1], pos, suffix))


    def solve(self, num_threads, output_file):

        self.model.setParam(GRB.Param.LogFile, output_file)
        self.model.setParam(GRB.Param.MIPGap, 0)
        self.model.optimize()   #self._next_solution_cb)
        self.write_results_to_file(output_file)
