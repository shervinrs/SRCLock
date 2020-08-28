import copy
from operator import itemgetter
import logging


class Wire:
    # def __init__(self, name, type, operands, mark, logic_level, prob0, prob1, absprob, fanout, mainout, tag, index):
    def __init__(self, cell_name, cell_type, operands, index):
        self.name = cell_name
        self.type = cell_type
        self.operands = operands
        self.index = index

        self.mark = 0
        self.logic_level = 0
        self.prob0 = 0.5  # initial value should be 0.5 for inputs
        self.prob1 = 0.5  # initial value should be 0.5 for inputs
        self.absprob = 0
        self.fanout = 0
        self.tag = 0
        self.delay = 0
        self.slack = 0
        self.fanouts = []
        self.lit = 0


class Circuit:
    def __init__(self, name, n_inputs, n_outputs):
        self.name = name
        self.n_inputs = n_inputs  # number of original inputs
        self.n_outputs = n_outputs

        self.k_inputs = 0  # number of keyinputs
        self.path = ""
        self.input_wires = []
        self.output_wires = []
        self.info = ""

        self.cone_index = []
        self.clk_period = 0
        self.max_level = 0
        self.b2b = True
        self.mainout = False
        self.wires = []
        self.key = ""



def fan_outs(wires, curr_wire):
    fan_out = []
    for w in wires:
        if curr_wire in w.operands:
            fan_out.append(w)
    return fan_out


def largest_cone(wires):
    # returns a sorted list of wire index of largest cones
    cone_list = []
    for i in range(0, len(wires)):
        if wires[i].fanout == 0:
            curr_cir = len(get_unique_fanin_cone(wires[i]))
            logging.debug(str(i) + "/" + str(len(wires)) + ": fan-in cone of wire (" + wires[i].name + ") is: " + str(curr_cir))
            cone_list.append([i, curr_cir])
    cone_list.sort(key=lambda x: x[1], reverse=True)
    cone_index = map(itemgetter(0), cone_list)
    logging.debug("highest fan-in cone is for " + wires[cone_list[0][0]].name + " with size of " + str(cone_list[0][1]))
    return cone_index


def get_bfs(wire_in, cone_size):
    index_traverse = 0
    if wire_in.type == "inp":
        return []
    else:
        fanin_cone = [wire_in]
        cone_size = cone_size - 1
        temp = copy.deepcopy(fanin_cone[index_traverse].operands)
        while cone_size != 0:
            added_bef = 0
            if len(temp) == 0:
                index_traverse = index_traverse + 1
                if index_traverse >= len(fanin_cone):
                    cone_size = 0
                else:
                    temp = copy.deepcopy(fanin_cone[index_traverse].operands)
            elif temp[0].type == "inp":
                temp.remove(temp[0])
            else:
                for i in range(0, len(fanin_cone)):
                    if fanin_cone[i].name == temp[0].name:
                        added_bef = 1
                if added_bef == 0:
                    fanin_cone.append(temp[0])
                    cone_size = cone_size - 1
                temp.remove(temp[0])
    return fanin_cone


def get_unique_fanin_cone(wire_in):
    # get unique fanin cone
    return uniquify_wire_list(get_fanin_cone(wire_in))


def get_fanin_cone(wire_in):
    # recursive fanin cone function
    # recursion have not done right, but it's faster than get_fanin_cone2!
    if wire_in.type == "inp":
        return []
    else:
        fanin_cone = [wire_in]
        for i in range(len(wire_in.operands)):
            fanin_cone += get_fanin_cone(wire_in.operands[i])
        return fanin_cone


def get_fanin_cone2(wire_in, fanin_cone):
    # correct recursive fanin cone function
    # it's slow?
    if wire_in.type != "inp":
        fanin_cone.add(wire_in)
        for i in range(len(wire_in.operands)):
            get_fanin_cone2(wire_in.operands[i], fanin_cone)


def uniquify_wire_list(wire_list):
    # removes duplicate wires from wire_list
    seen = set()
    unique = []
    for obj in wire_list:
        if obj.name not in seen:
            unique.append(obj)
            seen.add(obj.name)
    return unique


def max_dep(wire):
    # calculates depth of a wire object (logic level)
    if wire.type == "inp":
        return 0
    elif wire.logic_level != 0:
        return wire.logic_level
    else:
        max = 0
        for i in range(len(wire.operands)):
            curr = max_dep(wire.operands[i])
            if curr > max:
                max = curr
    return max+1


