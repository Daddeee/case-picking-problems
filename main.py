import networkx
import json
import sys
import matplotlib.pyplot as plt
from draw import build_graph_and_draw_warehouse

if len(sys.argv) > 4 or len(sys.argv) < 2:
    print("Usage: python main.py config_file [solution_file] [num_route_to_display]")
    sys.exit(1)

config_file = sys.argv[1]
solution_file = None
num_route_to_display = None
if len(sys.argv) > 2:
    solution_file = sys.argv[2]
    if len(sys.argv) > 3:
        num_route_to_display = int(sys.argv[3])


G,_ = build_graph_and_draw_warehouse(config_file, solution_file, num_route_to_display)

plt.show()
