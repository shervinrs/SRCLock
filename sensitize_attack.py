import argparse
import logging

from srclock import circuit


def get_fanout_cone(wire_in, fanout_cone):
    fanout_cone.append(wire_in)
    for i in range(len(wire_in.fanouts)):
        get_fanout_cone(wire_in.fanouts[i], fanout_cone)


def sa(args, target_circuit, wires):
    keys = []
    for input in target_circuit.input_wires:
        if "key" in input.name:
            keys.append(input)

    for key in keys:
        for w in wires:
            w.value = -1

        print("Key: " + key.name)
        is_valid = propagate_key_out(key, keys)

        if is_valid == True:
            print(key.name + " is sensitizable at: ")
            for input in target_circuit.input_wires:
                if input not in keys:
                    print("\t" + input.name + ": " + str(input.value))
        else:
            print(key.name + " is not sensitizable.\n")


# Recursive function that attempts to find values in preceding gates in order to achieve an
# output for the specified gate. Returns true if it successfully reaches an input and sets its
# value. Returns false if it cannot.
# In particular, it is looking for inputs to gates that are key bits, and sets the other input
# to mute that key. If it is unable to do that, the function returns false.
def propagate_key_in(wire, keys):
    # print "Going inward. Wire: " + wire.name
    # print "\tOperands:"
    # for op in wire.operands:
    # 	print "\t\t" + op.name

    is_valid = True

    if wire.type == "not":
        if wire.value == 1:
            wire.operands[0].value = 0
        elif wire.value == 0:
            wire.operands[0].value = 1

        if wire.operands[0].type != "inp":
            is_valid = propagate_key_in(wire.operands[0], keys)
        else:
            if wire.operands[0] in keys:
                is_valid = False

    if wire.type == "and":
        if wire.value == 1:
            for op in wire.operands:
                op.value = 1
                if op.type != "inp":
                    is_valid = propagate_key_in(op, keys)
                else:
                    if op in keys:
                        is_valid = False

        elif wire.value == 0:
            wire.operands[0].value = 0
            if wire.operands[0].type != "inp":
                is_valid = propagate_key_in(wire.operands[0], keys)

                if is_valid == False:
                    wire.operands[0].value = 1
                    is_valid = propagate_key_in(wire.operands[0], keys)
                    if is_valid != False:
                        wire.operands[1].value = 0
                        if wire.operands[1].type != "inp":
                            is_valid = propagate_key_in(wire.operands[1], keys)
                        else:
                            if wire.operands[1] in keys:
                                is_valid = False
                else:
                    wire.operands[1].value = 0
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                        if is_valid == False:
                            wire.operands[1].value = 1
                            is_valid = propagate_key_in(wire.operands[1], keys)
            else:
                if wire.operands[0] in keys:
                    wire.operands[1].value = 0
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                    else:
                        is_valid = False

    elif wire.type == "nand":
        if wire.value == 1:
            wire.operands[0].value = 0
            if wire.operands[0].type != "inp":
                is_valid = propagate_key_in(wire.operands[0], keys)

                if is_valid == False:
                    wire.operands[0].value = 1
                    is_valid = propagate_key_in(wire.operands[0], keys)
                    if is_valid != False:
                        wire.operands[1].value = 0
                        if wire.operands[1].type != "inp":
                            is_valid = propagate_key_in(wire.operands[1], keys)
                        else:
                            if wire.operands[1] in keys:
                                is_valid = False
                else:
                    wire.operands[1].value = 0
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                        if is_valid == False:
                            wire.operands[1].value = 1
                            is_valid = propagate_key_in(wire.operands[1], keys)
            else:
                if wire.operands[0] in keys:
                    wire.operands[1].value = 0
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                    else:
                        is_valid = False

        elif wire.value == 0:
            for op in wire.operands:
                op.value = 1
                if op.type != "inp":
                    is_valid = propagate_key_in(op, keys)
                else:
                    if op in keys:
                        is_valid = False

    elif wire.type == "or":
        if wire.value == 1:
            wire.operands[0].value = 1
            if wire.operands[0].type != "inp":
                is_valid = propagate_key_in(wire.operands[0], keys)

                if is_valid == False:
                    wire.operands[0].value = 0
                    is_valid = propagate_key_in(wire.operands[0], keys)
                    if is_valid != False:
                        wire.operands[1].value = 1
                        if wire.operands[1].type != "inp":
                            is_valid = propagate_key_in(wire.operands[1], keys)
                        else:
                            if wire.operands[1] in keys:
                                is_valid = False
                else:
                    wire.operands[1].value = 1
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                        if is_valid == False:
                            wire.operands[1].value = 0
                            is_valid = propagate_key_in(wire.operands[1], keys)
            else:
                if wire.operands[0] in keys:
                    wire.operands[1].value = 1
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                    else:
                        is_valid = False

        elif wire.value == 0:
            for op in wire.operands:
                op.value = 0
                if op.type != "inp":
                    is_valid = propagate_key_in(op, keys)
                else:
                    if op in keys:
                        is_valid = False
    elif wire.type == "nor":
        if wire.value == 1:
            for op in wire.operands:
                op.value = 0
                if op.type != "inp":
                    is_valid = propagate_key_in(op, keys)
                else:
                    if op in keys:
                        is_valid = False
        elif wire.value == 0:
            wire.operands[0].value = 1
            if wire.operands[0].type != "inp":
                is_valid = propagate_key_in(wire.operands[0], keys)

                if is_valid == False:
                    wire.operands[0].value = 0
                    is_valid = propagate_key_in(wire.operands[0], keys)
                    if is_valid != False:
                        wire.operands[1].value = 1
                        if wire.operands[1].type != "inp":
                            is_valid = propagate_key_in(wire.operands[1], keys)
                        else:
                            if wire.operands[1] in keys:
                                is_valid = False
                else:
                    wire.operands[1].value = 1
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                        if is_valid == False:
                            wire.operands[1].value = 0
                            is_valid = propagate_key_in(wire.operands[1], keys)
            else:
                if wire.operands[0] in keys:
                    wire.operands[1].value = 1
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                    else:
                        is_valid = False

    elif wire.type == "xor":
        if wire.value == 1:
            wire.operands[0].value = 1
            if wire.operands[0].type != "inp":
                is_valid = propagate_key_in(wire.operands[0], keys)
                if is_valid == False:
                    wire.operands[0].value = 0
                    is_valid = propagate_key_in(wire.operands[0], keys)
                    if is_valid != False:
                        wire.operands[1].value = 1
                        if wire.operands[1].type != "inp":
                            is_valid = propagate_key_in(wire.operands[1], keys)
                        else:
                            if "key" in wire.operands[1].name:
                                # if wire.operands[1] in keys:
                                is_valid = False
                else:
                    wire.operands[1].value = 0
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                    else:
                        if "key" in wire.operands[1].name:
                            # if wire.operands[1] in keys:
                            is_valid = False
            else:
                if "key" in wire.operands[0].name:
                    # if wire.operands[0] in keys:
                    is_valid = False

        elif wire.value == 0:
            wire.operands[0].value = 1
            if wire.operands[0].type != "inp":
                is_valid = propagate_key_in(wire.operands[0], keys)
                if is_valid == False:
                    wire.operands[0].value = 0
                    is_valid = propagate_key_in(wire.operands[0], keys)
                    if is_valid != False:
                        wire.operands[1].value = 0
                        if wire.operands[1].type != "inp":
                            is_valid = propagate_key_in(wire.operands[1], keys)
                        else:
                            if "key" in wire.operands[1].name:
                                # if wire.operands[1] in keys:
                                is_valid = False
                else:
                    wire.operands[1].value = 1
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                    else:
                        if "key" in wire.operands[1].name:
                            # if wire.operands[1] in keys:
                            is_valid = False
            else:
                if "key" in wire.operands[0].name:
                    # if wire.operands[0] in keys:
                    is_valid = False

    elif wire.type == "xnor":
        if wire.value == 1:
            wire.operands[0].value = 1
            if wire.operands[0].type != "inp":
                is_valid = propagate_key_in(wire.operands[0], keys)
                if is_valid == False:
                    wire.operands[0].value = 0
                    is_valid = propagate_key_in(wire.operands[0], keys)
                    if is_valid != False:
                        wire.operands[1].value = 0
                        if wire.operands[1].type != "inp":
                            is_valid = propagate_key_in(wire.operands[1], keys)
                        else:
                            if "key" in wire.operands[1].name:
                                # if wire.operands[1] in keys:
                                is_valid = False
                else:
                    wire.operands[1].value = 1
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                    else:
                        if "key" in wire.operands[1].name:
                            # if wire.operands[1] in keys:
                            is_valid = False
            else:
                if "key" in wire.operands[0].name:
                    # if wire.operands[0] in keys:
                    is_valid = False

        elif wire.value == 0:
            wire.operands[0].value = 1
            if wire.operands[0].type != "inp":
                is_valid = propagate_key_in(wire.operands[0], keys)
                if is_valid == False:
                    wire.operands[0].value = 0
                    is_valid = propagate_key_in(wire.operands[0], keys)
                    if is_valid != False:
                        wire.operands[1].value = 1
                        if wire.operands[1].type != "inp":
                            is_valid = propagate_key_in(wire.operands[1], keys)
                        else:
                            if "key" in wire.operands[1].name:
                                # if wire.operands[1] in keys:
                                is_valid = False
                else:
                    wire.operands[1].value = 0
                    if wire.operands[1].type != "inp":
                        is_valid = propagate_key_in(wire.operands[1], keys)
                    else:
                        if "key" in wire.operands[1].name:
                            # if wire.operands[1] in keys:
                            is_valid = False
            else:
                if "key" in wire.operands[0].name:
                    # if wire.operands[0] in keys:
                    is_valid = False
    # if is_valid == True:
    # 	print "Wire " + wire.name + " has a valid value of " + str(wire.value)

    return is_valid


