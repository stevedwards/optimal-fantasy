import click
import datetime
import json
from optimal_fantasy.models import mip_budget, mip_ghost, mip_complete
from optimal_fantasy.notation import process_data
from os import environ

@click.command()
@click.argument("solve_type")
def solve(solve_type):

    assert solve_type in ["ghost", "budget", "complete"]

    with open("optimal_fantasy/data/parameters.json", "r") as f:
        parameters = json.load(f)
    with open("optimal_fantasy/data/player_data2020.json", "r") as f:
        player_data = json.load(f)
    # Process data to get in arithmetic format
    data = process_data(player_data, parameters)
    if solve_type == "ghost":
        m = mip_ghost.model(data)
    elif solve_type == "complete":
        m = mip_complete.model(data)
    elif solve_type == "budget":
        m = mip_budget.model(data)
    else:
        raise ValueError("Incorrect solve type")

    m.setParam("TimeLimit", 900)
    
    msol = m.optimize()
    mip_complete.save_as_json(m, data, "my.json")

solve()  # pylint: disable=no-value-for-parameter
