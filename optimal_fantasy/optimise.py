import click
import datetime
import json
from optimal_fantasy.models.mip_budget import budget_model
from optimal_fantasy.notation import process_data

# current_time = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
# output_file = current_time + "-SuperCoachOutput.txt"

with open("parameters.json", 'r') as f:
    parameters = json.load(f)

with open("data/player_data2020.json", 'r') as f:
    player_data = json.load(f)

# Infer rounds from player data if not given as a parameter
if parameters["rounds"] is None:
    parameters["rounds"] = len(next(iter(player_data.values()))['price'])

data = process_data(player_data, parameters)
m = budget_model(data)
m.optimize()