from random import randint
from dateutil.relativedelta import relativedelta
import logging


def wire_print(wire_in):
    print("wire_name: ", wire_in.name)
    print("cell_type: ", wire_in.type)
    for i in range(0, len(wire_in.operands)):
        print("opr", i, ": ", wire_in.operands[i].name)
    print("logic_level: ", wire_in.logic_level)
    print("prob0:", wire_in.prob0)
    print("prob1:", wire_in.prob1)
    print("abs_prob:", wire_in.absprob)
    print("fanout:", wire_in.fanout)
    # print "mainout:", wire_in.mainout
    print("index:", wire_in.index)
    print("slack:", wire_in.slack)
    print("path_delay:", wire_in.delay, "\n")


def print_cone(wire_list):
    for i in range(len(wire_list)):
        print('  ' * wire_list[i].logic_level + wire_list[i].name)


def check_b2b_inwires(wires, selected):
    # check for inserted mux in previous level
    for i in range(0, len(wires[selected].operands)):
        if wires[selected].operands[i].type == "mux":
            tmp_w = wires[selected].operands[i]
            for j in range(len(tmp_w.operands)):
                if tmp_w.operands[j].name.find("keyinput"):
                    logging.warnings("b2b found in input of " + wires[selected].name + " connected to " + wires[selected].operands[i].name)
                    return False
    print("INCOMPLETE FUNCTION")
    exit()
    for i in range(len(wires)):
        if selected != i:
            for j in range(0, len(wires[i].operands)):
                if wires[i].operands[j].name == wires[selected].name and wires[i].operands[j].tag != 0:
                    logging.warnings("b2b found in output of " + wires[selected].name + " connected to " + wires[i].name)
                    return False
    return True


def check_b2b(wires, selected):
    for i in range(0, len(wires[selected].operands)):
        if wires[selected].operands[i].tag != 0:
            logging.warnings("b2b found in input of " + wires[selected].name + " connected to " + wires[selected].operands[i].name)
            return False

    for i in range(len(wires)):
        if selected != i:
            for j in range(0, len(wires[i].operands)):
                if wires[i].operands[j].name == wires[selected].name and wires[i].operands[j].tag != 0:
                    logging.warnings("b2b found in output of " + wires[selected].name + " connected to " + wires[i].name)
                    return False
    return True


def add_switch(input1, input2, output1, output2, select1):
    new_line = output1 + " = mux(" + select1 + ", " + input1 + ", " + input2 + ")\n"
    new_line += output2 + " = mux(" + select1 + ", " + input2 + ", " + input1 + ")\n"
    return new_line


def chomp(x):
    if x.endswith("\r\n"): return x[:-2]
    if x.endswith("\n"): return x[:-1]
    return x


def write_output(cpwires, num_of_path, bench_address, obf_kind):
    bench_file_name = bench_address[bench_address.find("original/") + 9: bench_address.find(".bench")]
    bench_folder = bench_address[0: bench_address.find("original/")]
    bench_file = open(bench_address)

    prev_key_size = 0
    key = "# key="
    for line in bench_file:
        if "# key=" in line:
            key = line
            prev_key_size = len(line)-7
            break
    key = chomp(key)

    new_bench = ""
    for i in range(prev_key_size + num_of_path/2):
        new_bench += "INPUT(keyinput" + str(i) + ")\n"

    bench_file = open(bench_address)
    for line in bench_file:
        if "INPUT" in line:
            if "INPUT(keyinput" not in line:
                new_bench += line
        elif "OUTPUT" in line:
            new_bench += line
        elif "#" in line:
            continue
        elif " = " in line:
            gate_type = line[line.find("= ") + 2: line.find("(")]
            gate_out = line[0: line.find(" =")]
            found = False
            for i in range(0, len(cpwires)):
                if gate_out == cpwires[i].name:
                    found = True
                    if cpwires[i].tag != 0:
                        new_bench += line.replace(gate_out, gate_out + "_enc")
                    else:
                        new_bench += line
                    break
            if not found:
                new_bench += line
        else:
            new_bench += line

    bench_file.close()

    new_bench += '\n'
    for i in range(1, num_of_path, 2):
        gate_out1 = ""
        gate_out2 = ""
        for j in range(0, len(cpwires)):
            if cpwires[j].tag == i:
                gate_out1 = cpwires[j].name
                break
        for j in range(0, len(cpwires)):
            if cpwires[j].tag == i+1:
                gate_out2 = cpwires[j].name
                break

        if randint(0, 1) == 0:
            key += '0'
            new_bench += add_switch(gate_out1 + "_enc", gate_out2 + "_enc", gate_out1, gate_out2,
                                 "keyinput" + str(prev_key_size + i/2))
        else:
            key += '1'
            new_bench += add_switch(gate_out1 + "_enc", gate_out2 + "_enc", gate_out2, gate_out1,
                                 "keyinput" + str(prev_key_size + i/2))

    new_bench = key + "\n" + new_bench
    new_bench_address = bench_folder + obf_kind + "/" + bench_file_name + "_" + str(num_of_path) + ".bench"
    new_bench_file = open(new_bench_address, 'w')
    new_bench_file.write(new_bench)
    new_bench_file.close()
    logging.info("written bench to: " + new_bench_address)


