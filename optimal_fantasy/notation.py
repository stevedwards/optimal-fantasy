from mip import BINARY, CONTINUOUS
from collections import defaultdict

def process_data(d, p):
    """Processing the data (d) and parameters (p)"""

    rounds = list(range(1, p["rounds"] + 1))
    positions = set(p["scoring positions"]) | set(p["substitute positions"])
    return {
        "players": set(d.keys()),
        "positions": positions,
        "scoring positions": set(p["scoring positions"]),
        "substitute positions": set(p["substitute positions"]),
        "players eligible in position q": {
            q_: set(player for player, x in d.items() if q in x["positions"])
            for q in p["scoring positions"] for q_ in [q, "SUB "+q]
        },
        "positions eligible to player p": {
            player: set(x["positions"]) | set(["SUB " + y for y in x["positions"]])
            for player, x in d.items()
        },
        "rounds": rounds,
        "trade limit per season": p["trades"]["total"],
        "trade limit in round r": defaultdict(lambda: p["trades"]["default"], {
            int(key): int(value) for key, value in p["trades"]["exceptions"].items()
        }),
        "players required in position q": p["capacities"],
        "scoring positions in round r": defaultdict(lambda: p["number of scoring positions"]["default"], {
            int(key): int(value) for key, value in p["number of scoring positions"]["exceptions"].items()
        }),
        "starting budget": p["starting budget"],
        "points scored by player p in round r": {
            (player, r): x["points"][str(r)]
            for player, x in d.items()
            for r in rounds
        },
        "value of player p in round r": {
            (player, r): x["price"][str(r)]
            for player, x in d.items()
            for r in rounds
        },
        "score to beat": p.get("score to beat", None),
        "slots of position q": {q: range(p["capacities"][q]) for q in p["substitute positions"]},
        "emergencies limit": p["emergencies"]
    }


def binary(m):
    return m.add_var(var_type=BINARY)


def continuous(m):
    return m.add_var(var_type=CONTINUOUS)

def declare_constraints(model, constraints):
    for name, constraint_set in constraints.items():
        for nb, constraint in enumerate(constraint_set):
            model += constraint, f"{name}-{nb}"
    return constraints

def remove_constraint_set(model, name):
    for nb in range(len(model.constraints.pop(name))):
        model.remove(model.constr_by_name(f"{name}-{nb}"))