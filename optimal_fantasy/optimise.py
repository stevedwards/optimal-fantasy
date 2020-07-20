import click
from read import read_data
import datetime
from mip.complete import MIP

threads = 4
print("You have specified {} threads".format(threads))
data_file = "data2019-Final.csv"
round = 23
players = read_data(data_file)
current_time = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
output_file = current_time + "-SuperCoachOutput.txt"
print(data_file)
mip = MIP.MIP(players, 2017, round, "SC")
mip.solve(threads, output_file)