def write_mux_output(cpwires, mux_list, bench_address, obf_kind):
    bench_file_name = bench_address[bench_address.find("original/") + 9: bench_address.find(".bench")]
    bench_folder = bench_address[0: bench_address.find("original/")]
    bench_file = open(bench_address)

    prev_key_size = 0
    key = "# key="
    for line in bench_file:
        if "# key=" in line:
            key = line
            prev_key_size = len(line)-7
            break
    key = chomp(key)

    new_bench = ""
    for i in range(prev_key_size + len(mux_list)):
        new_bench += "INPUT(keyinput" + str(i) + ")\n"

    bench_file = open(bench_address)
    for line in bench_file:
        if "INPUT" in line:
            if "INPUT(keyinput" not in line:
                new_bench += line
        elif "OUTPUT" in line:
            new_bench += line
        elif "#" in line:
            continue
        elif " = " in line:
            gate_type = line[line.find("= ") + 2: line.find("(")]
            gate_out = line[0: line.find(" =")]
            found = False
            for i in range(0, len(mux_list)):
                if gate_out == mux_list[i][2].name:
                    found = True
                    new_bench += line.replace(mux_list[i][0].name, mux_list[i][0].name + "_enc")
                    break
            if not found:
                new_bench += line
        else:
            new_bench += line

    bench_file.close()

    new_bench += '\n'
    i = 0
    for mux_inputs in mux_list:
        gate_out1 = mux_inputs[0].name
        gate_out2 = mux_inputs[1].name

        if randint(0, 1) == 0:
        # if True:
            key += '0'
            new_bench += gate_out1 + "_enc = mux(" + "keyinput" + str(prev_key_size + i) + ", " + gate_out1 + ", " + gate_out2 + ")\n"
        else:
            key += '1'
            new_bench += gate_out1 + "_enc = mux(" + "keyinput" + str(prev_key_size + i) + ", " + gate_out2 + ", " + gate_out1 + ")\n"
        i += 1

    new_bench = key + "\n" + new_bench
    new_bench_address = bench_folder + obf_kind + "/" + bench_file_name + "_" + str(len(mux_list)) + ".bench"
    new_bench_file = open(new_bench_address, 'w')
    new_bench_file.write(new_bench)
    new_bench_file.close()
    logging.warning("written bench to: " + new_bench_address)


def diff(t_a, t_b):
    t_diff = relativedelta(t_b, t_a)  # later/end time comes first!
    return '{h}h {m}m {s}s'.format(h=t_diff.hours, m=t_diff.minutes, s=t_diff.seconds)


def wires2bench(args, circuit, wires, aux_wires, key_string):
    bench_address = args.b
    obf_kind = args.m
    bench_file_name = circuit.name
    bench_folder = bench_address[0: bench_address.rfind("/", 0, bench_address.rfind("/"))] + "/"

    old_key_line = "# key=\n"
    bench_file = open(bench_address)
    for line in bench_file:
        if "# key" in line:
            old_key_line = line
            break

    num_of_path = 0
    new_bench = old_key_line + "# key-" + args.m + "=" + key_string + "\n\n"

    wires_list = wires
    wires_list += aux_wires

    for i in range(len(wires_list)):
        if wires_list[i].type == "inp":
            new_bench += "INPUT(" + wires_list[i].name + ")\n"
            if "keyinput" in wires_list[i].name:
                num_of_path += 1

    new_bench += "\n"

    for i in range(len(circuit.output_wires)):
        new_bench += "OUTPUT(" + circuit.output_wires[i].name + ")\n"
    new_bench += "\n"

    for i in range(len(wires_list)):
        if wires_list[i].type != "inp":
            if len(wires_list[i].operands) > 0:
                if wires_list[i].type == "not":
                    if len(wires_list[i].operands) > 1:
                        logging.critical("wire " + wires_list[i].name + " should have one input!")
                operands = wires_list[i].operands[0].name
                for j in range(1, len(wires_list[i].operands)):
                    operands += ', ' + wires_list[i].operands[j].name
                new_bench += wires_list[i].name + " = " + wires_list[i].type + "(" + operands + ")\n"
            else:
                logging.warning("wire " + wires_list[i].name + " is ignored!")
    # new_bench += "\n"

    new_bench_address = bench_folder + obf_kind + "/" + bench_file_name + "_" + str(num_of_path) + ".bench"
    new_bench_file = open(new_bench_address, 'w')
    new_bench_file.write(new_bench)
    new_bench_file.close()
    logging.info("written bench to: " + new_bench_address)

    return new_bench_address