# Recursive function that propagates a key value through a circuit
# Returns true if it can propagate to an output. False if it can not
def propagate_key_out(wire, keys):
    # print "Going outward. Wire: " + wire.name

    is_valid = True

    for f in wire.fanouts:
        print("\t" + f.name)
        is_valid = True
        f.value = wire.value
        if f.type == "and":
            for op in f.operands:
                if op is not wire and op not in keys:
                    op.value = 1
                    is_valid = propagate_key_in(op, keys)

        elif f.type == "nand":
            f.value ^= 1
            for op in f.operands:
                if op is not wire and op not in keys:
                    op.value = 1
                    is_valid = propagate_key_in(op, keys)

            for f2 in f.fanouts:
                if f2.type == "nand" or f2.type == "xor":
                    for op2 in f.operands:
                        if op2 is not f2 and op2 not in keys:
                            op2.value = 1
                            is_valid = propagate_key_in(op2, keys)
                elif f2.type == "nor" or f2.type == "xnor":
                    for op2 in f.operands:
                        if op2 is not f2 and op2 not in keys:
                            op2.value = 0
                            is_valid = propagate_key_in(op2, keys)
                else:
                    is_valid = False

        elif f.type == "or":
            for op in f.operands:
                if op is not wire and op not in keys:
                    op.value = 0
                    is_valid = propagate_key_in(op, keys)
        elif f.type == "nor":
            f.value ^= 1
            for op in f.operands:
                if op is not wire and op not in keys:
                    op.value = 0
                    is_valid = propagate_key_in(op, keys)

            for f2 in f.fanouts:
                if f2.type == "nand" or f2.type == "xor":
                    for op2 in f.operands:
                        if op2 is not f2 and op2 not in keys:
                            op2.value = 1
                            is_valid = propagate_key_in(op2, keys)
                elif f2.type == "nor" or f2.type == "xnor":
                    for op2 in f.operands:
                        if op2 is not f2 and op2 not in keys:
                            op2.value = 0
                            is_valid = propagate_key_in(op2, keys)
                else:
                    is_valid = False
        elif f.type == "xor":
            print
            "\t\tOperands: "
            for op in f.operands:
                print("\t\t\t" + op.name)
                if op.name is not wire.name:
                    if "key" not in op.name:
                        op.value = 0
                        is_valid = propagate_key_in(op, keys)
                    else:
                        is_valid = False

        elif f.type == "xnor":
            print("\t\tOperands: ")
            for op in f.operands:
                print("\t\t\t" + op.name)
                if op.name is not wire.name:
                    if "key" not in op.name:
                        op.value = 1
                        is_valid = propagate_key_in(op, keys)
                    else:
                        is_valid = False
        elif f.type == "not":
            f.value ^= 1
            for f2 in f.fanouts:
                if f2.type == "nand" or f2.type == "xor":
                    for op2 in f.operands:
                        if op2 is not f2 and op2 not in keys:
                            op2.value = 1
                            is_valid = propagate_key_in(op2, keys)
                elif f2.type == "nor" or f2.type == "xnor":
                    for op2 in f.operands:
                        if op2 is not f2 and op2 not in keys:
                            op2.value = 0
                            is_valid = propagate_key_in(op2, keys)
                else:
                    is_valid = False

        if is_valid != False:
            is_valid = propagate_key_out(f, keys)

    # if is_valid == True:
    # 	print "Wire " + wire.name + " has a valid value of " + str(wire.value)

    return is_valid


