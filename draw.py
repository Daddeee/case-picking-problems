import matplotlib.pyplot as plt
import networkx as nx
import json
import re
import ast


def parse_x_varname(s):
    pattern = r"x\[\s*(\(.*?\))\s*,\s*(\(.*?\))\s*,\s*([^,\]]+)\s*\]"

    match = re.match(pattern, s)
    if match:
        # Extract the parts as strings
        tuple1_str = match.group(1)
        tuple2_str = match.group(2)
        third_str = match.group(3).strip()
        
        # Convert the tuple strings to actual tuple objects
        tuple1 = ast.literal_eval(tuple1_str)
        tuple2 = ast.literal_eval(tuple2_str)
        
        # Since the last element is not quoted, we convert it to a string.
        # If it were quoted (e.g. "'l_9'"), ast.literal_eval would handle it.
        if not ((third_str.startswith("'") and third_str.endswith("'")) or 
                (third_str.startswith('"') and third_str.endswith('"'))):
            third = third_str
        else:
            third = ast.literal_eval(third_str)
        
        return tuple1, tuple2, third
    else:
        raise ValueError(f"Invalid x variable name: {s}")
    
def parse_u_varname(s):
    pattern = r"v\[\s*(\(.*?\))\s*,\s*([^,\]]+)\s*\]"

    match = re.match(pattern, s)
    if match:
        # Extract the parts as strings
        tuple1_str = match.group(1)
        second_str = match.group(2).strip()
        
        # Convert the tuple strings to actual tuple objects
        tuple1 = ast.literal_eval(tuple1_str)
        
        # Since the last element is not quoted, we convert it to a string.
        # If it were quoted (e.g. "'l_9'"), ast.literal_eval would handle it.
        if not ((second_str.startswith("'") and second_str.endswith("'")) or 
                (second_str.startswith('"') and second_str.endswith('"'))):
            second = second_str
        else:
            second = ast.literal_eval(second_str)
        
        return tuple1, second
    else:
        raise ValueError(f"Invalid u variable name: {s}")

