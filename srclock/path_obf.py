import copy
import operator
from random import randint
from datetime import datetime
import logging

from cycsat import cycsat_util
from helper import cir_draw
from srclock import circuit_timing as ct, my_util, circuit


def get_dfs(wires, head):
    # TODO: NOT WORKING
    nodes = []
    stack = [wires[head].index]
    while stack:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        n = len(wires[cur_node].operands)
        for i in range(n):
            stack.insert(0, wires[n-i].index)
    return nodes


def get_bfs(wires, head):
    visited, queue = [], [head]
    while queue:
        vertex = queue.pop(0)
        if vertex not in visited:
            visited.append(vertex)
            for v in vertex.operands:
                if v.type != "inp":
                    queue.append(v)
    return visited


def print_cyclification_info(args, tag_cnt, cycles_list, stage):
    logging.info("stage is: " + stage)

    # cir_draw.dot_draw_tag(args, wires, cycles_list, stage)

    my_util.write_output(wires, tag_cnt, args.b, args.m)

    # read the output and compute number of cycles
    num_of_path = tag_cnt
    bench_address = args.b
    bench_folder = bench_address[0: bench_address.find("original/")]
    bench_file_name = bench_address[bench_address.find("original/") + 9: bench_address.find(".bench")]
    new_bench_address = bench_folder + args.m + "/" + bench_file_name + "_" + str(num_of_path) + ".bench"
    cir, wires_tmp = circuit.simple_read_bench(new_bench_address)
    # cycsat_util.cycle_count_timeout(args, wires_tmp, 10800)


def print_cone_timing(target_circuit, wires, wire):
    # cone_temp = circ_func.get_bfs(wires[wire.index], 4000)
    cone_temp = wires
    # print "printing cone information for:", wire.name
    for i in range(1, target_circuit.max_level+1):
        logging.info("level=" + str(i))
        for j in range(0, len(cone_temp)):
            if cone_temp[j].logic_level == i:
                logging.info("wire_name:" + cone_temp[j].name + "cell_type:" + cone_temp[j].type + "#inputs:" + len(cone_temp[j].operands) + \
                    "slack:" + cone_temp[j].slack + "path_delay:" + cone_temp[j].delay + "mark:" + cone_temp[j].mark)


def timing_aware_setup(target_circuit, wires):
    target_circuit.b2b = True

    # find output cone indexes
    target_circuit.cone_index = circuit.largest_cone(wires)
    ct.sta(target_circuit, wires)


def ta1_exp(args, target_circuit, wires):
    m_cycles = args.n
    cycle_length = args.l
    c_i = 0
    slack_threshold = 0.06 - target_circuit.clk_period * (float(args.d) / 100)
    cycles_list = []
    while len(cycles_list) < m_cycles and c_i < len(target_circuit.cone_index):
        cone = get_bfs(wires, wires[target_circuit.cone_index[c_i]])
        logging.info(wires[target_circuit.cone_index[c_i]].name + " is selected as head for creating loops")

        if args.p > 2:
            tmp = "bfs: "
            for c in cone:
                tmp += c.name + " "
            logging.info(tmp)

        # mark = 0 --> available for selection
        # mark = 1 --> switch inserted
        # mark = 2 --> candidate for insertion
        # mark = 3 --> middle of selected cycle
        while cone and len(cycles_list) < m_cycles:
            curr = cone.pop(0)
            # print curr.name
            if curr.mark == 0 and curr.logic_level > cycle_length and curr.slack >= slack_threshold:
                created_cycle = [curr.index]
                curr.mark = 2
                # TODO: it should be corrected, for the current code, it cannot check timing of the first switch
                # because of curr.mark = 2 and not curr.mark = 1
                # ct.sta(target_circuit, wires)

                # dfs here
                dfs_completed = False
                while not dfs_completed and len(created_cycle) < cycle_length:
                    inserted = False
                    for j in range(len(curr.operands)):
                        if curr.operands[j].logic_level > cycle_length - len(created_cycle):
                            if curr.operands[j].mark == 0 and curr.operands[j].slack >= slack_threshold:
                                if curr.operands[j] in cone:
                                    curr = curr.operands[j]
                                    created_cycle.append(curr.index)
                                    curr.mark = 2
                                    inserted = True
                                    break

                    if not inserted:
                        # this is a dead end
                        if len(created_cycle) > 1:
                            # print created_cycle
                            # print wires[created_cycle[-1]].name
                            #
                            # tmp = "cone: "
                            # for c in cone:
                            #     tmp += c.name + " "
                            # print(tmp)

                            # cone.remove(wires[created_cycle[-1]])
                            created_cycle.pop()
                            # curr.mark = 0
                            curr = wires[created_cycle[-1]]
                        else:
                            dfs_completed = True

                if len(created_cycle) > 3:
                    # mark middle wires
                    for j in range(1, len(created_cycle) - 1):
                        wires[created_cycle[j]].mark = 3
                    # end of the cycle should be selected for switch insertion
                    wires[created_cycle[0]].mark = 1
                    wires[created_cycle[-1]].mark = 1
                    ct.sta(target_circuit, wires)
                    cycles_list.append(created_cycle)

                    tmp = "cycle " + str(len(cycles_list)) + ": "
                    for j in range(len(created_cycle)):
                        tmp += wires[created_cycle[j]].name + " "
                    logging.info(tmp)

            for n in cone:
                if n.mark == 2:
                    n.mark = 0
        c_i += 1
    return cycles_list


