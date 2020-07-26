
def print_solution(m, data, output_file):
    with open(output_file, 'w') as f:
        num_rounds = data["rounds"]
        f.write(f"{num_rounds}")
        trade_count = 0
        total_points = 0
        for round in range(1, num_rounds+1):
            # Points per round
            points_in_round = 0
            largest_point = 0
            for player in d["players"]:
                for pos_index, pos in enumerate(model._positions):
                    if pos in data["scoring positions"]:
                        if model.variables["pos_vars"][player_id][round][pos_index] >= 0.5:
                            points_in_round = points_in_round + \
                                            model._players.players[
                                                player_id].points[
                                                round]
                            if player.points[round] > largest_point:
                                largest_point = player.points[round]
            f.write(f"\n-----------------\nRound {round}\n")
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
            f.write(f"""Points - {}\n""".format(points_in_round))
            f.write("-----------------\n")
        f.write('\nTOTAL Points: {}\n'.format(total_points))
        f.write('Number of trades used {}\n'.format(trade_count))