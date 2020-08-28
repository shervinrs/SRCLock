from datetime import datetime
import multiprocessing
import signal
import logging

from networkx.utils import *
from graph_tool import Graph, topology
from collections import defaultdict
from dateutil.relativedelta import relativedelta


cnt = 0


def diff(t_a, t_b):
    t_diff = relativedelta(t_b, t_a)  # later/end time comes first!
    return '{h}h {m}m {s}s'.format(h=t_diff.hours, m=t_diff.minutes, s=t_diff.seconds)


@not_implemented_for('undirected')
def simple_cycles(G, wires, limit):
    def _unblock(thisnode, blocked, B):
        stack = set([thisnode])
        while stack:
            node = stack.pop()
            if node in blocked:
                blocked.remove(node)
                stack.update(B[node])
                B[node].clear()

    subG = type(G)(G.edges())
    sccs = list(nx.strongly_connected_components(subG))
    # print sccs
    while sccs:
        scc = sccs.pop()
        # order of scc determines ordering of nodes
        startnode = scc.pop()
        # Processing node runs "circuit" routine from recursive version
        path = [startnode]
        blocked = set()  # vertex: blocked from search?
        closed = set()   # nodes involved in a cycle
        blocked.add(startnode)
        B = defaultdict(set)  # graph portions that yield no elementary circuit
        stack = [(startnode, list(subG[startnode]))]  # subG gives comp nbrs
        # print stack
        while stack:
            thisnode, nbrs = stack[-1]

            # print path

            if nbrs and len(path) < limit:
                nextnode = nbrs.pop()
                if nextnode == startnode:
                    yield path[:]
                    closed.update(path)
                    # print "Found a cycle", path, closed
                elif nextnode not in blocked:
                    path.append(nextnode)
                    stack.append((nextnode, list(subG[nextnode])))
                    closed.discard(nextnode)
                    if len(path) != limit-1:
                        blocked.add(nextnode)
                    continue
            # done with nextnode... look for more neighbors
            if not nbrs or len(path) >= limit:  # no more nbrs
                if thisnode in closed:
                    _unblock(thisnode, blocked, B)
                else:
                    for nbr in subG[thisnode]:
                        if thisnode not in B[nbr]:
                            B[nbr].add(thisnode)
                stack.pop()
#                assert path[-1] == thisnode
                path.pop()
        # done processing this node
        subG.remove_node(startnode)
        H = subG.subgraph(scc)  # make smaller to avoid work in SCC routine
        sccs.extend(list(nx.strongly_connected_components(H)))


def my_imp(G, wires, limit):
    # working version
    # a simplified version of the code. it's slower for larger limits.
    subG = type(G)(G.edges())
    sccs = list(nx.strongly_connected_components(subG))
    # print sccs
    while sccs:
        scc = sccs.pop()
        # order of scc determines ordering of nodes
        startnode = scc.pop()
        # Processing node runs "circuit" routine from recursive version
        path = [startnode]
        blocked = set()  # vertex: blocked from search?
        blocked.add(startnode)
        stack = [(startnode, list(subG[startnode]))]  # subG gives comp nbrs
        # print stack
        while stack:
            thisnode, nbrs = stack[-1]

            if nbrs and len(path) < limit:
                nextnode = nbrs.pop()
                if nextnode == startnode:
                    yield path[:]
                elif nextnode not in blocked:
                    path.append(nextnode)
                    stack.append((nextnode, list(subG[nextnode])))
                    blocked.add(nextnode)
                    continue
            # done with nextnode... look for more neighbors
            if not nbrs or len(path) >= limit:  # no more nbrs
                blocked.remove(thisnode)
                stack.pop()
                path.pop()
        # done processing this node
        subG.remove_node(startnode)
        H = subG.subgraph(scc)  # make smaller to avoid work in SCC routine
        sccs.extend(list(nx.strongly_connected_components(H)))