def read_bench(args):
    # it is not sensitive to the order of lines
    # it cannot read cyclic circuits, because of max_dep()

    logging.warning("Read bench file.")
    inputs = []
    outputs = []
    wires = []
    # input_array = []
    temp = []
    bench_file = open(args.b)
    index = 0
    info = ""

    for line in bench_file:
        if "#" in line:
            info += line
            # continue
        elif "INPUT" in line:
            w = Wire(line[line.find("(") + 1:line.find(")")], "inp", [], index)
            inputs.append(w)
            # input_array.append(line[line.find("(") + 1:line.find(")")])
            wires.append(w)
            # input_array = []
            index += 1
        elif "OUTPUT" in line:
            w = Wire(line[line.find("(") + 1:line.find(")")], "out", [], 0)
            outputs.append(w)
        elif " = " in line:
            gate_out = line[0: line.find(" =")]
            gate_type = line[line.find("= ") + 2: line.find("(")]
            gate_list_inputs = line[line.find("(") + 1:line.find(")")]
            gate_oprs = gate_list_inputs.split(", ")
            for i in range(0, len(gate_oprs)):
                found = False
                for j in range(0, len(wires)):
                    if wires[j].name == gate_oprs[i]:
                        found = True
                        temp.append(wires[j])
                        break
                if not found:
                    # print gate_out, gate_oprs[i]
                    temp.append(Wire(gate_oprs[i], "dummy", [], 0))

            wires.append(Wire(gate_out, gate_type.lower(), temp, index))
            temp = []
            index += 1

    key_line = ""
    bench_file.seek(0)
    for line in bench_file:
        if "# key=" in line:
            key_line = line[6:len(line) - 1]
            break
    bench_file.close()

    # replacing dummy wires
    for i in range(0, len(wires)):
        for j in range(0, len(wires[i].operands)):
            if wires[i].operands[j].type == "dummy":
                found = False
                for k in range(0, len(wires)):
                    if wires[k].name == wires[i].operands[j].name:
                        found = True
                        wires[i].operands[j] = wires[k]
                        break
                # just check for correctness
                if not found:
                    logging.critical(wires[i].operands[j].name)
                    logging.critical("ERROR1")
                    exit()

    # just check for correctness
    for i in range(0, len(wires)):
        for j in range(i + 1, len(wires)):
            if wires[i].name == wires[j].name:
                logging.critical(wires[i].name, wires[j].name)
                logging.critical("ERROR2")
                exit()

    # calculating number of fanouts
    for i in range(0, len(wires)):
        fanout_temp = 0
        for j in range(0, len(wires)):
            if i != j:
                for k in range(0, len(wires[j].operands)):
                    if wires[i].name == wires[j].operands[k].name:
                        fanout_temp = fanout_temp + 1
        wires[i].fanout = fanout_temp

    # calculating level
    max_lvl = 0
    for i in range(len(wires)):
        wires[i].logic_level = max_dep(wires[i])
        if wires[i].logic_level > max_lvl:
            max_lvl = wires[i].logic_level

    # calculating fanout list
    for w in wires:
        w.fanouts = fan_outs(wires, w)

    # calculating wire probability
    for lvl in range(1, max_lvl+1):
        for w in wires:
            if w.logic_level == lvl:
                temp_prob0 = 0.25
                temp_prob1 = 0.25
                gate_type = w.type
                temp = w.operands

                for i in range(0, len(temp)):
                    if len(temp) == 1:
                        if gate_type == "NOT" or gate_type == "not":
                            temp_prob = temp[0].prob0
                            temp_prob0 = temp[0].prob1
                            temp_prob1 = temp_prob
                        elif gate_type == "BUFF" or gate_type == "buff":
                            temp_prob0 = temp[0].prob0
                            temp_prob1 = temp[0].prob1
                    else:
                        if gate_type == "NAND" or gate_type == "nand":
                            if i == 0:
                                temp_prob0 = temp[i].prob0
                                temp_prob1 = temp[i].prob1
                            else:
                                temp_prob0 = temp_prob0 * temp[i].prob0 + \
                                             temp_prob1 * temp[i].prob0 + \
                                             temp_prob0 * temp[i].prob1
                                temp_prob1 = temp_prob1 * temp[i].prob1
                        elif gate_type == "AND" or gate_type == "and":
                            if i == 0:
                                temp_prob0 = temp[i].prob0
                                temp_prob1 = temp[i].prob1
                            else:
                                temp_prob0 = temp_prob0 * temp[i].prob0 + \
                                             temp_prob1 * temp[i].prob0 + \
                                             temp_prob0 * temp[i].prob1
                                temp_prob1 = temp_prob1 * temp[i].prob1
                        elif gate_type == "NOR" or gate_type == "nor":
                            if i == 0:
                                temp_prob0 = temp[i].prob0
                                temp_prob1 = temp[i].prob1
                            else:
                                temp_prob0 = temp_prob0 * temp[i].prob0
                                temp_prob1 = 1 - temp_prob0
                        elif gate_type == "OR" or gate_type == "or":
                            if i == 0:
                                temp_prob0 = temp[i].prob0
                                temp_prob1 = temp[i].prob1
                            else:
                                temp_prob0 = temp_prob0 * temp[i].prob0
                                temp_prob1 = 1 - temp_prob0
                        elif gate_type == "XNOR" or gate_type == "xnor":
                            if i == 0:
                                temp_prob0 = temp[i].prob0
                                temp_prob1 = temp[i].prob1
                            else:
                                temp_prob0 = temp_prob0 * temp[i].prob0 + temp_prob1 * temp[i].prob1
                                temp_prob1 = 1 - temp_prob0
                        elif gate_type == "XOR" or gate_type == "xor":
                            if i == 0:
                                temp_prob0 = temp[i].prob0
                                temp_prob1 = temp[i].prob1
                            else:
                                temp_prob0 = temp_prob0 * temp[i].prob1 + temp_prob1 * temp[i].prob0
                                temp_prob1 = 1 - temp_prob0

                if gate_type == "NAND" or gate_type == "nand":
                    temp_prob = temp_prob0
                    temp_prob0 = temp_prob1
                    temp_prob1 = temp_prob

                if gate_type == "NOR" or gate_type == "nor":
                    temp_prob = temp_prob0
                    temp_prob0 = temp_prob1
                    temp_prob1 = temp_prob

                w.prob0 = temp_prob0
                w.prob1 = temp_prob1
                w.absprob = abs(temp_prob0 - temp_prob1)

    # if circuit.mainout:
    #     for i in range(0, len(outputs)):
    #         for j in range(0, len(wires)):
    #             if wires[j].name == outputs[i]:
    #                 # wire_list = wire_fanin_cone(wires[j], 4000)
    #                 wire_list = get_unique_fanin_cone(wires[j])
    #         for j in range(0, len(wire_list)):
    #             for k in range(0, len(wires)):
    #                 if wire_list[j].name == wires[k].name:
    #                     wires[k].mainout = wires[k].mainout + 1

    circuit_name = args.b[args.b.rfind("/")+1:args.b.rfind(".")]
    circuit_path = args.b[:args.b.rfind("/")+1]

    for i in range(len(outputs)):
        found = False
        for w_r in wires:
            if outputs[i].name == w_r.name:
                outputs[i] = w_r
                found = True
                break
        if not found:
            logging.critical("Error in replacing output wires!")
            exit()

    k_inputs = 0
    for w in inputs:
        if "keyinput" in w.name:
            k_inputs += 1

    circuit = Circuit(circuit_name, len(inputs)-k_inputs, len(outputs))
    circuit.k_inputs = k_inputs
    circuit.path = circuit_path
    circuit.max_level = max_lvl
    circuit.input_wires = inputs
    circuit.output_wires = outputs
    circuit.info = info
    circuit.wires = wires
    circuit.key = key_line

    logging.warning("bench : " + circuit_name + ", #gates: " + str(len(wires)-len(inputs)) + \
          ", #inputs: " + str(circuit.n_inputs) + ", #keys: " + str(circuit.k_inputs))
    logging.info("original key is: " + key_line)

    return circuit, wires


