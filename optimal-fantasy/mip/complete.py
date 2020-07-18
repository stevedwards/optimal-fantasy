from gurobipy import *
from datetime import datetime

"""
To do:
- add 2017 data reader
- update byes for 2017 
"""

DEF = "BAC"
SUB_DEF = "Sub-BAC"
MID = "MID"
SUB_MID = "Sub-MID"
RUCK = "RUC"
SUB_RUCK = "Sub-RUC"
FOR = "FWD"
SUB_FOR = "Sub-FWD"

BUDGET_VARS = 'budget_vars'
PLAYER_VARS = 'player_vars'
TRADE_IN_VARS = 'trade_in_vars'
TRADE_OUT_VARS = 'trade_out_vars'
POS_VARS = 'pos_vars'
CAPTAIN_VARS = 'captain_vars'
SCORING_VARS = 'scoring_vars'


class MIP:

    def __init__(self, players, year=2017, num_rounds=22, type="SC"):
        self.players = players
        self.year = year
        self.num_players = len(players.players)
        self.variables = {}
        self.normal_mode = True
        self.model = Model("super_coach")
        self.num_rounds = num_rounds
        self.num_trades = 30
        self.scoring_positions = [DEF, MID, RUCK, FOR]
        self.positions = [DEF, SUB_DEF, MID, SUB_MID, RUCK, SUB_RUCK, FOR,
                          SUB_FOR]
        if type == "SC":
            self.capacities = [6, 2, 8, 3, 2, 1, 6, 2]
            self.budget = 10000000
        elif type == "DT":
            self.capacities = [6, 2, 8, 2, 2, 2, 6, 2]
            self.budget = 11000000
        else:
            self.capacities = []
            self.budget = 0
        if year == 2017:
            self.bye_rounds = [12, 13, 14]
        elif year == 2016:
            self.bye_rounds = [13, 14, 15]
        else:
            self.bye_rounds = []
        self.trades_per_round = self.set_trades_per_round()
        self.num_scoring_players = self.set_scoring_players_per_round()

        # VARIABLES
        self.budget_vars = self.create_budget_variables()
        self.player_vars = self.create_player_variables()
        self.trade_in_vars = self.create_trade_in_variables()
        self.trade_out_vars = self.create_trade_out_variables()
        self.pos_vars = self.create_position_variables()
        self.captain_vars = self.create_captain_variables()
        self.scoring_vars = self.create_scoring_vars()

        # CONSTRAINTS
        # self.min_total_score()
        self.add_allowable_player_position_constraints()
        self.add_scoring_consistency_constraints()
        self.add_max_scoring_players_constraints()
        self.add_capacity_constraints()
        self.add_no_wasted_trade_constraint()
        self.add_season_trade_constraints()
        self.add_round_trade_constraints()
        self.add_consistency_constraints()
        self.add_initial_budget_constraint()
        self.add_budget_consistency_constraints()
        self.add_position_constraints()
        self.add_position_consistency_constraints()
        self.add_player_position_constraints()
        self.add_one_captain_per_round_constraint()
        self.add_on_field_captain_constraint()

        # DIRTY HAX
        self.model._my_vars = {
            BUDGET_VARS: self.budget_vars,
            PLAYER_VARS: self.player_vars,
            TRADE_IN_VARS: self.trade_in_vars,
            TRADE_OUT_VARS: self.trade_out_vars,
            POS_VARS: self.pos_vars,
            CAPTAIN_VARS: self.captain_vars,
            SCORING_VARS: self.scoring_vars,
        }

        self.model._players = players
        self.model._positions = self.positions
        self.model._scoring_positions = self.scoring_positions
        self.read_starting_solution()
        self.model.modelSense = GRB.MAXIMIZE
        self.model.update()
        #self.model.write('optimal.mps')

    @staticmethod
    def _next_solution_cb(model, where):
        """The hackiest output callback in the history of MIP"""
        if where == GRB.Callback.MIPSOL:

            my_vars = model._my_vars
            obj = int(model.cbGet(GRB.Callback.MIPSOL_OBJ))
            output_file = str(obj) + "SubOptimal.txt"
            summary_file = str(obj) + "Summary.csv"

            with open(summary_file,'w') as f_s:
                f_s.write("Starting Team\n\n")
                f_s.write("Player, Price, Position\n")
                for pos_index, pos in enumerate(model._positions):
                    for player_id, player in enumerate(model._players):

                        if model.cbGetSolution(
                                my_vars["pos_vars"][player_id][0][
                                    pos_index]) >= 0.5:
                            player = model._players.players[
                                                  player_id]
                            player.price[0]
                            f_s.write("{} {} ({}), {}, {}\n".format(
                                player.first_name.capitalize(),
                                player.last_name.split('-')[0].capitalize(),
                                player.team,
                                player.price[0], pos))

                f_s.write("\n\nRound-by-Round\n")
                f_s.write("Round, Score, Captain (Points), Trade-In, "
                          "Trade-Out\n")

                num_rounds = len(my_vars[BUDGET_VARS])
                for round in range(num_rounds):

                    trade_in = []
                    trade_out = []
                    points_in_round = 0

                    for player_id, player in enumerate(model._players):

                        if model.cbGetSolution(
                                my_vars["captain_vars"][player_id][
                                    round]) >= 0.5:
                            points_in_round += player.points[
                                round]
                            captain = player

                        if model.cbGetSolution(
                                my_vars["scoring_vars"][player_id][
                                    round]) >= 0.5:
                            points_in_round += player.points[round]

                        if round > 0 and model.cbGetSolution(
                                my_vars["trade_in_vars"][player_id][
                                    round-1]) >= 1:
                            trade_in.append(player)

                        if round > 0 and model.cbGetSolution(
                            my_vars["trade_out_vars"][player_id][
                                round-1]) >= 0.5:
                            trade_out.append(player)

                    trade_in_string = " & ".join(["{} {}".format(
                        player.first_name.capitalize(), player.last_name.split(
                            '-')[0].capitalize()) for player in trade_in]) if\
                        trade_in else ""

                    trade_out_string = " & ".join(["{} {}".format(
                        player.first_name.capitalize(), player.last_name.split(
                            '-')[0].capitalize()) for player in trade_out]) if \
                        trade_out else ""

                    f_s.write("{}, {}, {} {} ({}), {}, {}\n".format(round+1,
                                                       points_in_round,
                                                             captain.first_name.capitalize(),
                                                             captain.last_name.split('-')[0].capitalize(),
                                                             captain.points[
                                                                 round],
                                                                    trade_in_string, trade_out_string))


            with open(output_file, 'w') as f:
                f.write("Temp file created\n\n")

                num_rounds = len(my_vars[BUDGET_VARS])
                f.write("{}".format(num_rounds))
                trade_count = 0
                total_points = 0

                for round in range(num_rounds):
                    f.write("\n-----------------\nRound {}\n".format(round + 1))

                    # Points per round
                    points_in_round = 0
                    largest_point = 0
                    for player_id, player in enumerate(model._players):
                        for pos_index, pos in enumerate(model._positions):
                            if pos in model._scoring_positions:
                                if model.cbGetSolution(
                                        my_vars["pos_vars"][player_id][round][
                                            pos_index]) >= 1:
                                    points_in_round = points_in_round + \
                                                      model._players.players[
                                                          player_id].points[
                                                          round]
                                    if player.points[round] > largest_point:
                                        largest_point = player.points[round]

                    points_in_round = points_in_round + largest_point

                    f.write("Points {}\n".format(points_in_round))

                    # Team Value
                    team_value = 0
                    for player_id, player in enumerate(model._players):
                        if model.cbGetSolution(
                                my_vars["player_vars"][player_id][round]) == 1:
                            team_value = team_value + player.price[round]

                    f.write("Team Value {}\n".format(team_value))

                    # Budget
                    f.write("Remaining budget {}\n".format(
                        model.cbGetSolution(my_vars["budget_vars"][round])))
                    f.write("-----------------\n")

                    # Trade in1
                    change_in_budget = 0
                    if (round > 0):
                        for player_id, player in enumerate(model._players):
                            if model.cbGetSolution(
                                    my_vars["trade_in_vars"][player_id][
                                        round - 1]) == 1 and \
                                    model.cbGetSolution(
                                        my_vars["trade_out_vars"][player_id][
                                            round - 1]) == 0:
                                f.write("Trade in {} {} - ${}\n".format(
                                    player.first_name, player.last_name,
                                    player.price[round]))
                                trade_count = trade_count + 1
                                change_in_budget = change_in_budget - \
                                                   player.price[round]

                        for player_id, player in enumerate(model._players):
                            if model.cbGetSolution(
                                    my_vars["trade_out_vars"][player_id][
                                        round - 1]) == 1 and \
                                    model.cbGetSolution(
                                        my_vars["trade_in_vars"][player_id][
                                            round - 1]) == 0:
                                f.write("Trade out {} {} - ${}\n".format(
                                    player.first_name, player.last_name,
                                    player.price[round]))
                                change_in_budget = change_in_budget + \
                                                   player.price[round]

                    f.write("Change in budget {}\n".format(change_in_budget))

                    f.write("-----------------\n")

                    points_in_round = 0

                    for player_id, player in enumerate(model._players):
                        if model.cbGetSolution(
                                my_vars["captain_vars"][player_id][round]) == 1:
                            f.write("Captain {} {} with {} points\n".format(
                                player.first_name, player.last_name,
                                player.points[round]))
                            points_in_round += player.points[
                                round]

                    for pos_index, pos in enumerate(model._positions):
                        players_in_round = []
                        for player_id, player in enumerate(model._players):
                            if model.cbGetSolution(
                                    my_vars["pos_vars"][player_id][round][
                                        pos_index]) == 1:
                                players_in_round.append(player)

                                if model.cbGetSolution(
                                        my_vars["scoring_vars"][player_id][
                                            round]) == 1:
                                    points_in_round += player.points[round]

                        players_in_round.sort(key=lambda x: x.points[round],
                                              reverse=True)
                        for player_id, player in enumerate(players_in_round):
                            player_name = player.first_name + " " + \
                                          player.last_name

                            f.write("{:30} - {:4} - ${:5} - {:4}\n".format(
                                player_name, player.points[round],
                                player.price[round], pos))
                    total_points = total_points + points_in_round

                    f.write("Points - {}\n".format(points_in_round))
                    f.write("-----------------\n")

                f.write('\nTOTAL Points: {}\n'.format(total_points))
                f.write('Number of trades used {}\n'.format(trade_count))

            #    f.write("{}".format(my_sol))

    def read_starting_solution(self):

        with open("62101SubOptimal2019.txt", 'rU') as f_in:
            rows = f_in.read().splitlines()

            for round in range(0, self.num_rounds):

                relevant = False
                round_data = []
                for row in rows:
                    if "Round {}".format(round + 1) == row:
                        # print(row)
                        relevant = True
                    elif "Round" in row:
                        relevant = False

                    if relevant:
                        round_data.append(row)

                # Check captain
                line = [(row, row_index) for row_index, row in
                        enumerate(round_data) if "Captain" in row]
                first_name = line[0][0].split()[1]
                last_name = line[0][0].split()[2]
                starting_row = int(line[0][1])

                for player_index, player in enumerate(self.players):
                    if player.first_name == first_name and player.last_name \
                            == last_name:
                        # print("Captain Round {} - {} {}".format(round+1,
                        # first_name, last_name))
                        self.captain_vars[player_index][round].start = 1

                for row in round_data[starting_row:starting_row + 31]:

                    row = row.split()
                    first_name = row[0]
                    last_name = row[1]
                    pos = row[-1]

                    for player_index, player in enumerate(self.players):
                        if player.first_name == first_name and \
                                player.last_name == last_name:
                            for pos_index, position in enumerate(
                                    self.positions):
                                if pos == position:
                                    # print("{:20} - {:20} - ${:5} - {
                                    # :4}".format(player.first_name,
                                    # player.last_name, pos, round+1))
                                    self.pos_vars[player_index][round][
                                        pos_index].start = 1

    ###########################
    # PARAMETERS
    ###########################

    def set_trades_per_round(self):
        """In normal weeks you are allowed only 2 trades per week but in bye
        rounds you get 3"""

        trades_per_round = [2] * (self.num_rounds - 1)

        for bye_round in self.bye_rounds:
            trades_per_round[bye_round - 2] = 3

        return trades_per_round

    def set_scoring_players_per_round(self):
        """In bye weeks only 18 players count towards your points"""

        scoring_players_per_round = [22] * self.num_rounds

        for bye_round in self.bye_rounds:
            scoring_players_per_round[bye_round - 1] = 18

        return scoring_players_per_round

    ###########################
    # VARIABLES
    ###########################

    def create_starting_budget_var(self):
        """In the case where finding the cheapest team"""

        return self.model.addVar(vtype=GRB.CONTINUOUS, obj=1,
                                 name="StartingBudget")


    def create_scoring_vars(self):
        """A player must be on the field in order to be scoring. However in bye
        rounds only 18 of
        your on field players contribute towards to points"""

        scoring_vars = []
        for player in self.players.players:
            player_scoring_vars = []
            for round in range(self.num_rounds):
                objective = player.points[round] if self.normal_mode else 0

                player_scoring_vars.append(
                    self.model.addVar(vtype=GRB.BINARY, obj=objective,
                                      name="Scoring-{}-{}-{}".format(
                                          player.first_name,
                                          player.last_name, round)))
            scoring_vars.append(player_scoring_vars)

        return scoring_vars


    def create_captain_variables(self):
        """Each round you can choose a captain. The captain's points are worth
        double. The captain has to be
        on the ground in order for their points to count"""

        captain_vars = []
        for player in self.players.players:
            player_captain_vars = []
            for round in range(self.num_rounds):
                objective = player.points[round] if self.normal_mode else 0
                player_captain_vars.append(
                    self.model.addVar(vtype=GRB.BINARY, obj=objective,
                                      name="Captain-{}-{}-{}".format(
                                          player.first_name, player.last_name,
                                          round)))
            captain_vars.append(player_captain_vars)

        return captain_vars


    def create_position_variables(self):
        """Each position has a limited number of spaces that must be filled"""

        pos_vars = []
        for player in self.players.players:

            player_pos_vars = []
            for round in range(self.num_rounds):

                player_round_pos_vars = []
                for pos in self.positions:

                    if pos in self.scoring_positions:
                        # obj_coeff = player.points[round]
                        obj_coeff = 0
                    else:
                        obj_coeff = 0

                    player_round_pos_vars.append(
                        self.model.addVar(vtype=GRB.BINARY, obj=obj_coeff,
                                          name="PlayerPos-{}-{}-{}-{}".format(
                                              player.first_name,
                                              player.last_name, round, pos)))

                player_pos_vars.append(player_round_pos_vars)
            pos_vars.append(player_pos_vars)

        return pos_vars


    def create_budget_variables(self):
        """We have to manage a budget. We start with $10,000,000 and must keep
        track of how much money we have
        We can make money by trading out a player for one with a lower price. We
        only need a continuous variable
         for each round to keep track off this budget"""

        budget_vars = []

        for round in range(self.num_rounds):
            budget_vars.append(self.model.addVar(vtype=GRB.CONTINUOUS, obj=0,
                                                 name="Budget-{}".format(round)))

        return budget_vars


    def create_player_variables(self):
        """These variables state whether player i is in the team during round t"""

        player_in_team_vars = []

        for player in self.players:
            team_vars = []
            for round in range(self.num_rounds):
                team_vars.append(self.model.addVar(vtype=GRB.BINARY, obj=0,
                                                   name="InTeam-{}-{}-{}".format(
                                                       player.first_name,
                                                       player.last_name,
                                                       round + 1)))

            player_in_team_vars.append(team_vars)

        return player_in_team_vars


    def create_trade_in_variables(self):
        """These binary variables = 1 if player i is traded into the team for
        round t.
        Trades only begin after round 1."""

        trade_in_player_vars = []

        for player in self.players:
            trade_in_vars = []
            for round in range(1, self.num_rounds):
                trade_in_vars.append(self.model.addVar(vtype=GRB.BINARY, obj=0,
                                                       name="TradeIn-{}-{}-{"
                                                            "}".format(
                                                           player.first_name,
                                                           player.last_name,
                                                           round + 1)))

            trade_in_player_vars.append(trade_in_vars)

        return trade_in_player_vars


    def create_trade_out_variables(self):
        """These binary variables = 1 if player i is traded out of the team for
        round t"""

        trade_out_player_vars = []

        for player in self.players:
            trade_out_vars = []
            for round in range(1, self.num_rounds):
                trade_out_vars.append(self.model.addVar(vtype=GRB.BINARY, obj=0,
                                                        name="TradeOut-{}-{}-{"
                                                             "}".format(
                                                            player.first_name,
                                                            player.last_name,
                                                            round)))

            trade_out_player_vars.append(trade_out_vars)

        return trade_out_player_vars


    #############################
    # CONSTRAINTS
    #############################

    def min_total_score(self):
        """Used for the minimum budget version"""

        self.model.addConstr(
            sum(player.points[round] * (self.scoring_vars[player_id][round] +
                                        self.captain_vars[player_id][round])
                for player_id, player in enumerate(self.players.players) for round
                in range(self.num_rounds)) >= self.min_amount
        )


    def add_max_scoring_players_constraints(self):
        """In normal rounds all of your on field players count towards your
        points however in bye rounds only your top
        18 players count towards to score"""

        for round in range(self.num_rounds):
            self.model.addConstr(sum(
                self.scoring_vars[player_id][round] for player_id in
                range(self.num_players)) ==
                                 self.num_scoring_players[round],
                                 "ScoringPositions-{}".format(round))


    def add_scoring_consistency_constraints(self):
        """A player must be in the team in order to score"""

        for player_id, player in enumerate(self.players):
            for round in range(self.num_rounds):
                self.model.addConstr(
                    self.scoring_vars[player_id][round] -
                    sum(self.pos_vars[player_id][round][pos_index]
                        for pos_index, pos in enumerate(self.positions) if
                        pos in self.scoring_positions) <= 0,
                    name="Scoring-{}-{}-{}".format(player.first_name,
                                                   player.last_name, round))


    def add_one_captain_per_round_constraint(self):
        """There can only be one captain per round"""

        for round in range(self.num_rounds):
            self.model.addConstr(sum(self.captain_vars[player][round] for player in
                                     range(self.num_players)) == 1,
                                 "CaptainRound{}".format(round))


    def add_on_field_captain_constraint(self):
        """A player must be in the team and on field in order to be captain"""

        for player_id, player in enumerate(self.players):
            for round in range(self.num_rounds):
                self.model.addConstr(
                    self.captain_vars[player_id][round] -
                    sum(self.pos_vars[player_id][round][pos_index]
                        for pos_index, pos in enumerate(self.positions) if
                        pos in self.scoring_positions) <= 0,
                    name="Onfield-Captain-{}-{}-{}".format(player.first_name,
                                                           player.last_name, round))


    def add_capacity_constraints(self):
        """These constraints say that only 30 people can be in the team each week"""

        for round in range(self.num_rounds):
            self.model.addConstr(sum(self.player_vars[player][round] for player in
                                     range(self.num_players)) == 30,
                                 "CapacityRound{}".format(round))


    def add_season_trade_constraints(self):
        """We can ensure that at most 30 trades are used for the season"""

        self.model.addConstr(sum(
            self.trade_out_vars[player][round] for player in range(self.num_players)
            for round in range(self.num_rounds - 1)) <= self.num_trades,
                             "TotalTrades")


    def add_round_trade_constraints(self):
        """Each round you are allowed at more 2 trades"""

        for round in range(self.num_rounds - 1):
            self.model.addConstr(sum(
                self.trade_out_vars[player][round] for player in
                range(self.num_players)) <= self.trades_per_round[round],
                                 "RoundTrades-{}".format(round))


    def add_position_constraints(self):
        """For each round, there must be a certain amount of each player in each
        position"""

        for round in range(self.num_rounds):
            for pos_iter, pos in enumerate(self.positions):
                self.model.addConstr(sum(
                    self.pos_vars[player][round][pos_iter] for player in
                    range(self.num_players))
                                     == self.capacities[pos_iter],
                                     "Pos-{}-Round-{}".format(pos, round))


    def add_player_position_constraints(self):
        """A player can only be in at most one position every round"""

        for round in range(self.num_rounds):
            for player_id, player in enumerate(self.players):
                self.model.addConstr(sum(
                    self.pos_vars[player_id][round][pos_iter] for pos_iter, pos in
                    enumerate(self.positions)) <= 1,
                                     "SinglePos-{}-{}-{}".format(player.first_name,
                                                                 player.last_name,
                                                                 round))


    def add_allowable_player_position_constraints(self):
        """Some players cannot play in some positions. Constraints these
        positions to equal zero"""

        for player_id, player in enumerate(self.players):

            for pos_index, pos in enumerate(self.positions):

                if pos[-3:] not in player.positions:
                    # print(player.first_name, player.last_name, pos[-3:],
                    # player.positions)
                    self.model.addConstr(
                        sum(self.pos_vars[player_id][round][pos_index] for round in
                            range(self.num_rounds)) == 0,
                        "Player-{}-{}-CantPlay-{}".format(
                            player.first_name, player.last_name, pos))
                    # print("{} {} can not play {}".format(player.first_name,
                    # player.last_name, pos))


    def add_position_consistency_constraints(self):
        """A player can only be in a position if he is in the team"""

        for round in range(self.num_rounds):
            for player_id, player in enumerate(self.players):
                for pos_iter, pos in enumerate(self.positions):
                    self.model.addConstr(self.pos_vars[player_id][round][pos_iter] -
                                         self.player_vars[player_id][round]
                                         <= 0,
                                         name="PosCons-{}-{}-{}-{}".format(
                                             player.first_name, player.last_name,
                                             round, pos))


    def add_consistency_constraints(self):
        """If a player is in the team then he must be in the team the next week
        or he must be traded out"""

        for player_id, player in enumerate(self.players):
            for round in range(self.num_rounds - 1):
                self.model.addConstr(self.player_vars[player_id][round + 1] +
                                     self.trade_out_vars[player_id][round] ==
                                     self.player_vars[player_id][round] +
                                     self.trade_in_vars[player_id][round],
                                     "Consistency-{}-{}-{}".format(
                                         player.first_name, player.last_name,
                                         round + 1))


    def add_no_wasted_trade_constraint(self):
        """Add the redundant constraint that there is no point trading out and
        trading in the same player in a round"""

        for round in range(self.num_rounds - 1):
            for player_id, player in enumerate(self.players):
                self.model.addConstr(self.trade_in_vars[player_id][round] +
                                     self.trade_out_vars[player_id][round] <= 1,
                                     name="NoWastedTrade-{}-{}-{}".format(
                                         player.first_name, player.last_name,
                                         round + 1))


    def add_initial_budget_constraint(self):
        """Initially we have 10,000,000 to spend. Thus the first budget = 10,000,
        000 - the price of everyone
        in the initial team"""

        self.model.addConstr(self.budget_vars[0] + sum(
            self.players.players[player].price[0] * self.player_vars[player][0]
            for player in range(self.num_players)) == self.budget, "InitialBudget")


    def add_budget_consistency_constraints(self):
        """The available budget is equal to that in the previous round + the
        price of the players traded out
        - the price of the players traded in"""

        for round in range(self.num_rounds - 1):
            # print(self.num_rounds, round)
            self.model.addConstr(self.budget_vars[round + 1] -
                                 self.budget_vars[round] +
                                 sum(self.players.players[player].price[round + 1] *
                                     self.trade_in_vars[player][round] for player in
                                     range(self.num_players)) +
                                 sum(-self.players.players[player].price[
                                     round + 1] * self.trade_out_vars[player][round]
                                     for player in range(self.num_players)) == 0,
                                 "Budget-{}".format(round))


    def add_non_negative_budget_constraints(self):
        """Of course the budget must always be non-zero"""

        for round in range(self.num_rounds):
            self.model.addConstr(self.budget_vars[round] >= 0,
                                 "Budget-NonNeg-{}".format(round))


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

        for player in self.players:
            player.first_name = player.first_name.title()
            player.last_name = player.last_name[:-5].title() + player.last_name[-5:].upper()

        with open(output_file, 'a') as f:

            self.model.printStats()
            # f.write(self.model.NumVars)

            trade_count = 0
            for round in range(self.num_rounds):
                f.write("\n-----------------\nRound {}\n".format(round + 1))

                # Points per round
                points_in_round = 0
                largest_point = 0
                for player_id, player in enumerate(self.players):

                    if self.scoring_vars[player_id][round].x > 0.5:
                        points_in_round = points_in_round + \
                                          self.players.players[player_id].points[
                                              round]
                        if player.points[round] > largest_point:
                            largest_point = player.points[round]

                    # for pos_index, pos in enumerate(self.positions):
                    #     if pos in self.scoring_positions:
                    #         if self.pos_vars[player_id][round][pos_index].x == 1:
                    #             points_in_round = points_in_round +
                    #             self.players.players[player_id].points[round]
                    #             if player.points[round] > largest_point:
                    #                 largest_point = player.points[round]

                points_in_round = points_in_round + largest_point

                f.write("Points {}\n".format(points_in_round))

                # Team Value
                team_value = 0
                for player_id, player in enumerate(self.players):
                    if self.player_vars[player_id][round].x == 1:
                        team_value = team_value + player.price[round]

                f.write("Team Value {}\n".format(team_value))

                # Budget
                f.write("Remaining budget {}\n".format(self.budget_vars[round].x))
                f.write("-----------------\n")

                # Trade in1
                change_in_budget = 0
                if (round > 0):
                    for player_id, player in enumerate(self.players):
                        if self.trade_in_vars[player_id][round - 1].x == 1 and \
                                self.trade_out_vars[player_id][round - 1].x == 0:
                            f.write(
                                "Trade in {} {} - ${}\n".format(player.first_name,
                                                                player.last_name,
                                                                player.price[
                                                                    round]))
                            trade_count = trade_count + 1
                            change_in_budget = change_in_budget - player.price[
                                round]

                    for player_id, player in enumerate(self.players):
                        if self.trade_out_vars[player_id][round - 1].x == 1 and \
                                self.trade_in_vars[player_id][round - 1].x == 0:
                            f.write(
                                "Trade out {} {} - ${}\n".format(player.first_name,
                                                                 player.last_name,
                                                                 player.price[
                                                                     round]))
                            change_in_budget = change_in_budget + player.price[
                                round]

                f.write("Change in budget {}\n".format(change_in_budget))

                f.write("-----------------\n")

                points_in_round = 0
                for player_id, player in enumerate(self.players):
                    if self.captain_vars[player_id][round].x == 1:
                        f.write("Captain {} {} with {} points\n".format(
                            player.first_name, player.last_name,
                            player.points[round]))
                        points_in_round = points_in_round + player.points[round]

                for pos_index, pos in enumerate(self.positions):

                    players_in_round = []
                    for player_id, player in enumerate(self.players):
                        if self.pos_vars[player_id][round][pos_index].x == 1:
                            players_in_round.append(player)

                            if self.scoring_vars[player_id][round].x == 1:
                                points_in_round += player.points[round]

                    players_in_round.sort(key=lambda x: x.points[round],
                                          reverse=True)
                    for player_id, player in enumerate(players_in_round):
                        player_name = player.first_name + " " + player.last_name

                        f.write("{:30} - {:4} - ${:5} - {:4}\n".format(player_name,
                                                                       player.points[
                                                                           round],
                                                                       player.price[
                                                                           round],
                                                                       pos))

                f.write("Points - {}\n".format(points_in_round))
                f.write("-----------------\n")

            f.write('\nTOTAL Points: {}\n'.format(self.model.objVal))
            f.write('Number of trades used {}\n'.format(trade_count))

            # sum(self.trade_out_vars[player][round].x - self.trade_out_vars[
            # player][round].x for player in range(self.num_players) for round in
            # range(self.num_rounds-1))))

            """
            for player_id, player in enumerate(self.players):
                if sum(self.player_vars[player_id][round] for round in range(
                self.num_rounds)) == 0:
                    print("{} {} not used\n".format(player.first_name, 
                    player.last_name))
            """


    def solve(self, num_threads, output_file):
        self.model.modelSense = GRB.MAXIMIZE

        # self.model.modelSense = GRB.MINIMIZE

        # self.model.setParam(GRB.Param.Threads, num_threads)
        self.model.setParam(GRB.Param.LogFile, output_file)
        self.model.setParam(GRB.Param.MIPGap, 1e-9)
        # self.model.setParam(GRB.Param.TimeLimit, 60)
        # self.model.setParam(GRB.Param.SolutionLimit, 1)
        self.model.optimize(self._next_solution_cb)
        self.write_results_to_file(output_file)
