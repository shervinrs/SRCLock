import logging


def get_clk_period(wires):
    # calculate largest delay which is equal to clock period
    clk_period = 0
    w_longest = wires[0]
    for w in wires:
        if w.type != "inp":
            if w.delay != 0:
                if w.delay > clk_period:
                    clk_period = w.delay
                    w_longest = w
            else:
                logging.critical("gate delay is not calculated for clk period calculation!")
                exit()
    logging.info("longest delay is for " + w_longest.name + " = " + str(clk_period))
    return clk_period


def gate_delay(wire):
    # delays stored in dictionaries for X1_RVT cells
    # AND2X1_RVT
    and_delay = {2: 0.04, 3: 0.06, 4: 0.07, 5: 0.11, 6: 0.13, 7: 0.14, 8: 0.18, 9: 0.20}
    # NAND2X1_RVT
    nand_delay = {2: 0.06, 3: 0.06, 4: 0.07, 5: 0.11, 6: 0.13, 7: 0.14, 8: 0.18, 9: 0.20}
    # OR2X1_RVT
    or_delay = {2: 0.05, 3: 0.06, 4: 0.07, 5: 0.11, 6: 0.13, 7: 0.14, 8: 0.18, 9: 0.20}
    # NOR2X1_RVT
    nor_delay = {2: 0.06, 3: 0.06, 4: 0.07, 5: 0.11, 6: 0.13, 7: 0.14, 8: 0.18, 9: 0.20}
    # XNOR2X1_RVT
    xnor_delay = {2: 0.1, 3: 0.11, 4: 0.12}
    # XOR2X1_RVT
    xor_delay = {2: 0.1, 3: 0.11, 4: 0.12}
    # MUX21X1_RVT
    mux_delay = {3: 0.06}
    # INVX1_RVT
    not_delay = {1: 0.03}
    # IBUFFX2_RVT, it doesn't have X1
    buff_delay = {1: 0.05}

    delay = 0
    if wire.type == "and":
        delay = and_delay[len(wire.operands)]
    elif wire.type == "nand":
        delay = nand_delay[len(wire.operands)]
    elif wire.type == "or":
        delay = or_delay[len(wire.operands)]
    elif wire.type == "nor":
        delay = nor_delay[len(wire.operands)]
    elif wire.type == "xnor":
        delay = xnor_delay[len(wire.operands)]
    elif wire.type == "xor":
        delay = xor_delay[len(wire.operands)]
    elif wire.type == "mux":
        delay = mux_delay[len(wire.operands)]
    elif wire.type == "not":
        delay = not_delay[len(wire.operands)]
    elif wire.type == "buff":
        delay = buff_delay[len(wire.operands)]
    else:
        logging.critical("Unspecified gate type: " + wire.type)
        exit()

    if wire.mark == 1:
        delay += mux_delay[3]

    return delay


def update_wire_delays(cir, wires):
    if cir.max_level == 0:
        logging.critical("Error: max level shouldn't be zero")
        exit()

    # calculate worst delays for each cell in a path
    for curr_lvl in range(1, cir.max_level + 1):
        # print curr_lvl
        for w in wires:
            if w.logic_level == curr_lvl:
                # max path delay before this gate
                max_path = 0
                for i in range(len(w.operands)):
                    if w.operands[i].delay > max_path:
                        max_path = w.operands[i].delay
                w.delay = max_path + gate_delay(w)


def sta(cir, wires):
    update_wire_delays(cir, wires)

    if cir.clk_period == 0:
        cir.clk_period = get_clk_period(wires)

    # redundant
    if cir.clk_period == 0:
        logging.critical("clock period shouldn't be zero")
        exit()

    # calculate slacks for the last levels
    # print "last level:", max_level
    for i in cir.cone_index:
        wires[i].slack = cir.clk_period - wires[i].delay

    # calculate slacks for gates in other levels
    for curr_lvl in range(cir.max_level-1, 0, -1):
        # print curr_lvl
        for w in wires:
            if w.logic_level == curr_lvl:
                # fan_outs = circ_func.fan_outs(wires, w)
                fan_outs = w.fanouts

                # check if the selected wire is not output
                if fan_outs:
                    # find the fan out with min slack
                    w_lowest = fan_outs[0]
                    for f in fan_outs:
                        if f.slack < w_lowest.slack:
                            w_lowest = f

                    w.slack = w_lowest.slack + (w_lowest.delay - w.delay) - gate_delay(w_lowest)
                    if w.slack < 0.001:
                        w.slack = 0.0

    # for i in range(0, len(wires)):
    #     my_util.wire_print(wires[i]