def ta1(args, target_circuit, wires):
    m_cycles = args.n
    cycle_length = args.l
    c_i = 0
    slack_threshold = 0.06 - target_circuit.clk_period * (float(args.d) / 100)
    cycles_list = []
    while len(cycles_list) < m_cycles and c_i < len(target_circuit.cone_index):
        cone = get_bfs(wires, wires[target_circuit.cone_index[c_i]])
        logging.info(wires[target_circuit.cone_index[c_i]].name + " is selected as head for creating loops")

        if args.p == 2:
            tmp = "bfs: "
            for c in cone:
                tmp += c.name + " "
            logging.info(tmp)

        # mark = 0 --> available for selection
        # mark = 1 --> switch inserted
        # mark = 2 --> candidate for insertion
        # mark = 3 --> middle of selected cycle
        while cone and len(cycles_list) < m_cycles:
            curr = cone.pop(0)
            # print curr.name
            if curr.mark == 0 and curr.logic_level > cycle_length and curr.slack >= slack_threshold:
                created_cycle = [curr.index]
                curr.mark = 1
                ct.sta(target_circuit, wires)

                # dfs here
                dfs_completed = False
                while not dfs_completed and len(created_cycle) < cycle_length:
                    inserted = False
                    for j in range(len(curr.operands)):
                        if curr.operands[j].logic_level > cycle_length - len(created_cycle):
                            if curr.operands[j].mark == 0 and curr.operands[j].slack >= slack_threshold:
                                if curr.operands[j] in cone:
                                    curr = curr.operands[j]
                                    created_cycle.append(curr.index)
                                    curr.mark = 2
                                    inserted = True
                                    break

                    if not inserted:
                        # this is a dead end
                        if len(created_cycle) > 1:
                            # print created_cycle
                            # print wires[created_cycle[-1]].name
                            #
                            # tmp = "cone: "
                            # for c in cone:
                            #     tmp += c.name + " "
                            # print(tmp)

                            cone.remove(wires[created_cycle[-1]])
                            created_cycle.pop()
                            curr = wires[created_cycle[-1]]
                        else:
                            dfs_completed = True

                if len(created_cycle) > 4:
                    # mark middle wires
                    for j in range(1, len(created_cycle) - 1):
                        wires[created_cycle[j]].mark = 3
                    # end of the cycle should be selected for switch insertion
                    wires[created_cycle[-1]].mark = 1
                    ct.sta(target_circuit, wires)
                    cycles_list.append(created_cycle)

                    tmp = "cycle " + str(len(cycles_list)) + ": "
                    for j in range(len(created_cycle)):
                        tmp += wires[created_cycle[j]].name + " "
                    logging.info(tmp)

                for n in cone:
                    if n.mark == 2:
                        n.mark = 0

                # ct.sta(target_circuit, wires)
        c_i += 1
    return cycles_list


def ta2(args, target_circuit, wires):
    m_cycles = args.n
    cycle_length = args.l
    c_i = 0
    slack_threshold = 0.06 - target_circuit.clk_period * (float(args.d) / 100)
    cycles_list = []
    while len(cycles_list) < m_cycles and c_i < len(target_circuit.cone_index):
        # cone = circ_func.get_bfs(wires[target_circuit.cone_index[c_i]], 4000)
        cone = get_bfs(wires, wires[target_circuit.cone_index[c_i]])
        logging.info(wires[target_circuit.cone_index[c_i]].name + " is selected as head for creating loops")

        bfs = []
        for w in cone:
            bfs.append(w.index)

        if args.p > 3:
            tmp = "bfs: "
            for i in bfs:
                tmp += wires[i].name + " "
            logging.debug(tmp)

        created_cycle = []
        for i in bfs:
            # print wires[i].name, wires[i].slack, wires[i].logic_level
            if wires[i].mark == 0 and wires[i].logic_level > cycle_length and \
                    wires[i].slack >= slack_threshold:
                curr = wires[i]
                # print curr.name, "is selected for dfs"
                created_cycle.append(curr.index)
                curr.mark = 1
                ct.sta(target_circuit, wires)

                # dfs here
                for dfs_i in range(cycle_length-1):
                    for j in range(len(curr.operands)):
                        if curr.operands[j].logic_level > cycle_length-len(created_cycle):
                            if curr.operands[j].mark == 0 and curr.operands[j].slack >= slack_threshold:
                                curr = curr.operands[j]
                                created_cycle.append(curr.index)
                                curr.mark = 2

                                # for w in wires:
                                #     if w.slack < slack_threshold - 0.06:
                                #         print "Error: slack is less than specified!"
                                #         print_cone_timing(target_circuit, wires, w)
                                #         print curr.name, curr.slack
                                #         print w.name, w.slack
                                #         exit()
                                break

                if len(created_cycle) > 4:
                    # end of the cycle should be selected for switch insertion
                    wires[created_cycle[-1]].mark = 1
                    ct.sta(target_circuit, wires)
                    cycles_list.append(created_cycle)

                    if args.p > 0:
                        tmp = "cycle " + str(len(cycles_list)) + ": "
                        for j in range(len(created_cycle)):
                            tmp += wires[created_cycle[j]].name + " "
                        logging.info(tmp)
                else:
                    # whole cycle should be ignored
                    for j in range(1, len(created_cycle)):
                        wires[created_cycle[j]].mark = 0
                    wires[created_cycle[0]].mark = 3

                    if args.p > 1:
                        tmp = "ignored cycle: "
                        for j in range(len(created_cycle)):
                            tmp += wires[created_cycle[j]].name + " "
                        logging.debug(tmp)

                ct.sta(target_circuit, wires)
                created_cycle = []

                # for w in wires:
                #     if w.slack < slack_threshold - 0.06:
                #         print "Error: slack is less than specified!"
                #         print w.name, w.slack
                #         exit()

                if len(cycles_list) > m_cycles-1:
                    break
            else:
                # wires[i].mark = 1
                continue
        c_i += 1
    return cycles_list