# Test function to see if gate values work.
def calc_output(wires, inputs, output_wires):
    outputs_found = False
    output_val = -1
    for wire in wires:
        wire.value = -1

    while outputs_found == False:
        i = 0
        for wire in wires:
            if wire.type == "inp":
                wire.value = inputs[i]
                i = i + 1
            elif wire.type == "not":
                not_input = wire.operands[0]
                if not_input.value != -1:
                    if not_input.value == 0:
                        wire.value = 1
                    else:
                        wire.value = 0
            elif wire.type == "xor":
                xor_input1 = wire.operands[0]
                xor_input2 = wire.operands[1]
                if xor_input1.value != -1 and xor_input2.value != -1:
                    if xor_input1.value == xor_input2.value:
                        wire.value = 0
                    else:
                        wire.value = 1

            elif wire.type == "xnor":
                xor_input1 = wire.operands[0]
                xor_input2 = wire.operands[1]
                if xor_input1.value != -1 and xor_input2.value != -1:
                    if xor_input1.value == xor_input2.value:
                        wire.value = 1
                    else:
                        wire.value = 0

            elif wire.type == "mux":
                mux_key = wire.operands[0]
                mux_input1 = wire.operands[1]
                mux_input2 = wire.operands[2]
                if mux_key.value != -1:
                    if mux_key.value == 0:
                        wire.value = mux_input1.value
                    else:
                        wire.value = mux_input2.value

            # print(wire.name + "= " + str(wire.value))
            # if len(wire.fanouts) == 0:
            if wire.name == output_wires[0].name:  # TODO: Account for more than one output
                if wire.value != -1:
                    output_val = wire.value
                    outputs_found = True
    # print ("\n")
    return output_val


