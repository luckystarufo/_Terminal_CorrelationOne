import matplotlib.pyplot as plt
import numpy as np
import argparse
import sys
import os

# size of the playground
x_bdry = 27
y_bdry = 13


def create_arg_parser():
    """"Creates and returns the ArgumentParser object."""

    parser = argparse.ArgumentParser(description='Generate the picture of your defensive system!')
    parser.add_argument('dataDirectory', help='Path to the data directory')
    return parser


# create figure object
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(1, 1, 1)
ax.set_facecolor('k')

# plot the grids on our side
for i in np.arange(0, x_bdry+1):
    if i <= y_bdry:
        j_start = y_bdry - i
    else:
        j_start = i - y_bdry - 1
    for j in np.arange(j_start, y_bdry+1):
        ax.scatter(i, j, marker=',', c='c', s=3, alpha=1.0)

# read defensive units data
arg_parser = create_arg_parser()
parsed_args = arg_parser.parse_args(sys.argv[1:])
if os.path.exists(parsed_args.dataDirectory):
    f = open(parsed_args.dataDirectory+'/defensive_data.txt')
    defensive_data = eval(f.read())
    f.close()

# add FILTERS
filter_locations = defensive_data['filter_locations']
for filter_location in filter_locations:
    ax.scatter(*filter_location, s=30, facecolors='none', edgecolors='c', linewidths=2, alpha=0.8)

# add DESTRUCTORS
destructor_locations = defensive_data['destructor_locations']
for destructor_location in destructor_locations:
    ax.scatter(*destructor_location, s=30, facecolors='none', edgecolors='c', linewidths=1.5, alpha=0.6)
    ax.scatter(*destructor_location, s=250, facecolors='none', edgecolors='c', linewidths=1.0, alpha=1.0)

# add ENCRYPTERS
encrypter_locations = defensive_data['encrypter_locations']
for encrypter_location in encrypter_locations:
    ax.scatter(*encrypter_location, s=30, facecolors='none', edgecolors='c', linewidths=1.5, alpha=0.4)
    ax.scatter(*encrypter_location, s=200, facecolors='none', edgecolors='c', linewidths=3.0, alpha=0.4)

# maybe read information units data and add to the plot later ...?

# save image
plt.savefig(parsed_args.dataDirectory+'/defensive_img.png')