def timing_aware(args, target_circuit, wires):
    # timing aware obfuscation by considering slack times
    m_cycles = args.n
    timing_aware_setup(target_circuit, wires)
    slack_threshold = 0.06 - target_circuit.clk_period * (float(args.d) / 100)
    logging.info("allowed slack is > " + str(slack_threshold))

    if args.p > 1:
        print_cone_timing(target_circuit, wires, wires[target_circuit.cone_index[0]])

    if args.p > 1:
        cir_draw.dot_draw(args, wires)

    logging.info("creating cycles")
    cycles_list = []
    if args.m == "ta1":
        cycles_list = ta1_exp(args, target_circuit, wires)
    elif args.m == "ta2":
        cycles_list = ta2(args, target_circuit, wires)

    if len(cycles_list) < m_cycles:
        logging.critical("there is not enough micro cycles in this circuit!")
        logging.info("available: " + str(len(cycles_list)))
        exit()

    tag_cnt = 1
    # tagging begin and end of cycles
    for i in range(0, m_cycles):
        t = cycles_list[i][0]
        s = cycles_list[i][-1]
        wires[t].tag = tag_cnt
        wires[s].tag = tag_cnt+1
        tag_cnt += 2

    # print_cyclification_info(args, tag_cnt, cycles_list, args.m + "_1")

    # for connecting cycles to other cycles
    for i in range(0, m_cycles-1):
        t = cycles_list[i][1]
        s = cycles_list[i+1][-2]
        wires[t].tag = tag_cnt
        wires[s].tag = tag_cnt+1
        tag_cnt += 2

    # print_cyclification_info(args, tag_cnt, cycles_list, args.m + "_2")

    # consider largest cone for selecting high skew wires
    # cone = circ_func.get_bfs(wires[target_circuit.cone_index[0]], 4000)
    cone = get_bfs(wires, wires[target_circuit.cone_index[0]])
    # sort cone for high skew wires
    cone.sort(key=operator.attrgetter('absprob'), reverse=True)

    logging.info("add high skew cycles")
    wire_avail = True
    while wire_avail:
        # get an element from that cycle
        cycle_wire = None

        for cycle in cycles_list:
            for j in range(1, len(cycle)):
                ind = cycle[j]
                if check4switch(args, wires, wires[ind]) and wires[ind].slack >= slack_threshold:
                    cycle_wire = wires[ind]
                else:
                    continue

        # select next hs wire
        hs_wire = None
        for j in range(len(cone)):
            if check4switch(args, wires, wires[cone[j].index]) and \
                    cycle_wire != wires[cone[j].index] and wires[cone[j].index].slack >= slack_threshold:
                hs_wire = wires[cone[j].index]  # next high skew wire
                break

        if hs_wire is None or cycle_wire is None:
            wire_avail = False
            tag_cnt -= 1
        else:
            wires[cycle_wire.index].tag = tag_cnt
            wires[cycle_wire.index].mark = 1
            hs_wire.tag = tag_cnt+1
            hs_wire.mark = 1
            ct.sta(target_circuit, wires)
            tag_cnt += 2

            logging.debug("high skew: " + hs_wire.name + ", node in last loop: " + cycle_wire.name)

    if args.p > 1:
        print_cone_timing(target_circuit, wires, wires[target_circuit.cone_index[0]])

    logging.info("tag count: " + str(tag_cnt))
    if args.p > 0:
        logging.debug("list of selected wires for inserting switches:")
        for i in range(1, tag_cnt+1, 2):
            for j in range(0, len(wires)):
                if wires[j].tag == i:
                    for k in range(0, len(wires)):
                        if wires[k].tag == i+1:
                            logging.debug(wires[k].name, wires[k].slack, wires[j].name, wires[j].slack)
                            break

    print_cyclification_info(args, tag_cnt, cycles_list, args.m + "_3")


