from srclock import path_obf, circuit, my_util
import argparse
import logging

logging.basicConfig(format="%(asctime)s %(levelname)s:: %(message)s", datefmt="%H:%M:%S")
logging.getLogger().setLevel(level=logging.INFO)
logging.getLogger().handlers[0].setFormatter(logging.Formatter("%(message)s"))
logging.warning(r'  _____ _____   _____ _                _    ')
logging.warning(r' / ____|  __ \ / ____| |              | |   ')
logging.warning(r'| (___ | |__) | |    | |     ___   ___| | __')
logging.warning(r' \___ \|  _  /| |    | |    / _ \ / __| |/ /')
logging.warning(r' ____) | | \ \| |____| |___| (_) | (__|   < ')
logging.warning(r'|_____/|_|  \_\\_____|______\___/ \___|_|\_\ ')
logging.warning(r'      by Gate Lab, George Mason University')
logging.warning(r'')
logging.getLogger().handlers[0].setFormatter(logging.Formatter("%(asctime)s.%(msecs)04d %(funcName)s %(levelname)s:: %(message)s", datefmt="%H:%M:%S"))

parser = argparse.ArgumentParser(description='This is for path obfuscation.')
parser.add_argument("-p", action="store", default=0, type=int, help="print wire details")
parser.add_argument("-n", action="store", required=True, type=int, help="number of paths/loops for obfuscation")
parser.add_argument("-l", action="store", required=False, type=int, help="length of the loops")
parser.add_argument("-m", action="store", required=True, help="obfuscation method")
parser.add_argument("-b", action="store", required=True, type=str, help="original benchmark path")
parser.add_argument("-d", action="store", default=0, required=False, type=int, help="percentage of delay penalty for ta mode")
parser.add_argument("-a", action="store", default=0, required=False, type=int, help="area constrain")
args = parser.parse_args()

if args.p == 0:
    logging.getLogger().setLevel(level=logging.WARNING)
elif args.p == 1:
    logging.getLogger().setLevel(level=logging.INFO)
elif args.p == 2:
    logging.getLogger().setLevel(level=logging.DEBUG)

if args.m != "date":
    target_circuit, wires = circuit.read_bench(args)
else:
    target_circuit, wires = circuit.simple_read_bench(args.b)

if args.p > 2:
    for i in range(0, len(wires)):
        my_util.wire_print(wires[i])

if args.m == "rnd":
    target_circuit.b2b = False
    path_obf.rnd_marking(args, wires)
elif args.m == "high_skew":
    target_circuit.b2b = False
    path_obf.high_skew_marking(args, wires)
elif args.m == "high_skew_b2b":
    path_obf.high_skew_marking(args, wires)
elif args.m == "cone":
    target_circuit.b2b = True
    path_obf.cone_marking(args, wires)
elif args.m == "hs_rc":
    target_circuit.b2b = True
    if args.l < 1:
        logging.critical("Loop length (-l) is missing!")
        exit()
    path_obf.rand_cycle_highskew(args, target_circuit, wires)
elif args.m == "glsvlsi":
    target_circuit.b2b = True
    if args.l < 1:
        logging.critical("Loop length (-l) is missing!")
        exit()
    path_obf.glsvlsi17(args, target_circuit, wires)
elif args.m == "date":
    target_circuit.b2b = True
    args.l = 4
    path_obf.date18(args, target_circuit, wires)
elif args.m == "ta1" or args.m == "ta2":
    if args.l < 1:
        logging.critical("Loop length (-l) is missing!")
        exit()
    path_obf.timing_aware(args, target_circuit, wires)
elif args.m == "lfn":
    if args.l % 2 != 0:
        logging.critical("Loop length (-l) should be even!")
        exit()
    path_obf.lfn(args, target_circuit, wires)
else:
    logging.critical("Invalid obfuscation method!")
