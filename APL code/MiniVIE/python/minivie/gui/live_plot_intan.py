# Simple plot function for showing the EMG stream
# Requires matplotlib
#
# To run from command line:
# > python -m gui.live_plot_intan

import logging
import os
import sys
from typing import Iterable

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.artist import Artist

# Set up path
if os.path.split(os.getcwd())[1] == "gui":
    sys.path.insert(0, os.path.abspath(".."))

from inputs.intan.intan_client import IntanUdp

logger = logging.getLogger("live_plot_intan")


def animate(frame, *fargs) -> Iterable[Artist]:
    lines, intan = fargs

    d = intan.get_data() * 1  # *1 for a shallow copy

    # Flip data for plotting most recent data from right to left
    for iChannel in range(0, intan.num_channels):
        d[:, iChannel] = d[::-1, iChannel] + (1 * (iChannel + 1))

    # Set the plot data
    for ch in range(intan.num_channels):
        lines[ch].set_data(range(intan.num_samples), d[:, ch])

    # Print the EMG sample rate
    print("EMG: {:0.2f} Hz".format(intan.get_data_rate_emg()))

    return lines


def main():
    # Set up data source
    intan = IntanUdp(num_samples=500)
    intan.connect()
    num_samples = intan.num_samples

    # Set up plot
    style.use("dark_background")
    fig = plt.figure("EMG Preview")
    ax = fig.add_subplot(1, 1, 1)

    plt.xlabel("Samples")
    plt.ylabel("Voltage, microvolts")
    plt.title("EMG Stream")
    plt.xlim(0, num_samples)
    plt.ylim(-8000, 8000)
    plt.grid(linewidth="0.5")

    lines = []

    # Initialize plot
    for ch in range(intan.num_channels):
        line = ax.plot([], [], label=str(ch))[0]
        lines.append(line)
    ax.legend(handles=lines, loc="upper left")

    ani = animation.FuncAnimation(fig, animate, interval=150, fargs=(lines, intan))
    plt.show()
    intan.close()


if __name__ == "__main__":
    # Configure logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        main()
    except KeyboardInterrupt:
        plt.close("all")
        sys.exit(0)
