from datetime import datetime
from cycsat import cycsat_util
import logging


def write_output(added_lines, bench_address):
    new_bench = "INPUT(DUMMY_IN)\n"
    key_s = ""

    bench_file = open(bench_address)
    first_output = True
    for line in bench_file:
        if "INPUT" in line:
            new_bench += line
        elif "OUTPUT" in line:
            if first_output:
                first_output = False
                new_bench += "OUTPUT(DUMMY_OUT)\n"
            new_bench += line
        elif "key=" in line:
            key_s = line
        elif "#" in line:
            continue
        else:
            new_bench += line

    bench_file.close()

    new_bench += "\nNOT_DUMMY_IN = NOT(DUMMY_IN)\n"
    new_bench += "ONE = OR(NOT_DUMMY_IN, DUMMY_IN)\n"
    new_bench += '\n' + added_lines
    new_bench = "# Modified for CycSAT Attack\n" + key_s + "\n" + new_bench

    bench_file_name = bench_address[bench_address.rfind("/") + 1:]
    bench_folder = bench_address[0: bench_address.rfind("/")]
    new_bench_address = bench_folder + "_cycsat/" + bench_file_name
    new_bench_file = open(new_bench_address, 'w')
    new_bench_file.write(new_bench)
    new_bench_file.close()
    print(new_bench_address)


def glsvlsi18(wires, cycle):
    # for CycSAT-II on our paper

    conditions = []
    for c in range(len(cycle)):
        pre_index = cycle[c - 1]
        cur_index = cycle[c]
        nex_index = cycle[(c + 1) % len(cycle)]

        if wires[cur_index].type == "nand" and "SRL" in wires[cur_index].name:
            # for glsvlsi18 paper
            # print cycle
            # print wires[cur_index].name
            # print wires[cur_index].operands[0].name
            conditions.append(wires[cur_index].operands[0].name)
            conditions.append(1)
            # exit()
            # break
    return conditions


def cycsat_date18(bench_address):
    # for CycSAT-II on Hai Zhou DATE18 paper (auxiliary circuit)

    input_str = "INPUT(DUMMY_IN)\n"
    output_str = "OUTPUT(DUMMY_OUT)\n"
    circuit_str = ""
    xor_list = []
    aux_in_list = []

    bench_file = open(bench_address)
    keys_line_glsvlis = ""
    for line in bench_file:
        if "INPUT" in line:
            input_str += line
        elif "OUTPUT" in line:
            output_str += line
        elif "# key=" in line:
            keys_line_glsvlis = line
        elif "# key-date" in line:
            keys_line_date = line
        elif "#" in line:
            continue
        else:
            circuit_str += line
            if " = xor(mux_" in line:
                if "xor1_" in line:
                    xor_list.append(line[line.find("xor1_"):line.find(" = ")])
                elif "xor0_" in line:
                    aux_in_list.append(line[line.find(",")+2:line.find(")")])

    bench_file.close()

    if len(aux_in_list) != len(xor_list):
        logging.critical("Something is wrong!")

    # remove keys=
    keys_str = keys_line_date[keys_line_date.find("=")+1:]
    offset = len(keys_line_glsvlis[keys_line_glsvlis.find("=") + 1:]) - 1

    # add the new dummy keys to the input ports
    # for i in range(len(aux_in_list)):
    #     input_str += "INPUT(keyinput" + str(len(keys_str) + offset - 1 + i) + ")\n"
    # input_str += "\n"

    # generate cycsat nc3 clauses
    added_circuit_str = ""
    for i in range(len(aux_in_list)):
        # new_key_i = len(keys_str) + offset - 1 + i

        if keys_str[2*i] == "0":
            key0c = "DUMMY_W" + str(2*i+offset)
            key0o = "keyinput" + str(2 * i + offset)
        else:
            key0c = "keyinput" + str(2*i+offset)
            key0o = "DUMMY_W" + str(2 * i + offset)

        if keys_str[2*i+1] == "0":
            key1c = "DUMMY_W" + str(2*i+1+offset)
            key1o = "keyinput" + str(2 * i + 1 + offset)
        else:
            key1c = "keyinput" + str(2*i+1+offset)
            key1o = "DUMMY_W" + str(2 * i + 1 + offset)

        # line = "out" + str(i) + " = mux(keyinput" + str(new_key_i) + ", " + xor_list[i] + ", " + aux_in_list[0] + ")\n"
        line = "and_key" + str(i) + " = and(" + key0c + ", " + key1c + ")\n"

        line += "reducible_" + str(2 * i) + " = or(" + key0o + ", and_key" + str(i) + ")\n"
        line += "reducible_" + str(2 * i + 1) + " = or(" + key1o + ", and_key" + str(i) + ")\n"

        # line += "reducible_" + str(2 * i) + " = or(keyinput" + str(new_key_i) + ", and_key" + str(i) + ")\n"
        # line += "reducible_" + str(2 * i + 1) + " = or(keyinput" + str(new_key_i) + ", and_key" + str(i) + ")\n"

        line += "nc3_" + str(i) + " = and(reducible_" + str(2 * i) + ", reducible_" + str(2 * i + 1) + ")\n"

        line += "\n"
        added_circuit_str += line

    # replace xor1_# in circuit_str with out#
    # for i in range(len(xor_list)):
    #     circuit_str = circuit_str.replace(xor_list[i], "out" + str(i), 1)

    # add inverted keys
    for i in range(len(keys_str) + offset - 1):
        added_circuit_str += "DUMMY_W" + str(i) + " = not(keyinput" + str(i) + ")\n"

    # add dummy_out signal
    added_circuit_str += "DUMMY_OUT = AND(ONE"
    for i in range(len(aux_in_list)):
        added_circuit_str += ", " + "nc3_" + str(i)
    added_circuit_str += ")\n"

    # add auxiliary signals
    circuit_str += "\nNOT_DUMMY_IN = NOT(DUMMY_IN)\n"
    circuit_str += "ONE = OR(NOT_DUMMY_IN, DUMMY_IN)\n\n"

    new_bench = "# Modified for CycSAT Attack\n" + keys_line_glsvlis + keys_line_date + "\n" + input_str + output_str + circuit_str + added_circuit_str

    bench_file_name = bench_address[bench_address.rfind("/") + 1:]
    bench_folder = bench_address[0: bench_address.rfind("/")]
    new_bench_address = bench_folder + "_cycsat/" + bench_file_name
    new_bench_file = open(new_bench_address, 'w')
    new_bench_file.write(new_bench)
    new_bench_file.close()
    print(new_bench_address)
    exit()


