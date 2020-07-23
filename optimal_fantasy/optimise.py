import click
from read import read_data
import datetime
import json
from mip_complete import build_model

threads = 4
data_file = "data/data2019-SC.csv"
round = 23
with open("parameters.json", 'r') as f:
    parameters = json.load(f)
players = read_data(data_file)
current_time = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
output_file = current_time + "-SuperCoachOutput.txt"
print(players)
print(parameters)
#mip = MIP.MIP(players, 2017, round, "SC")
#mip.solve(threads, output_file)