def my_imp2(G, wires, limit):
    # TODO: not working yet
    def _unblock(thisnode, blocked, B):
        stack = set([thisnode])
        while stack:
            node = stack.pop()
            if node in blocked:
                blocked.remove(node)
                stack.update(B[node])
                B[node].clear()

    # added closed and unblock
    subG = type(G)(G.edges())
    sccs = list(nx.strongly_connected_components(subG))
    # print sccs
    while sccs:
        scc = sccs.pop()
        # order of scc determines ordering of nodes
        startnode = scc.pop()
        # Processing node runs "circuit" routine from recursive version
        path = [startnode]
        blocked = set()  # vertex: blocked from search?
        closed = set()   # nodes involved in a cycle
        blocked.add(startnode)
        B = defaultdict(set)  # graph portions that yield no elementary circuit
        stack = [(startnode, list(subG[startnode]))]  # subG gives comp nbrs
        # print stack
        while stack:
            thisnode, nbrs = stack[-1]

            #          [93, 228, 174, 229, 97, 211, 200, 210]
            # if path == [93, 228, 174]:
            #     print "here"

            if nbrs and len(path) < limit:
                nextnode = nbrs.pop()
                if nextnode == startnode:
                    yield path[:]
                    closed.update(path)
                elif nextnode not in blocked:
                    path.append(nextnode)
                    stack.append((nextnode, list(subG[nextnode])))
                    closed.discard(nextnode)
                    # if nextnode == 211:
                    #     print "here"
                    blocked.add(nextnode)
                    continue
            # done with nextnode... look for more neighbors
            if not nbrs or len(path) >= limit:  # no more nbrs
                if thisnode in closed or len(path) >= limit:
                    _unblock(thisnode, blocked, B)
                else:
                    for nbr in subG[thisnode]:
                        if thisnode not in B[nbr]:
                            B[nbr].add(thisnode)
                stack.pop()
                path.pop()
        # done processing this node
        subG.remove_node(startnode)
        H = subG.subgraph(scc)  # make smaller to avoid work in SCC routine
        sccs.extend(list(nx.strongly_connected_components(H)))


def get_cyclic_cone(wire_in, fanin_cone):
    if wire_in.type != "inp":
        if wire_in not in fanin_cone:
            fanin_cone.add(wire_in)
            for i in range(len(wire_in.operands)):
                get_cyclic_cone(wire_in.operands[i], fanin_cone)


def find_feedbacks(args, wires):
    # TODO: not working
    feedbacks = []

    for target in wires:
        if target.type != "inp":
            path_list = []
            fanin_cone = set()
            get_cyclic_cone(target, fanin_cone)
            fanin_cone = list(fanin_cone)

            source = None
            for j in range(len(fanin_cone)):
                if fanin_cone[j].type != "inp" and fanin_cone[j] != target:
                    if target in fanin_cone[j].operands:
                        source = fanin_cone[j]
                        break

            if source is not None:
                G = nx.DiGraph()
                lst = []
                for j in range(0, len(fanin_cone)):
                    lst.append(fanin_cone[j].name)

                G.add_nodes_from(lst)

                for j in range(len(fanin_cone)):
                    if fanin_cone[j].type != "inp":
                        for k in range(len(fanin_cone[j].operands)):
                            G.add_edges_from(zip([fanin_cone[j].operands[k].name], [fanin_cone[j].name]))

                print("srclock, target:", source.name, target.name)
                # for c in fanin_cone:
                #     print c.name

                cycles = []
                try:
                    cycles = list(nx.shortest_simple_paths(G, source.name, target.name))
                    # cycles = list(nx.find_cycle(G, [target.name]))

                except:
                    pass
                print(cycles, '\n')

                if len(cycles) != 0:
                    feedbacks.append(cycles)
            else:
                logging.warnings(target.name + " has no feedback")

    return feedbacks