def lfn(args, target_circuit, wires):
    # timing aware obfuscation by considering slack times
    m_cycles = args.n
    timing_aware_setup(target_circuit, wires)
    slack_threshold = 0.06 - target_circuit.clk_period * (float(args.d) / 100)
    logging.info("allowed slack is > " + str(slack_threshold))

    logging.info("creating cycles")
    max_cycles = 60
    args.n = max_cycles
    cycles_list = ta1_exp(args, target_circuit, wires)

    if len(cycles_list) < m_cycles:
        logging.critical("there is not enough micro cycles in this circuit!")
        logging.info("available: " + str(len(cycles_list)))
        exit()

    if args.p > 0:
        logging.debug("cycle indexes:")
        for i in range(0, m_cycles):
            logging.debug(cycles_list[i])

    lfn_lst = []

    # break paths for lfn
    logging.info("lfn indexes: sp1a, ep1a, sp1b, ep1b")
    for i in range(0, len(cycles_list)):
        if len(cycles_list[i]) % 2 != 0:
            logging.critical("cycle length is not even!")
            exit()

        sp1a = cycles_list[i][-1]
        ep1a = cycles_list[i][(len(cycles_list[i])/2)]
        sp1b = cycles_list[i][(len(cycles_list[i])/2)-1]
        ep1b = cycles_list[i][0]

        # disconnect ep1a from sp1b
        sink = sp1b
        source = ep1a

        if (len(wires[sp1a].operands) == 1) or (len(wires[sp1b].operands) == 1):
            logging.info("path is ignored, SPs have only one input: " +
                str(wires[sp1a].name) + " " + str(wires[ep1a].name) + ' x ' + str(wires[sp1b].name) + " " + str(
                    wires[ep1b].name))
            continue

        for j in range(0, len(wires[sink].operands)):
            if wires[sink].operands[j].index == source:
                wires[sink].operands.pop(j)
                break

        for j in range(0, len(wires[source].fanouts)):
            if wires[source].fanouts[j].index == sink:
                wires[source].fanouts.pop(j)
                break

        logging.info(str(wires[sp1a].name) + " " + str(wires[ep1a].name) + ' x ' + str(wires[sp1b].name) + " " + str(wires[ep1b].name))

        lfn_lst.append(sp1a)
        lfn_lst.append(ep1a)
        lfn_lst.append(sp1b)
        lfn_lst.append(ep1b)

        if len(lfn_lst) == m_cycles*4:
            break

    # add LFN circuit to the wires
    key_wires = []
    key_string = ""

    def myLog(x, b):
        if x < b:
            return 0
        return 1 + myLog(x / b, b)

    lfn_size = 2*m_cycles
    n_rows = lfn_size
    n_columns = myLog(lfn_size, 2)

    if len(lfn_lst)/2 != lfn_size:
        logging.critical("there is not enough eligible paths in this circuit!")
        logging.warning("required nodes: " + str(lfn_size))
        logging.warning("available nodes: " + str(len(lfn_lst)/2))
        exit()

    # create required mux and keyinput wires
    mux_matrix = [[None for x in range(n_columns)] for y in range(n_rows)]
    for row in range(n_rows):
        for col in range(n_columns):
            key = circuit.Wire("keyinput" + str(row) + "_" + str(col), "inp", [], 0)
            tmp = circuit.Wire("lfn" + str(row) + "_" + str(col), "mux", [key], 0)
            key_wires.append(key)
            mux_matrix[row][col] = tmp

    # add muxes together connections
    # first column
    for row in range(n_rows):
        mux_matrix[row][0].operands.append(wires[lfn_lst[2*row+1]])
        op_ind = ((n_rows/2) + row) % n_rows
        mux_matrix[row][0].operands.append(wires[lfn_lst[2*op_ind+1]])
        key_string += "0"

    # middle columns
    for row in range(n_rows):
        for col in range(1, n_columns-1):
            mux_matrix[row][col].operands.append(mux_matrix[row][col-1])
            op_ind = ((row/2) + 1) % n_rows
            mux_matrix[row][col].operands.append(mux_matrix[op_ind][col-1])
            key_string += "0"

    # last column
    for row in range(n_rows):
        mux_matrix[row][n_columns-1].operands.append(mux_matrix[row][n_columns-2])
        mux_matrix[row][n_columns-1].operands.append(mux_matrix[(row+1)%n_rows][n_columns-2])
        wires[lfn_lst[2*row]].operands.append(mux_matrix[row][n_columns-1])
        key_string += "0"

    # convert 2d mux_matrix to 1d mux_wires
    mux_wires = []
    for row in range(n_rows):
        for col in range(n_columns):
            mux_wires.append(mux_matrix[row][col])

    my_util.wires2bench(args, target_circuit, wires, key_wires + mux_wires, key_string)
    exit()

    # cycle count on logical graph
    import graph_tool.all as gt
    g = gt.Graph()
    lst = []

    for i in range(0, len(wires)):
        lst.append(g.add_vertex())

    for i in range(0, len(wires)):
        if wires[i].type != "inp":
            for j in range(len(wires[i].operands)):
                g.add_edge(lst[wires[i].operands[j].index], lst[wires[i].index])

    n = len(lfn_lst)
    # connect inputs of each spia to each spib
    for i in range(0, n, 4):
        spia = lfn_lst[i]
        spib = lfn_lst[i+2]
        # print spia, spib
        for j in range(len(wires[spia].operands)):
            g.add_edge(lst[wires[spia].operands[j].index], lst[wires[spib].index])

    # connect output of each epia to outputs of each epib
    for i in range(0, n, 4):
        epia = lfn_lst[i+1]
        epib = lfn_lst[i+3]
        for j in range(len(wires[epib].fanouts)):
            g.add_edge(lst[wires[epia].index], lst[wires[epib].fanouts[j].index])

    # connect each EP to all SPs
    for i in range(1, n, 2):
        for j in range(0, n, 2):
            # print lfn_lst[i], lfn_lst[j]
            g.add_edge(lst[lfn_lst[i]], lst[lfn_lst[j]])

    g_out = gt.all_circuits(g)

    try:
        cnt = 0
        for c in g_out:
            cnt += 1
    except KeyboardInterrupt:
        logging.critical("INTERRUPTED")

    logging.info("there are " + str(cnt) + " cycles")