def wire_dep2(benchmark_address, args, circuit):
    # original version, but doesn't work on obfuscated circuits
    # wire class changed since last test
    # it is sensitive to order of lines
    inputs = []
    outputs = []
    wires = []
    input_array = []
    temp = []
    bench_file = open(benchmark_address)
    index = 0

    for line in bench_file:
        if "INPUT" in line:
            inputs.append(line[line.find("(") + 1:line.find(")")])
            input_array.append(line[line.find("(") + 1:line.find(")")])
            wires.append(wire(line[line.find("(") + 1:line.find(")")], "inp", [], index))
            input_array = []
            index += 1
        elif "OUTPUT" in line:
            out_name = line[line.find("(") + 1:line.find(")")]
            outputs.append(out_name)
        elif " = " in line:
            gate_out = line[0: line.find(" =")]
            gate_type = line[line.find("= ") + 2: line.find("(")]
            gate_list_inputs = line[line.find("(") + 1:line.find(")")]
            gate_oprs = gate_list_inputs.split(", ")
            for i in range(0, len(gate_oprs)):
                found = False
                for j in range(0, len(wires)):
                    if wires[j].name == gate_oprs[i]:
                        found = True
                        temp.append(wires[j])
                        break
                if not found:
                    print("ERROR")
                    print(gate_out, gate_oprs[i])
                    exit()
            max_level = 0
            for i in range(0, len(temp)):
                if temp[i].logic_level > max_level:
                    max_level = temp[i].logic_level

            temp_prob0 = 0.25
            temp_prob1 = 0.25
            for i in range(0, len(temp)):
                if len(temp) == 1:
                    if gate_type == "NOT" or gate_type == "not":
                        temp_prob = temp[0].prob0
                        temp_prob0 = temp[0].prob1
                        temp_prob1 = temp_prob
                    elif gate_type == "BUFF" or gate_type == "buff":
                        temp_prob0 = temp[0].prob0
                        temp_prob1 = temp[0].prob1
                else:
                    if gate_type == "NAND" or gate_type == "nand":
                        if i == 0:
                            temp_prob0 = temp[i].prob0
                            temp_prob1 = temp[i].prob1
                        else:
                            temp_prob0 = temp_prob0 * temp[i].prob0 + temp_prob1 * temp[i].prob0 + temp_prob0 * temp[
                                i].prob1
                            temp_prob1 = temp_prob1 * temp[i].prob1
                    elif gate_type == "AND" or gate_type == "and":
                        if i == 0:
                            temp_prob0 = temp[i].prob0
                            temp_prob1 = temp[i].prob1
                        else:
                            temp_prob0 = temp_prob0 * temp[i].prob0 + temp_prob1 * temp[i].prob0 + temp_prob0 * temp[
                                i].prob1
                            temp_prob1 = temp_prob1 * temp[i].prob1
                    elif gate_type == "NOR" or gate_type == "nor":
                        if i == 0:
                            temp_prob0 = temp[i].prob0
                            temp_prob1 = temp[i].prob1
                        else:
                            temp_prob0 = temp_prob0 * temp[i].prob0
                            temp_prob1 = 1 - temp_prob0
                    elif gate_type == "OR" or gate_type == "or":
                        if i == 0:
                            temp_prob0 = temp[i].prob0
                            temp_prob1 = temp[i].prob1
                        else:
                            temp_prob0 = temp_prob0 * temp[i].prob0
                            temp_prob1 = 1 - temp_prob0
                    elif gate_type == "XNOR" or gate_type == "xnor":
                        if i == 0:
                            temp_prob0 = temp[i].prob0
                            temp_prob1 = temp[i].prob1
                        else:
                            temp_prob0 = temp_prob0 * temp[i].prob0 + temp_prob1 * temp[i].prob1
                            temp_prob1 = 1 - temp_prob0
                    elif gate_type == "XOR" or gate_type == "xor":
                        if i == 0:
                            temp_prob0 = temp[i].prob0
                            temp_prob1 = temp[i].prob1
                        else:
                            temp_prob0 = temp_prob0 * temp[i].prob1 + temp_prob1 * temp[i].prob0
                            temp_prob1 = 1 - temp_prob0

            if gate_type == "NAND" or gate_type == "nand":
                temp_prob = temp_prob0
                temp_prob0 = temp_prob1
                temp_prob1 = temp_prob

            if gate_type == "NOR" or gate_type == "nor":
                temp_prob = temp_prob0
                temp_prob0 = temp_prob1
                temp_prob1 = temp_prob

            w = wire(gate_out, gate_type.lower(), temp, index)
            w.logic_level = max_level + 1
            w.prob0 = temp_prob0
            w.prob1 = temp_prob1
            w.absprob = abs(temp_prob0 - temp_prob1)
            wires.append(w)
            temp = []
            index += 1

    bench_file.close()

    # just check for correctness
    for i in range(0, len(wires)):
        for j in range(i+1, len(wires)):
            if wires[i].name == wires[j].name:
                print(wires[i].name, wires[j].name)
                print("ERROR in reading wires")
                exit()

    for i in range(0, len(wires)):
        fanout_temp = 0
        for j in range(0, len(wires)):
            if i != j:
                for k in range(0, len(wires[j].operands)):
                    if wires[i].name == wires[j].operands[k].name:
                        fanout_temp = fanout_temp + 1
        wires[i].fanout = fanout_temp

    # if circuit.mainout:
    #     for i in range(0, len(outputs)):
    #         for j in range(0, len(wires)):
    #             if wires[j].name == outputs[i]:
    #                 # wire_list = wire_fanin_cone(wires[j], 4000)
    #                 wire_list = get_unique_fanin_cone(wires[j])
    #         for j in range(0, len(wire_list)):
    #             for k in range(0, len(wires)):
    #                 if wire_list[j].name == wires[k].name:
    #                     wires[k].mainout = wires[k].mainout + 1
    return wires


