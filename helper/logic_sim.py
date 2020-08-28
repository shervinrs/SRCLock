import logging


def bit_not(n):
    return (1 << 1) - 1 - n


def simulation(circuit, input, keyinput):
    wires = circuit.wires
    for w in wires:
        w.logic_value = -1

    i = 0
    k = 0
    for w in wires:
        if w.type == "inp":
            if "keyinput" in w.name:
                w.logic_value = keyinput[k]
                k += 1
            else:
                w.logic_value = input[i]
                i += 1

    for l in range(circuit.max_level+1):
        for w in wires:
            if w.logic_level == l:
                # for k in w.operands:
                #     if k.logic_value == -1:
                #         logging.critical("Error in simulation!")
                #         logging.critical("Error in input value of " + w.name + ", wrong input: " + k.name)
                #         exit()

                if w.type == "inp":
                    continue
                elif w.type == "not":
                    w.logic_value = bit_not(w.operands[0].logic_value)
                elif (w.type == "buff") or (w.type == "buf"):
                    w.logic_value = w.operands[0].logic_value
                elif w.type == "nand":
                    w.logic_value = 1
                    for k in w.operands:
                        w.logic_value &= k.logic_value
                    w.logic_value = bit_not(w.logic_value)
                elif w.type == "and":
                    w.logic_value = 1
                    for k in w.operands:
                        w.logic_value &= k.logic_value
                elif w.type == "or":
                    w.logic_value = 0
                    for k in w.operands:
                        w.logic_value |= k.logic_value
                elif w.type == "nor":
                    w.logic_value = 0
                    for k in w.operands:
                        w.logic_value |= k.logic_value
                    w.logic_value = bit_not(w.logic_value)
                elif w.type == "xor":
                    w.logic_value = 0
                    for k in w.operands:
                        w.logic_value ^= k.logic_value
                elif w.type == "xnor":
                    w.logic_value = 0
                    for k in w.operands:
                        w.logic_value ^= k.logic_value
                    w.logic_value = bit_not(w.logic_value)
                else:
                    logging.critical("Error in simulation!")
                    logging.critical("Error in type of " + w.name)
                    exit()

    output = []
    for w in circuit.output_wires:
        if w.logic_value == -1:
            logging.critical("Error in simulation!")
            logging.critical("Error in output of " + w.name)
            exit()
        output.append(w.logic_value)

    return output


def simulation2(circuit, input, keyinput):
    wires = circuit.wires
    for w in wires:
        w.logic_value = -1

    i = 0
    k = 0
    for w in wires:
        if w.type == "inp":
            if "keyinput" in w.name:
                w.logic_value = keyinput[k]
                k += 1
            else:
                w.logic_value = input[i]
                i += 1

    for w in wires:
        if w.type == "inp":
            continue
        elif w.type == "not":
            w.logic_value = bit_not(w.operands[0].logic_value)
        elif (w.type == "buff") or (w.type == "buf"):
            w.logic_value = w.operands[0].logic_value
        elif w.type == "nand":
            w.logic_value = 1
            for k in w.operands:
                w.logic_value &= k.logic_value
            w.logic_value = bit_not(w.logic_value)
        elif w.type == "and":
            w.logic_value = 1
            for k in w.operands:
                w.logic_value &= k.logic_value
        elif w.type == "or":
            w.logic_value = 0
            for k in w.operands:
                w.logic_value |= k.logic_value
        elif w.type == "nor":
            w.logic_value = 0
            for k in w.operands:
                w.logic_value |= k.logic_value
            w.logic_value = bit_not(w.logic_value)
        elif w.type == "xor":
            w.logic_value = 0
            for k in w.operands:
                w.logic_value ^= k.logic_value
        elif w.type == "xnor":
            w.logic_value = 0
            for k in w.operands:
                w.logic_value ^= k.logic_value
            w.logic_value = bit_not(w.logic_value)
        else:
            logging.critical("Error in simulation!")
            logging.critical("Error in type of " + w.name)
            exit()

    output = []
    for w in circuit.output_wires:
        if w.logic_value == -1:
            logging.critical("Error in simulation!")
            logging.critical("Error in output of " + w.name)
            exit()
        output.append(w.logic_value)

    return output