def wire_from_cycles(cycles_list):
    for cycle in cycles_list:
        for j in range(1, len(cycle)):
            ind = cycle[j]

            if check4switch(args, wires, wires[ind]):
                wires[ind].tag = 1
                return wires[ind], wires[cycle[j-1]]
    return None, None


def glsvlsi17(args, target_circuit, wires):
    # This is based on the original cyclic obfuscation paper by Kaveh Shamsi

    t_gates = len(wires) - target_circuit.n_inputs
    a_limit = float(args.a)/100

    m_cycles = args.n
    timing_aware_setup(target_circuit, wires)

    logging.info("creating cycles")
    cycles_list = ta1_exp(args, target_circuit, wires)

    # cir_draw.dot_draw_tag(args, wires, cycles_list)

    if len(cycles_list) < m_cycles:
        logging.critical("there is not enough micro cycles in this circuit!")
        logging.info("available: " + str(len(cycles_list)))
        exit()

    if args.p > 0:
        logging.debug("cycle indexes:")
        for i in range(0, m_cycles):
            logging.debug(cycles_list[i])

    mux_list = []
    # tagging begin and end of cycles
    for i in range(0, m_cycles):
        last = cycles_list[i][0]
        first = cycles_list[i][-1]
        second = cycles_list[i][-2]
        wires[last].tag = 1
        wires[first].tag = 1
        mux_list.append([wires[first], wires[last], wires[second]])

    logging.info("generate available fanin and fanout wires")
    available_fanin = []
    available_fanout = []
    for w in wires:
        if (w.tag == 0) and (w.type != "inp") and (w.fanout > 0):
            available_fanin.append(w)
            available_fanout.append(w)

    for m in mux_list:
        cone = circuit.get_unique_fanin_cone(m[1])
        for w in cone:
            if w in available_fanout:
                available_fanout.remove(w)
            if w in available_fanin:
                available_fanin.remove(w)

    for w in wires:
        cone = circuit.get_unique_fanin_cone(w)
        for m in mux_list:
            if m[0] in cone:
                if w in available_fanin:
                    available_fanin.remove(w)

    # calculate the median of available wires
    # lvl_list = []
    # for w in available_fanout:
    #     lvl_list.append(w.logic_level)
    # lvl_list.sort()
    # median_lvl = lvl_list[len(lvl_list)/2]
    # logging.info("median level is: " + str(median_lvl))

    logging.info("add mux to the wires in middle")
    wire_avail = True
    while wire_avail:
        # get an element from that cycle
        cycle_wire, cycle_wire_out = wire_from_cycles(cycles_list)

        # select random wires
        rnd_wire = []
        rnd_wire_cnt = 0
        if cycle_wire:
            fo = circ_func.fan_outs(wires, cycle_wire)
            if len(fo) == 1:
                # select two free wire
                rnd_wire_cnt = 2
            elif len(fo) > 1:
                # select one free wire
                rnd_wire_cnt = 1
            else:
                logging.critical("Output selected!")
                exit()

            j = 0

            if False:
                while j < rnd_wire_cnt:
                    rnd_w = available_fanin[randint(0, len(available_fanin) - 1)]

                    # get fanin wire (j==0) from the first half of the circuit
                    # and fanout wire (j==1) from the second half of the circuit
                    # this is for avoiding creation of additional cycles!
                    if j == 0 and (rnd_w.logic_level > median_lvl - 1):
                        continue
                    elif j == 1 and (rnd_w.logic_level < median_lvl + 1):
                        continue

                    if check4switch(args, wires, rnd_w):
                        rnd_wire.append(rnd_w)
                        available_fanin.remove(rnd_w)
                        j += 1

            else:
                while j < rnd_wire_cnt and len(available_fanin) > 0 and len(available_fanout) > 0:
                    if j == 0:
                        rw = available_fanin[randint(0, len(available_fanin)-1)]

                        cone = circ_func.get_unique_fanin_cone(rw)
                        if cycle_wire in cone:
                            continue
                    else:
                        rw = available_fanout[randint(0, len(available_fanout)-1)]

                        cone = circ_func.get_unique_fanin_cone(cycle_wire_out)
                        if rw in cone:
                            continue

                    # if rw.logic_level > cycle_wire.logic_level:
                    #     continue

                    if check4switch(args, wires, rw):
                        cone = circ_func.get_unique_fanin_cone(rw)
                        for w in cone:
                            if w in available_fanout:
                                available_fanout.remove(w)

                        rnd_wire.append(rw)
                        if rw in available_fanin:
                            available_fanin.remove(rw)
                        j += 1

        if len(rnd_wire) != rnd_wire_cnt or cycle_wire is None:
            wire_avail = False
        elif a_limit > 0 and len(mux_list) > a_limit*t_gates:
            # comment this elif if you don't want area constrain
            wire_avail = False
            logging.info("Area constrained to 10% of total gates! ")
        else:
            wires[cycle_wire.index].tag = 1
            rnd_wire[0].tag = 2
            mux_list.append([wires[cycle_wire.index], rnd_wire[0], cycle_wire_out])

            if rnd_wire_cnt == 2:
                rnd_wire[1].tag = 2
                fo = circ_func.fan_outs(wires, rnd_wire[1])
                if len(fo) == 0:
                    logging.critical("Error: has no output: " + rnd_wire[1].name)
                    exit()
                mux_list.append([rnd_wire[1], wires[cycle_wire.index], fo[0]])

    logging.info("mux count: " + str(len(mux_list)))
    if args.p > 0:
        logging.debug("list of selected wires for inserting muxes:")
        for mux_inputs in mux_list:
            logging.debug("in1:" + mux_inputs[0].name + " in2:" + mux_inputs[1].name + " to:" + mux_inputs[2].name)

    my_util.write_mux_output(wires, mux_list, args.b, args.m)

    # for cycle count and test
    bench_folder = target_circuit.path[0: target_circuit.path.find("original/")]
    bench_file_name = target_circuit.name
    new_bench_address = bench_folder + args.m + "/" + bench_file_name + "_" + str(len(mux_list)) + ".bench"
    cir, wires_tmp = circ_func.simple_read_bench(new_bench_address)

    for mx in mux_list:
        for w in wires_tmp:
            if w.name == mx[0].name or w.name == mx[1].name:
                w.mark = 1

    # cir_draw.dot_draw_tag(args, wires_tmp, [])

    cycsat_util.cycle_count_timeout(args, wires_tmp, 10800)