def simple_read_bench(bench_path):
    # simplified read_bench function
    wires = []
    temp = []
    bench_file = open(bench_path)
    index = 0
    inputs = []
    outputs = []
    info = ""

    for line in bench_file:
        if "#" in line:
            info += line
            continue
        elif "input(" in line.lower():
            w = Wire(line[line.find("(") + 1:line.find(")")], "inp", [], index)
            wires.append(w)
            inputs.append(w)
        elif "output" in line.lower():
            w = Wire(line[line.find("(") + 1:line.find(")")], "out", [], 0)
            outputs.append(w)
            continue
            # wires.append(wire(line[line.find("(") + 1:line.find(")")], "out", [], 0, 0, 0, 0, 0, 0, 0, 0, index))
        elif " = " in line:
            gate_out = line[0: line.find(" =")]
            gate_type = line[line.find("= ") + 2: line.find("(")].lower()
            gate_list_inputs = line[line.find("(") + 1:line.find(")")]
            gate_oprs = gate_list_inputs.split(",")
            gate_oprs = [x.strip(' ') for x in gate_oprs]
            for i in range(0, len(gate_oprs)):
                found = False
                for j in range(0, len(wires)):
                    if wires[j].name == gate_oprs[i]:
                        found = True
                        temp.append(wires[j])
                        break
                if not found:
                    # print gate_out, gate_oprs[i]
                    temp.append(Wire(gate_oprs[i], "dummy", [], 0))
            wires.append(Wire(gate_out, gate_type.lower(), temp, index))
        else:
            continue

        temp = []
        index += 1

    bench_file.close()

    for i in range(0, len(wires)):
        for j in range(0, len(wires[i].operands)):
            if wires[i].operands[j].type == "dummy":
                found = False
                for k in range(0, len(wires)):
                    if wires[k].name == wires[i].operands[j].name:
                        found = True
                        wires[i].operands[j] = wires[k]
                        break
                if not found:
                    logging.critical(wires[i].operands[j].name)
                    logging.critical("ERROR1")
                    exit()

    for i in range(0, len(wires)):
        fanout_temp = 0
        for j in range(0, len(wires)):
            if i != j:
                for k in range(0, len(wires[j].operands)):
                    if wires[i].name == wires[j].operands[k].name:
                        fanout_temp = fanout_temp + 1
        wires[i].fanout = fanout_temp

    # just to be sure!
    for i in range(len(wires)):
        if wires[i].name != wires[wires[i].index].name:
            logging.critical(wires[i].name)
            logging.critical("ERROR2 in read_circuit()")
            exit()

    circuit_name = bench_path[bench_path.rfind("/")+1:bench_path.rfind(".")]

    logging.warning("bench : " + circuit_name + ", number of gates: " + str(len(wires)-len(inputs)) + \
          ", number of inputs: " + str(len(inputs)))

    circuit = Circuit(circuit_name, len(inputs), len(outputs))
    circuit.input_wires = inputs
    circuit.output_wires = outputs
    circuit.info = info

    return circuit, wires
