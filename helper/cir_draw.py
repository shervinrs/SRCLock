import argparse
from srclock import circuit

import json
import networkx as nx
from networkx.readwrite import json_graph
from helper import http_server
import os


def dot_draw_tag(args, wires, cycles_list):
    c_i = None
    for w in wires:
        if w.name == "G871gat":
            c_i = w
            break

    if c_i:
        cone = circuit.get_bfs(wires, c_i)
    else:
        cone = wires
    print("cone size for dot output:", len(cone))

    G = nx.DiGraph()
    for w in cone:
        # lst.append(wires[i].name)
        if w.mark == 1:
            G.add_node(w.name, style='filled', fillcolor='darkorange')
        elif "_enc" in w.name:
            G.add_node(w.name, style='filled', fillcolor='darksalmon')
        elif w.tag == 2:
            G.add_node(w.name, style='filled', fillcolor='cyan')
        else:
            G.add_node(w.name)

    for i in range(0, len(cone)):
        if cone[i].type != "inp":
            for j in range(len(cone[i].operands)):
                G.add_edges_from(zip([cone[i].operands[j].name], [cone[i].name]))

    for cycle in cycles_list:
        for j in range(len(cycle)-1):
            i1 = cycle[j]
            i2 = cycle[j+1]
            G[wires[i2].name][wires[i1].name]['color'] = 'red'

    write_path = "/home/shervinrs/Downloads/cir"
    nx.nx_agraph.write_dot(G, write_path + ".dot")
    os.system("dot -Tsvg " + write_path + ".dot -o " + write_path + ".svg")


def dot_draw(args, wires):
    c_i = None
    for w in wires:
        if w.name == "G871gat":
            c_i = w
            break

    if c_i:
        cone = srclock.get_bfs(wires, c_i)
    else:
        cone = wires
    print("cone size for dot output:", len(cone))

    # implemented with networkx
    G = nx.DiGraph()
    for w in cone:
        # lst.append(wires[i].name)
        if w.type == "inp":
            if "keyinput" in w.name:
                G.add_node(w.name, style = 'filled', shape = 'rectangle', fillcolor = 'darkolivegreen1')
            else:
                G.add_node(w.name, style='filled', shape = 'rectangle', fillcolor='darkolivegreen3')
        elif w.type == "mux" or "keyinput" in w.name:
            G.add_node(w.name, style='filled', fillcolor='lightpink3')
        else:
            G.add_node(w.name)

    for i in range(0, len(cone)):
        if cone[i].type != "inp":
            for j in range(len(cone[i].operands)):
                G.add_edges_from(zip([cone[i].operands[j].name], [cone[i].name]))

    # G['G876gat']['G879gat']['color'] = 'red'
    # G.node['G879gat']['shape'] = 'circle'
    # G.node['G879gat']['style'] = 'filled'
    # G.node['G879gat']['fillcolor'] = 'red'

    write_path = "/home/shervinrs/Downloads/cir"
    nx.nx_agraph.write_dot(G, write_path + ".dot")
    os.system("dot -Tsvg " + write_path + ".dot -o " + write_path + ".svg")


def d3_draw(args, wires):
    # implemented for d3
    G = nx.DiGraph()
    lst = []
    for i in range(0, len(wires)):
        lst.append(i)
    G.add_nodes_from(lst)

    for i in range(0, len(wires)):
        if wires[i].type != "inp":
            for j in range(len(wires[i].operands)):
                # G.add_edges_from(zip([wires[i].operands[j].index], [wires[i].index]))
                for z in range(0, len(wires)):
                    if wires[i].operands[j].index == wires[z].index:
                        G.add_edges_from([(z, i)])
                        break

    # so add a name to each node
    for n in G:
        G.node[n]['name'] = wires[n].name
        G.node[n]['type'] = wires[n].type
        G.node[n]['logic_level'] = wires[n].logic_level
        G.node[n]['delay'] = round(wires[n].delay, 2)
        G.node[n]['slack'] = round(wires[n].slack, 2)
    # write json formatted data
    d = json_graph.node_link_data(G)  # node-link format to serialize
    # write json
    json.dump(d, open('force/force.json', 'w'))
    print('Wrote node-link JSON data to force/force.json')
    # open URL in running web browser
    http_server.load_url('force/force.html')
    print('Or copy all files in force/ to webserver and load force/force.html')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This is for removing cycles from obfuscated circuit.')
    parser.add_argument("-b", action="store", required=True, type=str, help="original benchmark path")
    args = parser.parse_args()

    circuit, wires = circuit.simple_read_bench(args.b)

    # d3_draw(args, wires)
    dot_draw(args, wires)
    exit()