def check_date18(wire):
    if wire.mark == 0 and wire.type != "inp" and wire.type != "mux" and "keyinput" not in wire.name:
        return True
    else:
        return False


def b2b_cyc(args, target_circuit, wires):
    # this function returns a list of b2b gates
    i = 0
    cycles_list = []

    while i < len(wires):
        # mark = 1 --> selected
        curr = wires[i]
        if check_date18(curr):
            created_cycle = [curr.index]

            # check inputs
            is_ok = True
            for j in range(len(curr.operands)):
                if not check_date18(curr.operands[j]):
                    is_ok = False
                    break

            if is_ok:
                for j in range(len(curr.operands)):
                    curr2 = curr.operands[j]
                    for k in range(len(curr2.operands)):
                        if check_date18(curr2.operands[k]):
                            created_cycle.append(curr2.index)
                            break

                    if len(created_cycle) > 1:
                        wires[created_cycle[0]].mark = 1
                        wires[created_cycle[1]].mark = 1
                        cycles_list.append(created_cycle)

                        tmp = "cycle " + str(len(cycles_list)) + ": "
                        tmp += wires[created_cycle[0]].name + " " + wires[created_cycle[1]].name
                        logging.info(tmp)
                        break

        i += 1
    return cycles_list


def date18(args, target_circuit, wires):
    # This is based on DATE18 paper by Hai Zhou

    m_cycles = args.n

    logging.info("selecting back-to-back gates")
    # cycles_list = ta1_exp(args, target_circuit, wires)
    cycles_list = b2b_cyc(args, target_circuit, wires)
    print(len(cycles_list))
    if len(cycles_list) < m_cycles:
        logging.critical("there is not enough micro cycles in this circuit!")
        logging.info("available: " + str(len(cycles_list)))

    # selecting back-to-back gates for inserting real cycles
    back2back_list = []
    # tagging begin and end of cycles
    for i in range(len(cycles_list)):
        t = cycles_list[i][0]
        s = cycles_list[i][1]
        if len(wires[s].operands) > 1:
            wires[t].tag = 1
            wires[s].tag = 1
            back2back_list.append([wires[s], wires[t]])
            if len(back2back_list) == m_cycles:
                break
        # logging.warning("gate has one input, back-to-back gate skipped!")

    if args.p > 0:
        logging.debug("selected paths:")
        for i in range(len(back2back_list)):
            logging.debug(back2back_list[i][0].name + ", " + back2back_list[i][1].name)

    logging.info("add auxiliary circuits")
    aux_wires = []
    wire_index = 0

    key_index = 0
    for i in range(len(wires)):
        if wires[i].type == "inp" and ("keyinput" in wires[i].name):
            key_index += 1

    key_string = ""
    for i in range(len(back2back_list)):
        gate0 = back2back_list[i][0]
        gate1 = back2back_list[i][1]

        # add keys
        key0 = circuit.Wire("keyinput" + str(key_index), "inp", [], wire_index)
        key_index += 1
        wire_index += 1
        key1 = circuit.Wire("keyinput" + str(key_index), "inp", [], wire_index)
        key_index += 1
        wire_index += 1

        # add muxes
        mux0 = circuit.Wire("mux_" + str(wire_index), "mux", [key0], wire_index)
        wire_index += 1
        mux1 = circuit.Wire("mux_" + str(wire_index), "mux", [key1], wire_index)
        wire_index += 1

        # add xors
        xor0 = circuit.Wire("xor0_" + str(wire_index), "xor", [mux0, gate0], wire_index)
        wire_index += 1
        xor1 = circuit.Wire("xor1_" + str(wire_index), "xor", [mux1, xor0], wire_index)
        wire_index += 1

        if randint(0, 1) == 0:
            key_string += '0'
            mux0.operands.extend((xor1, gate0.operands[1]))
        else:
            key_string += '1'
            mux0.operands.extend((gate0.operands[1], xor1))

        if randint(0, 1) == 0:
            key_string += '0'
            mux1.operands.extend((xor1, gate0.operands[0]))
        else:
            key_string += '1'
            mux1.operands.extend((gate0.operands[0], xor1))

        # correct fanout list
        xor0.fanouts = [xor1]
        xor1.fanouts = [mux0, mux1, gate1]
        mux0.fanouts = [xor0]
        mux1.fanouts = [xor1]

        # correct number
        xor0.fanout = 1
        xor1.fanout = 3
        mux0.fanout = 1
        mux1.fanout = 1

        # update aux_wires
        aux_wires.append(key0)
        aux_wires.append(key1)
        aux_wires.append(mux0)
        aux_wires.append(mux1)
        aux_wires.append(xor0)
        aux_wires.append(xor1)

        # disconnect gate0 from gate1
        gate1.operands.remove(gate0)
        gate1.operands.append(xor1)

    # cir_draw.dot_draw_tag(args, wires, [])
    new_bench_address = my_util.wires2bench(args, target_circuit, wires, aux_wires, key_string)

    cir, wires_tmp = circuit.simple_read_bench(new_bench_address)
    cycsat_util.cycle_count_timeout(args, wires_tmp, 10800)