def find_runs_of_keys(keys):
    logging.info("Finding runs of keys")
    runs = []
    return runs


def brute_force(wires, target_circuit, num_keys):
    logging.info("Performing brute force")
    inputs = [0, 0, 0, 0, 0]
    for i in range(0, 2 ** (len(inputs))):
        output = calc_output(wires, inputs, target_circuit.output_wires)
        print("Inputs: " + str(inputs) + ", Output: " + str(output))

        for j in range(0, len(inputs)):
            inputs[j] = (((i + 1) >> j) % 2) & 0xFF


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(levelname)s:: %(message)s", datefmt="%H:%M:%S")
    logging.getLogger().setLevel(level=logging.INFO)
    logging.getLogger().handlers[0].setFormatter(
        logging.Formatter("%(asctime)s.%(msecs)04d %(funcName)s %(levelname)s:: %(message)s", datefmt="%H:%M:%S"))

    parser = argparse.ArgumentParser(description='This is for path obfuscation.')
    parser.add_argument("-p", action="store", default=0, type=int, help="print wire details")
    parser.add_argument("-b", action="store", required=True, type=str, help="original benchmark path")
    parser.add_argument("-k", action="store", default=1, type=int, help="number of key inputs")
    args = parser.parse_args()

    if args.p == 0:
        logging.getLogger().setLevel(level=logging.WARNING)
    elif args.p == 1:
        logging.getLogger().setLevel(level=logging.INFO)
    elif args.p == 2:
        logging.getLogger().setLevel(level=logging.DEBUG)

    # read the bench file. the netlist and its connections are in the wires object.
    # You can find circuit and wires class variables on top of the circuit.py
    # for example, output of a gate is in wires[i].name and its inputs are in wires[i].operands[j].
    target_circuit, wires = circuit.read_bench(args)
    sa(args, target_circuit, wires)
    exit()
