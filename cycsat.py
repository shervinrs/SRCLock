import argparse
import logging
from srclock import circuit
from cycsat import cycsat_attack, cycsat_util

logging.basicConfig(format="%(asctime)s %(levelname)s:: %(message)s", datefmt="%H:%M:%S")
logging.getLogger().handlers[0].setFormatter(logging.Formatter("[%(asctime)s.%(msecs)04d %(funcName)s %(levelname)s] %(message)s", datefmt="%H:%M:%S"))

parser = argparse.ArgumentParser(description='This is for removing cycles from obfuscated circuit.')
parser.add_argument("-p", action="store", default=0, type=int, help="print wire details")
parser.add_argument("-m", action="store_true", default=False, help="using CycSAT-II (considering SR-Latch inputs)")
parser.add_argument("-f", action="store", default=1, type=int, help="select method for finding cycles")
parser.add_argument("-c", action="store_true", default=False, help="only count cycles")
parser.add_argument("-b", action="store", required=True, type=str, help="original benchmark path")
parser.add_argument("-l", action="store", required=False, type=int, help="find cycles with length < l")
args = parser.parse_args()

if args.p == 0:
    logging.getLogger().setLevel(level=logging.WARNING)
elif args.p == 1:
    logging.getLogger().setLevel(level=logging.INFO)
elif args.p == 2:
    logging.getLogger().setLevel(level=logging.DEBUG)

target_circuit, wires = circuit.simple_read_bench(args.b)

# if args.p:
#     for i in range(0, len(wires)):
#         my_util.wire_print(wires[i])

if args.c:
    cycsat_util.cycle_count(args, wires)
    exit()

# test(args, wires)

# find cycles
if args.f == 1:
    cycles = cycsat_util.find_cycles(args, wires)
elif args.f == 2:
    cycles = cycsat_util.find_cycles2(args, wires)
elif args.f == 3:
    if args.l < 1:
        print("Error: cycle length is not defined")
        exit()
    else:
        cycles = cycsat_util.find_cycles3(args, wires)
        # exit()
elif args.f == 4:
    cycsat_attack.cycsat_date18(args.b)
    exit()

# find required terms for cyc_sat
added_lines = cycsat_attack.cyc_sat(args, wires, cycles)

# write new files for original design and obfuscated design
cycsat_attack.write_output(added_lines, args.b)
