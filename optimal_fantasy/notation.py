from mip import BINARY, CONTINUOUS


def process_data(d, p):
    """Processing the data"""
    rounds = p["trades"]["total"]
    return {
        "Set of players P": set(d.keys()),
        "Set of positions Q": set(p["scoring positions"])
        + set(p["substitute positions"]),
        "Subset of players P_q eligible in position q": {
            q: set(player for player, x in d.items() if q in x["positions"])
            for q in p["scoring positions"]
        },
        "Subset of positions Q_p eligible to player p": {
            player: set(x["positions"]) for player, x in d.items()
        },
        "Set of rounds R": list(range(1, p["rounds"] + 1)),
        "Trades allowed per season": rounds,
        "Trades T_r allowed in round r": {
            r: p["rounds"]["bye"] if r in p["bye rounds"] else p["rounds"]["default"]
            for r in rounds
        },
        "Number of players required in position q": p["capacities"],
        "Number of scoring positions in round r": {
            r: p["number of scoring positions"]["bye"]
            if r in p["bye rounds"]
            else p["number of score positions"]["default"]
            for r in rounds
        },
        "Starting budget for first round": p["starting budget"],
        "Points scored by player p in round r": {
            player: x["points"] for player, x in d.items()
        },
        "Value of player p in round r": {
            player: x["price"] for player, x in d.items()
        }
    }


def binary(m):
    return m.add_var(var_type=BINARY)


def continuous(m):
    return m.add_var(var_type=CONTINUOUS)


def declare_constraints(model, constraints):
    for constraint_set in constraints.values():
        for constraint in constraint_set:
            model += constraint
    return constraints