def find_cycles(args, wires):
    # implemented with networkx
    G = nx.DiGraph()
    t_a = datetime.now()
    lst = []
    for i in range(0, len(wires)):
        lst.append(i)
    #print lst
    G.add_nodes_from(lst)

    for i in range(0, len(wires)):
        if wires[i].type != "inp":
            for j in range(len(wires[i].operands)):
                G.add_edges_from(zip([wires[i].operands[j].index], [wires[i].index]))

    cycles = list(nx.simple_cycles(G))
    t_b = datetime.now()
    print("time of finding cycles: " + diff(t_a, t_b))
    print("there are", len(cycles), "cycles")
    if args.p:
        print("list of cycles:")
        for cycle in cycles:
            tmp = ""
            for i in range(len(cycle)):
                tmp += wires[cycle[i]].name + " "
            print(tmp)
    return cycles


def signal_handler(signal, frame):
    print("INTERRUPTED: there are", str(cnt), "cycles")
    exit()


def cycle_count(args, wires):
    signal.signal(signal.SIGTERM, signal_handler)

    g = Graph()
    # t_a = datetime.now()
    lst = []
    for i in range(0, len(wires)):
        lst.append(g.add_vertex())

    for i in range(0, len(wires)):
        if wires[i].type != "inp":
            for j in range(len(wires[i].operands)):
                g.add_edge(lst[wires[i].operands[j].index], lst[wires[i].index])

    # cnt = 0
    global cnt
    cnt = 0
    cycles = []
    g_out = topology.all_circuits(g)

    try:
        for c in g_out:
            cnt += 1
            if args.p == 2:
                cycles.append(c.tolist())
    except KeyboardInterrupt:
        logging.critical("INTERRUPTED")

    logging.warning("there are " + str(cnt) + " cycles")
    if args.p > 1:
        logging.debug("list of cycles:")
        for cycle in cycles:
            tmp = ""
            for i in range(len(cycle)):
                tmp += wires[cycle[i]].name + " "
            logging.debug(tmp)
    return


def cycle_count_timeout(args, wires, timeout):
    p = multiprocessing.Process(target=cycle_count, name="cycle_count", args=(args, wires,))
    p.start()
    p.join(timeout)
    if p.is_alive():
        logging.critical("timeout: cycle_count is killed!")
        p.terminate()
        p.join()


def find_cycles2(args, wires):
    # implemented with graph-tools
    g = Graph()
    t_a = datetime.now()
    lst = []
    for i in range(0, len(wires)):
        lst.append(g.add_vertex())

    for i in range(0, len(wires)):
        if wires[i].type != "inp":
            for j in range(len(wires[i].operands)):
                g.add_edge(lst[wires[i].operands[j].index], lst[wires[i].index])

    cycles = []
    for c in all_circuits(g):
        if len(cycles) > 100000:
            logging.info("number of cycles is limited.")
            break
        cycles.append(c.tolist())

    t_b = datetime.now()
    logging.info("time of finding cycles: " + diff(t_a, t_b))
    logging.info("there are" + str(len(cycles)) + "cycles")
    if args.p:
        logging.info("list of cycles:")
        for cycle in cycles:
            tmp = ""
            for i in range(len(cycle)):
                tmp += wires[cycle[i]].name + " "
            logging.info(tmp)
        print()
    return cycles


def find_cycles3(args, wires):
    # new attack method considering cell timings
    G = nx.DiGraph()
    t_a = datetime.now()
    lst = []
    for i in range(0, len(wires)):
        lst.append(i)
    #print lst
    G.add_nodes_from(lst)

    for i in range(0, len(wires)):
        if wires[i].type != "inp":
            for j in range(len(wires[i].operands)):
                G.add_edges_from(zip([wires[i].operands[j].index], [wires[i].index]))

    cycles = list(my_imp(G, wires, args.l))
    t_b = datetime.now()
    print("time of finding cycles: " + diff(t_a, t_b))
    print("there are " + str(len(cycles)) + " cycles")
    if args.p:
        print("list of cycles:")
        for cycle in cycles:
            tmp = ""
            for i in range(len(cycle)):
                tmp += wires[cycle[i]].name + " "
            print(tmp)
        print()
    return cycles