def rand_cycle_highskew(args, circuit, wires):
    print("rand_cycle_highskew")
    circuit.b2b = True
    cycle_length = args.l
    m_cycles = args.n

    cone_index = circuit.largest_cone(wires)

    cycles_list = []
    c_i = 0
    print("creating cycles")
    while len(cycles_list) < m_cycles and c_i < len(cone_index):
        cone = circuit.get_bfs(wires[cone_index[c_i]], 4000)
        print(wires[cone_index[c_i]].name + " is selected as head for creating loops")
        if args.p:
            my_util.print_cone(cone)

        bfs = []
        for w in cone:
            bfs.append(w.index)

        tmp = "bfs: "
        for i in bfs:
            tmp += wires[i].name + " "
        # print(tmp)

        created_cycle = []
        for i in bfs:
            # print "bfs: ", wires[i].name, wires[i].logic_level
            if wires[i].mark == 0 and wires[i].logic_level > cycle_length:
                # dfs here
                curr = wires[i]
                created_cycle.append(curr.index)
                curr.mark = 1
                # print "head", curr.name, curr.logic_level
                for dfs_i in range(cycle_length-1):
                    for j in range(len(curr.operands)):
                        if curr.operands[j].logic_level > cycle_length-len(created_cycle):
                            if curr.operands[j].mark == 0:
                                curr = curr.operands[j]
                                created_cycle.append(curr.index)
                                curr.mark = 1
                                break
                if len(created_cycle) > 4:
                    cycles_list.append(created_cycle)
                    tmp = "cycle " + str(len(cycles_list)) + ": "
                    for j in range(len(created_cycle)):
                        tmp += wires[created_cycle[j]].name + " "
                    print(tmp)
                created_cycle = []
                if len(cycles_list) > m_cycles-1:
                    break
            else:
                # wires[i].mark = 1
                continue
        c_i += 1

    tag_cnt = 1

    # tagging begin and end of cycles
    for i in range(0, m_cycles):
        t = cycles_list[i][0]
        s = cycles_list[i][-1]
        wires[t].tag = tag_cnt
        wires[s].tag = tag_cnt+1
        tag_cnt += 2

    # bench_address = args.b
    # bench_file_name = bench_address[bench_address.find("original/") + 9: bench_address.find(".bench")]
    # bench_folder = bench_address[0: bench_address.find("original/")]

    # my_util.write_output(wires, tag_cnt-1, args.b, "hs_rc1")
    # num_of_path = tag_cnt-1
    # new_bench_address = bench_folder + "hs_rc1" + "/" + bench_file_name + "_" + str(num_of_path) + ".bench"
    # wires_tmp = circ_func.simple_read_bench(new_bench_address)
    # cycsat.cycle_count(args, wires_tmp)

    # for connecting cycles to other cycles
    for i in range(0, m_cycles-1):
        t = cycles_list[i][1]
        s = cycles_list[i+1][-2]
        wires[t].tag = tag_cnt
        wires[s].tag = tag_cnt+1
        tag_cnt += 2

    # num_of_path = tag_cnt-1
    # my_util.write_output(wires, tag_cnt-1, args.b, "hs_rc2")
    # new_bench_address = bench_folder + "hs_rc2" + "/" + bench_file_name + "_" + str(num_of_path) + ".bench"
    # wires_tmp = circ_func.simple_read_bench(new_bench_address)
    # cycsat.cycle_count(args, wires_tmp)

    # consider largest cone for selecting high skew wires
    cone = circuit.get_bfs(wires[cone_index[0]], 4000)
    # sort cone for high skew wires
    cone.sort(key=operator.attrgetter('absprob'), reverse=True)

    # add cycles
    wire_avail = True
    while wire_avail:
        # get an element from that cycle
        cycle_wire = None

        for cycle in cycles_list:
            for j in range(1, len(cycle)):
                ind = cycle[j]
                if check4switch(args, wires, wires[ind]):
                    cycle_wire = wires[ind]
                else:
                    continue

        # select next hs wire
        hs_wire = None
        for j in range(len(cone)):
            if check4switch(args, wires, wires[cone[j].index]) and cycle_wire != wires[cone[j].index]:
                hs_wire = wires[cone[j].index]  # next high skew wire
                break

        if hs_wire is None or cycle_wire is None:
            wire_avail = False
            tag_cnt -= 1
        else:
            wires[cycle_wire.index].tag = tag_cnt
            hs_wire.tag = tag_cnt+1
            tag_cnt += 2

            if args.p:
                print("high skew: " + hs_wire.name + ", node in last loop: " + cycle_wire.name)

    print("tag count:", tag_cnt)
    if args.p:
        print("list of selected wires for inserting switches:")
        for i in range(1, tag_cnt+1, 2):
            for j in range(0, len(wires)):
                if wires[j].tag == i:
                    for k in range(0, len(wires)):
                        if wires[k].tag == i+1:
                            print(wires[k].name, wires[j].name)
                            break

    my_util.write_output(wires, tag_cnt, args.b, args.m)

    # num_of_path = tag_cnt
    # new_bench_address = bench_folder + "hs_rc" + "/" + bench_file_name + "_" + str(num_of_path) + ".bench"
    # wires_tmp = circ_func.simple_read_bench(new_bench_address)
    # cycsat.cycle_count(args, wires_tmp)