def cycsat1(wires, cycle):
    # for CycSAT-I on Kaveh Shamsi paper

    # for ignoring cycles in date18 paper, comment out for the normal cycsat1
    # for c in cycle:
    #     if wires[c].type == "mux" and "mux_" in wires[c].name:
    #         return []

    conditions = []
    for c in range(len(cycle)):
        pre_index = cycle[c - 1]
        cur_index = cycle[c]
        nex_index = cycle[(c + 1) % len(cycle)]

        if wires[cur_index].type == "mux":
            # print cycle[c]
            for o in range(len(wires[cur_index].operands)):
                # print wire.operands[o].name, cycle[(c+1) % len(cycle)], cycle[c-1]
                if wires[cur_index].operands[o] == wires[nex_index]:
                    # clause.append(cycle[(c+1) % len(cycle)])
                    conditions.append(wires[cur_index].operands[0].name)
                    conditions.append(o - 1)
                    break
                elif wires[cur_index].operands[o] == wires[pre_index]:
                    # clause.append(cycle[c-1])
                    conditions.append(wires[cur_index].operands[0].name)
                    conditions.append(o - 1)
                    break
    return conditions


def cyc_sat(args, wires, cycle_list):
    condition_list = []
    z = 0

    # cycle_list is list of cycles, each cycle is a list of wire indexes
    t_a = datetime.now()

    # find conditions that create a cycle
    for cycle in cycle_list:
        if args.m:
            conditions = glsvlsi18(wires, cycle)
            # conditions = date18(wires, cycle)
        else:
            conditions = cycsat1(wires, cycle)
        if len(conditions) < 1:
            continue

        if len(cycle_list) > 5000:
            if z % 5000 == 0:
                print("processed: " + str(z) + "/" + str(len(cycle_list)))
        z += 1

        if args.p:
            print(conditions)

        clause = []
        # convert conditions to c1 and c2 and c3 and ... without using additional not gates
        for i in range(0, len(conditions), 2):
            if conditions[i+1] == 0 and "inv_keyinput" in conditions[i]:
                clause.append("keyinput" +  conditions[i][12:])
            elif conditions[i+1] == 0 and "inv_keyinput" not in conditions[i]:
                clause.append("inv_keyinput" + conditions[i][8:])
            else:
                clause.append(conditions[i])
        condition_list.append(clause)

    # for removing duplicate conditions
    unique_conditions = [list(x) for x in set(tuple(x) for x in condition_list)]

    if args.p:
        print('\n' + str(unique_conditions))

    d = 0
    new_line = ""
    for condition in unique_conditions:
        if len(condition) == 1:
            new_line += "DUMMY_W" + str(d) + " = "
            new_line += "NOT(" + condition[0] + ")\n"
        else:
            new_line += "DUMMY_D_" + str(d) + " = "
            new_line += "AND(" + condition[0]
            for i in range(1, len(condition)):
                new_line += ", " + condition[i]
            new_line += ")\n"
            new_line += "DUMMY_W" + str(d) + " = " + "NOT(DUMMY_D_" + str(d) + ")\n"
        d += 1

    for i in range(len(wires)):
        if wires[i].type == "inp":
            if "keyinput" in wires[i].name:
                new_line += "inv_" + wires[i].name + " = " + "NOT(" + wires[i].name + ")\n"

    # connect all dummy wires to the new port named dummy_out
    if len(unique_conditions) > 0:
        new_line += "DUMMY_OUT = AND(ONE"
        for i in range(0, d):
            new_line += ", " + "DUMMY_W" + str(i)
        new_line += ")\n"
    else:
        new_line += "DUMMY_OUT = BUFF(ONE)\n"

    t_b = datetime.now()
    print("time for interpreting new clauses: " + cycsat_util.diff(t_a, t_b))
    return new_line


def test(args, wires):
    key = ""
    for w in wires:
        for o in w.operands:
            if "keyinput" in o.name and "inv_keyinput" not in o.name:
                # print w.name
                if w.type == "mux":
                    if w.name in w.operands[1].name:
                        key += "0"
                    elif w.name in w.operands[2].name:
                        key += "1"
                    else:
                        print("error:" + w.name)
                        key += "X"
                        break
                elif w.type == "xor":
                    key += "0"
                elif w.type == "xnor":
                    key += "1"
                elif w.type == "not":
                    break
                else:
                    print("error2")
                    exit()
                break
    print(key)
    exit()
