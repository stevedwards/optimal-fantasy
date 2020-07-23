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


def pairwise(iterable):
	"""s -> (s0,s1), (s1,s2), (s2, s3), ..."""
	a, b = itertools.tee(iterable)
	next(b, None)
	return itertools.izip(a, b)

class MIP:

    def __init__(self,players):
        self.players = players
        self.num_players = len(players.players)
        self.variables = {}
        self.model = Model("super_coach")
        self.current_round = round
        self.num_rounds = 4
        self.rounds = range(1, self.num_rounds+1)
        #self.rounds = range(12,15)
        self.scoring_positions = [DEF, MID, RUCK, FOR]
        self.sub_positions = [SUB_DEF, SUB_MID, SUB_RUCK, SUB_FOR]
        self.positions = [DEF, SUB_DEF, MID, SUB_MID, RUCK, SUB_RUCK, FOR, SUB_FOR]
        self.capacities = {DEF:6, SUB_DEF: 2, MID: 8, SUB_MID: 3, RUCK: 2, SUB_RUCK: 1, FOR: 6, SUB_FOR: 2}
        self.bye_rounds = [12,13,14]
        self.budget = 10000000
        self.captain_pos = [CAP, VICE]
        self.num_scoring_players = self.set_scoring_players_per_round()
        self.position2players = {position : [player for player in self.players if any(player_pos in position for player_pos in player.positions)] for position in self.positions}
        self.playerID2positions = {player.id : [pos for scoring_pos in player.positions for pos in ["Sub-"+scoring_pos, scoring_pos]] for player in self.players}
        self.playerID2subpositions = {player.id : ["Sub-" + pos for pos in player.positions] for player in self.players}
        self.positions2slots = {pos: range(self.capacities[pos]) for pos in self.sub_positions}
        self.scoringpos2subpos = {playing_pos : "Sub-" + playing_pos for playing_pos in self.scoring_positions}

        # VARIABLES
        self.player_vars = self.create_player_vars()
        self.scoring_vars = self.create_scoring_vars()
        self.captain_vars, self.vice_captain_vars = self.create_captain_vars()
        self.scoring_vice_vars = self.create_scoring_vice_vars()
        self.slot_vars = self.create_slot_vars()
        self.emergency_vars = self.create_emergency_vars()

        # CONSTRAINTS
        #self.add_score_based_slot_logic_constraints()
        #self.force_emergencies()
        self.add_unique_captain_constraints()
        self.add_in_team_captain_constraints()
        self.add_pos_cover_constraints()
        self.add_unique_pos_constraints()
        self.add_emergency_consistency_constraints()
        self.add_scoring_var_cover_constraints()
        self.add_budget_constraint()
        self.add_slot_emergency_cons_constraint()
        self.add_number_emergencies_req_constraints()
        #self.add_slot_logic_constraints()
        self.add_slot_ordering_constraints()
        self.add_scoring_logic_constraints()
        self.add_scoring_vice_logic_constraints()
        self.add_unique_slot_constraints()
        self.add_beautiful_slot_logic_constraints()
        #self.add_initial_scoring_slot_constraints()

        self.model.modelSense = GRB.MAXIMIZE
        self.model.write('ghost2.mps')


        print "model built"


    ###########################
    # PARAMETERS
    ###########################

    def set_scoring_players_per_round(self):
        """In bye weeks only 18 players count towards your points"""

        scoring_players_per_round = {round: 22 for round in self.rounds}

        for bye_round in self.bye_rounds:
            scoring_players_per_round[bye_round] = 18

        return scoring_players_per_round

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
                                  obj=0)
        return player_vars

    def create_scoring_vars(self):
        """xhat_p,r"""

        scoring_vars = defaultdict(dict)
        for player in self.players:
            for round in self.rounds:
                scoring_vars[player.id][round] = self.model.addVar(
                    vtype=GRB.BINARY,
                    obj=player.points[round]
                )

        return scoring_vars

    def create_captain_vars(self):

        captain_vars = {}
        vice_captain_vars = {}
        for player in self.players:

            captain_vars[player.id] = self.model.addVar(
                vtype=GRB.BINARY,
                obj=sum(player.points[round] for round in self.rounds)
            )

            vice_captain_vars[player.id] = self.model.addVar(
                vtype=GRB.BINARY,
                obj=0
            )

        return captain_vars, vice_captain_vars

    def create_scoring_vice_vars(self):
        """cbar_p,r"""

        scoring_vice_vars = defaultdict(dict)
        for player in self.players:
            for round in self.rounds:
                scoring_vice_vars[player.id][round] = self.model.addVar(
                    vtype=GRB.BINARY,
                    obj=player.points[round])

        return scoring_vice_vars

    def create_slot_vars(self):
        """y_pqrs"""

        slot_vars = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for player in self.players:
            for pos in self.playerID2subpositions[player.id]:
                for round in self.rounds:
                    for slot in range(self.capacities[pos]):
                        slot_vars[player.id][pos][round][slot] = self.model.addVar(
                            vtype=GRB.BINARY,
                            obj=0
                        )

        return slot_vars

    def create_emergency_vars(self):
        """e_p,q"""

        emergency_vars = defaultdict(dict)
        for player in self.players:
            for pos in self.playerID2positions[player.id]:
                emergency_vars[player.id][pos] = self.model.addVar(
                    vtype=GRB.BINARY,
                    obj=0
                )

        return  emergency_vars
    ###########################
    # CONSTRAINTS
    ###########################

    def force_emergencies(self):

        for pos in self.sub_positions:
            num_slots = len(self.positions2slots[pos])

            if DEF in pos:

                self.model.addConstr(
                    sum(self.emergency_vars[player.id][pos] for player in self.position2players[pos]) == 2
                )

    print("Adding constraints")
    def add_unique_captain_constraints(self):

        print("1 - unique captain constraints")

        self.model.addConstr(
            sum(self.captain_vars[player.id] for player in self.players) == 1
        )

        self.model.addConstr(
            sum(self.vice_captain_vars[player.id] for player in self.players) == 1
        )

    def add_in_team_captain_constraints(self):
        print("2 - in team captain constraints")

        for player in self.players:

            self.model.addConstr(
                self.captain_vars[player.id] <=
                sum(self.player_vars[player.id][pos] for pos in player.positions)
            )

            self.model.addConstr(
                self.vice_captain_vars[player.id] <=
                sum(self.player_vars[player.id][pos] for pos in player.positions)
            )

    def add_pos_cover_constraints(self):
        print("3 - position cover constraints")

        for pos in self.positions:
            self.model.addConstr(
                sum(self.player_vars[player.id][pos] for player in self.position2players[pos]) == self.capacities[pos]
            )

    def add_unique_pos_constraints(self):

        print("4 - unique position constraints")

        for player in self.players:
            self.model.addConstr(
                sum(self.player_vars[player.id][pos] for pos in self.playerID2positions[player.id]) <= 1
            )

    def add_emergency_consistency_constraints(self):

        print("5 - emergency consistency constraints")
        for player in self.players:
            for pos in self.playerID2subpositions[player.id]:
                self.model.addConstr(
                    self.emergency_vars[player.id][pos] <= self.player_vars[player.id][pos]
                )

    def add_scoring_var_cover_constraints(self):
        print("6 - scoring var cover constraints")

        for round in self.rounds:
            self.model.addConstr(
                sum(self.scoring_vars[player.id][round] for player in self.players) <= self.num_scoring_players[round]
            )

    def add_slot_emergency_cons_constraint(self):

        for player in self.players:
            for pos in self.playerID2subpositions[player.id]:
                for round in self.rounds:
                    self.model.addConstr(
                        sum(self.slot_vars[player.id][pos][round][slot] for slot in range(self.capacities[pos])) <=
                        self.emergency_vars[player.id][pos]
                    )

    def add_budget_constraint(self):

        self.model.addConstr(
            sum(player.price[self.rounds[0]]*self.player_vars[player.id][pos] for player in self.players for pos in self.playerID2positions[player.id]) <= self.budget
        )

    def add_number_emergencies_req_constraints(self):

        for pos in self.scoring_positions:
            for round in self.rounds:
                self.model.addConstr(
                    sum(sum(self.slot_vars[player.id][self.scoringpos2subpos[pos]][round][slot] for player in self.position2players[pos]) for slot in self.positions2slots[self.scoringpos2subpos[pos]])  <=
                    sum(self.player_vars[player.id][pos] for player in self.position2players[pos] if player.points[round] == 0)
                )

    def add_slot_ordering_constraints(self):
        """Earlier slots must be used before later ones"""

        for pos in self.sub_positions:
            for round in self.rounds:
                for slot1, slot2 in pairwise(self.positions2slots[pos]):
                    self.model.addConstr(
                        sum(self.slot_vars[player.id][pos][round][slot2] -
                            self.slot_vars[player.id][pos][round][slot1] for player in self.position2players[pos]) <= 0
                    )

    def add_slot_logic_constraints(self):
        """This is the scary one"""

        for player in self.players:
            for pos in self.playerID2subpositions[player.id]:
                for slot_1, slot_2 in pairwise(self.positions2slots[pos]):
                    for round in self.rounds:
                        self.model.addConstr(
                            self.slot_vars[player.id][pos][round][slot_2] <=
                            sum(self.slot_vars[player2.id][pos][round][slot_1] for player2 in self.position2players[pos] if player2.points[round] < player.points[round])
                        )
    def add_unique_slot_constraints(self):
        for pos in self.sub_positions:
            for round in self.rounds:
                for slot in self.positions2slots[pos]:
                    self.model.addConstr(
                        sum(self.slot_vars[player.id][pos][round][slot] for player in self.position2players[pos]) <= 1
                    )

    def add_scoring_logic_constraints(self):

        for player in self.players:
            for round in self.rounds:
                self.model.addConstr(
                    self.scoring_vars[player.id][round] <=
                    sum(self.player_vars[player.id][pos] for pos in player.positions) +
                    sum(sum(self.slot_vars[player.id][pos][round][slot] for slot in self.positions2slots[pos]) for pos in self.playerID2subpositions[player.id])
                )

    def add_scoring_vice_logic_constraints(self):

        for player in self.players:
            for round in self.rounds:
                self.model.addConstr(
                    self.scoring_vice_vars[player.id][round] <=
                    self.vice_captain_vars[player.id]
                )

        for round in self.rounds:
            self.model.addConstr(
                sum(self.scoring_vice_vars[player.id][round] for player in self.players) <=
                sum(self.captain_vars[player.id] for player in self.players if player.points[round] == 0)
            )

        for player in self.players:
            self.model.addConstr(
                self.vice_captain_vars[player.id] + self.captain_vars[player.id] <= 1
            )


    def add_initial_scoring_slot_constraints(self):
        for pos in self.sub_positions:
            if len(self.positions2slots[pos]) > 1:
                for round in self.rounds:
                    for player1 in self.position2players[pos]:
                        for player2 in self.position2players[pos]:
                            if player2.points[round] < player1.points[round]:
                                self.model.addConstr(
                                    self.slot_vars[player1.id][pos][round][0] <= 1 -
                                    self.emergency_vars[player2.id][pos]
                                )

    def add_beautiful_slot_logic_constraints(self):

        for pos in self.sub_positions:
            num_slots = len(self.positions2slots[pos])
            for round in self.rounds:
                for player1 in self.position2players[pos]:
                    self.model.addConstr(
                        sum(self.emergency_vars[player2.id][pos] for player2 in self.position2players[pos] if player2.points[round] < player1.points[round]) +
                        sum((num_slots-slot)*self.slot_vars[player1.id][pos][round][slot] for slot in self.positions2slots[pos]) <= num_slots
                    )

    def add_score_based_slot_logic_constraints(self):
        for pos in self.sub_positions:
            num_slots = len(self.positions2slots[pos])
            for round in self.rounds:
                diff_scores = set(player.points[round] for player in self.position2players[pos])
                for slot in self.positions2slots[pos]:
                    for score in diff_scores:

                        self.model.addConstr(
                            sum(self.emergency_vars[player.id][pos] for player in self.position2players[pos] if player.points[round] <= score) +
                            sum((num_slots-slot)*self.slot_vars[player.id][pos][round][slot] for player in self.position2players[pos] if player.points[round] > score) <=
                            num_slots
                        )



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
            trade_count = 0
            for round in self.rounds:

                f.write("\n-----------------\nRound {}\n".format(round))

                # Points per round
                points_in_round = 0
                for player in self.players:

                    if self.captain_vars[player.id].x > 0.5:
                        points_in_round += player.points[round]

                    if self.scoring_vice_vars[player.id][round].x > 0.5:
                        points_in_round += player.points[round]

                    if self.scoring_vars[player.id][round].x > 0.5:
                        points_in_round += player.points[round]

                f.write("Points {}\n".format(points_in_round))

                # Team Value
                team_value = 0
                for player in self.players:
                    if any(self.player_vars[player.id][pos].x > 0.5 for pos in self.playerID2positions[player.id]):
                        team_value = team_value + player.price[round]

                f.write("Team Value {}\n".format(team_value))

                # Budget
                f.write("Remaining budget {}\n".format(self.budget - team_value))
                f.write("-----------------\n")

                f.write("-----------------\n")

                for player in self.players:
                    if self.captain_vars[player.id].x > 0.5:
                        f.write("Captain {} {} with {} points\n".format(player.first_name, player.last_name, player.points[round]))

                for player in self.players:
                    if self.vice_captain_vars[player.id].x > 0.5:
                        f.write("Vice {} {} with {} points {}\n".format(player.first_name, player.last_name, player.points[round], "*" if self.scoring_vice_vars[player.id][round].x > 0.5 else ""))

            #     num_emergencies = len([player_id for player_id, player in enumerate(self.players) for pos_index, pos in enumerate(self.positions) if "Sub" in pos and self.emergency_vars[player_id][round][pos].x > 0.5])
            #     num_scoring_emergencies = len([player_id for player_id, player in enumerate(self.players) for pos_index, pos in enumerate(self.positions) for level in range(self.capacities[pos_index]) if "Sub" in pos and self.scoring_emergency_vars[player_id][round][pos][level].x > 0.5])\
            #     f.write("Number of Scoring emergencys: {} / {}\n".format(num_scoring_emergencies, num_emergencies))

                for pos in self.positions:

                    players_in_round = []
                    for player in self.position2players[pos]:
                        if self.player_vars[player.id][pos].x > 0.5:
                            players_in_round.append(player)

                    print(players_in_round)
                    players_in_round.sort(key=lambda x: x.points[round], reverse=True)

                    for player in self.players:
                #
                        if player in players_in_round:

                            player_name = player.first_name + " " + player.last_name
                            suffix = ""
                            if "Sub" in pos:
                                if self.emergency_vars[player.id][pos].x > 0.5:
                                    suffix += "(E)"

                                for level in self.positions2slots[pos]:
                                    if self.slot_vars[player.id][pos][round][level].x > 0.5:
                                        suffix += "{}***".format(level)

                            f.write("{:30} - {:4} - ${:5} - {:4} {}\n".format(player_name, player.points[round], player.price[round], pos, suffix))
			#
			#
            #     f.write("Points - {}\n".format(points_in_round))
            #     f.write("-----------------\n")
			#
            # f.write('\nTOTAL Points: {}\n'.format(self.model.objVal))
            # f.write('Number of trades used {}\n'.format(trade_count))

                #sum(self.trade_out_vars[player][round].x - self.trade_out_vars[player][round].x for player in range(self.num_players) for round in range(self.num_rounds-1))))


            """
            for player_id, player in enumerate(self.players):
                if sum(self.player_vars[player_id][round] for round in range(self.num_rounds)) == 0:
                    print("{} {} not used\n".format(player.first_name, player.last_name))
            """

    def solve(self, num_threads, output_file):




        #self.model.setParam(GRB.Param.Threads, num_threads)
        self.model.setParam(GRB.Param.LogFile, output_file)
        self.model.setParam(GRB.Param.MIPGap, 0)
        #self.model.setParam(GRB.Param.Heuristics, 0.5)
        #self.model.setParam(GRB.Param.TimeLimit, 600)
        #self.model.setParam(GRB.Param.SolutionLimit, 1)
        self.model.optimize()#self._next_solution_cb)
        self.write_results_to_file(output_file)
