import click
import datetime
import json
from models.mip_complete import model
from notation import process_data

# current_time = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
# output_file = current_time + "-SuperCoachOutput.txt"

with open("parameters.json", 'r') as f:
    parameters = json.load(f)

with open("data/player_data2010.json", 'r') as f:
    player_data = json.load(f)

data = process_data(player_data, parameters)
model(data)