def insert_switch(wires, input1, input2, select):
    # TODO: Not working, it needs to duplicate connected inputs
    tmp_input1 = copy.deepcopy(input1)
    tmp_input2 = copy.deepcopy(input2)
    tmp_input1.name = tmp_input1.name + "_enc"
    tmp_input2.name = tmp_input2.name + "_enc"

    key = circuit.Wire("keyinput" + str(select), "inp", [], "1", 0, 0, 0, 0, 1, 0, 0, len(wires))
    wires.append(key)
    inv_key = circuit.Wire("inv_keyinput" + str(select), "not", [key], "1", 0, 0, 0, 0, 1, 0, 0, len(wires))

    wires.append(circuit.Wire(input1.name, "mux", [key, tmp_input1, tmp_input2], "1", 0, 0, 0, 0, 1, 0, 0, len(wires)))
    wires.append(inv_key)
    wires.append(
        circuit.Wire(input2.name, "mux", [inv_key, tmp_input1, tmp_input2], "1", 0, 0, 0, 0, 1, 0, 0, len(wires)))


def check4switch(target_circuit, wires, sel_wire):
    if sel_wire.tag == 0 and sel_wire.type != "inp":
        return True
        if target_circuit.b2b:
            return my_util.check_b2b(wires, sel_wire.index)
        else:
            return True
    else:
        return False


def benchmarking1(wires):
    print("running benchmarking1")
    for i in range(0, len(wires)):
        fanout1 = circuit.get_unique_fanin_cone(wires[i])
        fanout2 = circuit.wire_fanin_cone(wires[i], 250)

        if len(fanout1) != len(fanout2):
            print("FAIL")
            exit()

        for i in range(0, len(fanout2)):
            found = False
            for j in range(0, len(fanout1)):
                if fanout1[j].name == fanout2[i].name:
                    found = True
                    break
            if not found:
                print("FAIL")
                exit()
    print("SUCCESS")
    exit()


def benchmarking2(wires):
    print("running benchmarking2")

    t_a = datetime.now()
    for i in range(0, len(wires)):
        fanout1 = circuit.get_unique_fanin_cone(wires[i])
        print(i, len(fanout1))
    t_b = datetime.now()
    print("rec: " + my_util.diff(t_a, t_b))

    t_a = datetime.now()
    for i in range(0, len(wires)):
        fan_in = set()
        circuit.get_fanin_cone2(wires[i], fan_in)
        print(i, len(fan_in))
    t_b = datetime.now()
    print("set: " + my_util.diff(t_a, t_b))

    t_a = datetime.now()
    for i in range(0, len(wires)):
        fanout2 = circuit.wire_fanin_cone(wires[i], 4000000)
        print(i, len(fanout2))
    t_b = datetime.now()
    print("for-loop: " + my_util.diff(t_a, t_b))

    exit()


def cone_marking(args, wires):
    args.b2b = True

    #benchmarking2(wires)

    cone_i = circuit.largest_cone(wires)
    wire_list = circuit.get_unique_fanin_cone(wires[cone_i])
    if args.p:
        my_util.print_cone(wire_list)
    high_skew_marking(args, wire_list)


def high_skew_marking(args, wires):
    print("executing high_skew_marking")
    wires.sort(key=operator.attrgetter('absprob'), reverse=True)

    selected = 1
    for i in range(0, len(wires)):
        if check4switch(args, wires, wires[i]):
            wires[i].tag = selected
            if args.p:
                print(wires[i].name + ", skew: " + str(wires[i].absprob) + " is selected for obfuscation")
            if selected % 2 == 0:
                my_util.write_output(wires, selected, args.b, args.m)
            if selected == args.n:
                break
            selected += 1

    if selected < args.n:
        print("There is not enough paths for obfuscation!")


def rnd_marking(args, wires):
    #TODO: print an error if there is not enough paths for obfuscation
    selected = 0
    while selected != args.n:
        rand_value = randint(0, len(wires) - 1)
        if check4switch(args, wires, wires[rand_value]):
            selected += 1
            wires[rand_value].tag = selected
            if selected % 2 == 0:
                my_util.write_output(wires, selected, args.b, "rnd")