def build_graph_and_draw_warehouse(config_file, solution_file=None, num_route_to_display=None):
    """
    Draws a 2D representation of a parallel-aisle warehouse with locations on both sides of each aisle
    and a graph representation of the aisles.

    Parameters:
        config_file (str): Path to the JSON file specifying warehouse parameters and storage.
    """
    # Load configuration and storage
    with open(config_file, 'r') as f:
        config = json.load(f)

    num_aisles = config['num_aisles']
    locations_per_aisle = config['locations_per_aisle'] if 'locations_per_aisle' in config else config['num_cells']
    aisle_draw_size = config['aisle_draw_size'] if 'aisle_draw_size' in config else 2
    location_draw_size = config['location_draw_size'] if 'location_draw_size' in config else 1
    storage_data = config['storage']

    if isinstance(storage_data, dict):
        storage_data = list(storage_data.values())

    # Create a plot
    fig, ax = plt.subplots(figsize=(15, locations_per_aisle * location_draw_size / 2))

    # Create a graph
    G = nx.Graph()

    # Parse storage data
    storage_map = {}
    for item in storage_data:
        color = item['color']
        if isinstance(item['storage'], dict):
            locs = item['storage']['loc']
            for i in range(len(locs)):
                loc = locs[i]
                qty = item['storage']['quantity'][i]
                key = (loc[0]-1, loc[1]-1, loc[2])
                storage_map[key] = {'color': color, 'quantity': qty}
        else:
            for loc in item['storage']:
                key = (loc['aisle'], loc['loc'], loc['side'])
                storage_map[key] = {'color': color, 'quantity': loc['quantity']}

    # Draw warehouse layout and add nodes/edges to the graph
    for aisle in range(num_aisles):
        aisle_x_left = aisle * (aisle_draw_size + 2 * location_draw_size)
        aisle_x_right = aisle_x_left + location_draw_size + aisle_draw_size

        node_x = aisle_x_left + location_draw_size + aisle_draw_size / 2

        # Add node for the start of aisle
        G.add_node((aisle, 0), pos=(node_x, location_draw_size / 2))

        for loc in range(locations_per_aisle):
            loc_y = (loc + 1) * location_draw_size

            # Left side locations
            left_key = (aisle, loc, 'left')
            left_color = storage_map.get(left_key, {}).get('color', 'none')
            left_quantity = storage_map.get(left_key, {}).get('quantity', None)
            left_item = storage_map.get(left_key, {}).get('item', None)
            left_rect = plt.Rectangle((aisle_x_left, loc_y), location_draw_size, location_draw_size, edgecolor='black', facecolor=left_color)
            ax.add_patch(left_rect)
            if left_quantity:
                ax.text(aisle_x_left + location_draw_size / 2, loc_y + location_draw_size / 2, str(left_quantity), ha='center', va='center', fontsize=8)

            # Right side locations
            right_key = (aisle, loc, 'right')
            right_color = storage_map.get(right_key, {}).get('color', 'none')
            right_quantity = storage_map.get(right_key, {}).get('quantity', None)
            right_item = storage_map.get(right_key, {}).get('item', None)
            right_rect = plt.Rectangle((aisle_x_right, loc_y), location_draw_size, location_draw_size, edgecolor='black', facecolor=right_color)
            ax.add_patch(right_rect)
            if right_quantity:
                ax.text(aisle_x_right + location_draw_size / 2, loc_y + location_draw_size / 2, str(right_quantity), ha='center', va='center', fontsize=8)

            # Add graph nodes for aisle points
            n = (aisle, loc+1)
            G.add_node(n, pos=(node_x, loc_y + location_draw_size / 2), storage={
                'left': {'item': left_item, 'quantity': left_quantity},
                'right': {'item': right_item, 'quantity': right_quantity}
            })

            # Add vertical edges if not the first location
            G.add_edge((aisle, loc), n)

        # Add node for the end of aisle
        G.add_node((aisle, locations_per_aisle + 1), pos=(node_x, (locations_per_aisle + 1) * location_draw_size + location_draw_size / 2), storage=None)
        G.add_edge((aisle, locations_per_aisle), (aisle, locations_per_aisle + 1))

        # Add horizontal edges between adjacent aisles
        if aisle > 0:
            G.add_edge((aisle - 1, 0), (aisle, 0))
            G.add_edge((aisle - 1, locations_per_aisle + 1), (aisle, locations_per_aisle + 1))

    # Draw the boundary around the entire warehouse
    warehouse_width = num_aisles * (aisle_draw_size + 2 * location_draw_size)
    warehouse_height = (2 + locations_per_aisle) * location_draw_size 
    boundary = plt.Rectangle((0, 0), warehouse_width, warehouse_height, edgecolor='black', facecolor='none', linewidth=2)
    ax.add_patch(boundary)

    # Set plot limits
    ax.set_xlim(-location_draw_size, warehouse_width + location_draw_size)
    ax.set_ylim(-location_draw_size, warehouse_height + location_draw_size)

    # Draw the graph
    pos = nx.get_node_attributes(G, 'pos')

    
    if solution_file is not None:
        with open(solution_file, 'r') as f:
            sol = json.load(f)

        u_vars = [v for v in sol['Vars'] if v['VarName'][0:1] == 'v']

        
        u_by_k = {}
        for u in u_vars:
            i, k = parse_u_varname(u['VarName'])
            val = int(u['X'])
            if k not in u_by_k:
                u_by_k[k] = []
            u_by_k[k].append((i, val))

        route_colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'p', 'o', 'w']

        labels = {}
        num_routes = 0
        for k in u_by_k:
            u_by_k[k] = sorted(u_by_k[k], key=lambda x: x[1])
            if len(u_by_k[k]) <= 1:
                continue

            num_k = int(k.replace('l_', ''))

            if num_route_to_display is not None and num_route_to_display != num_k:
                continue

            color = route_colors[num_k % len(route_colors)]

            prev = (1, 0)
            cnt = 1
            for i in range(1, len(u_by_k[k])):
                curr = u_by_k[k][i][0]
                np = (prev[0]-1, prev[1])
                nc = (curr[0]-1, curr[1])

                if nc in labels:
                    labels[nc] += ", " + str(cnt)
                else:
                    labels[nc] = str(cnt)
                
                cnt += 1

                if np not in G.nodes:
                    wrong_cnt += 1
                    print("Invalid node prev:", np)

                if nc not in G.nodes:
                    wrong_cnt += 1
                    print("Invalid node cur:", nc)

                # path = nx.shortest_path(G, source=np, target=nc)
                # path_edges = list(zip(path, path[1:]))
                G.add_edge(np, nc, color=color)
                prev = curr

            G.add_edge((prev[0]-1, prev[1]), (0,0), color=color)


    edges = G.edges()
    overlay_edges = [(u, v) for u, v in edges if 'color' in G[u][v]]
    normal_edges = [(u, v) for u, v in edges if 'color' not in G[u][v]]
    
    colors = [G[u][v]['color'] if 'color' in G[u][v] else 'black' for u,v in overlay_edges]

    nx.draw(G, pos, node_size=50, node_color='black', ax=ax, edgelist=normal_edges, edge_color='black')
    nx.draw_networkx_edges(G, pos, edgelist=overlay_edges, edge_color=colors, width=2)

    pos_labels = { k: (v[0] + 0.3, v[1] + 0.3) for k, v in pos.items() }

    nx.draw_networkx_labels(G,pos_labels,labels,font_color='black')

    # Add grid and labels
    ax.set_aspect('equal')
    ax.axis('off')

    return G,(fig, ax)

if __name__ == '__main__':
    G, _ = build_graph_and_draw_warehouse("config.json")
    plt.show()
