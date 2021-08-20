import my_functions as my
from os import getenv
from dotenv import load_dotenv
from re import findall
from time import sleep

# ----------------------------------------------------------------
# SETUP

load_dotenv()

sf_location = getenv('ENGINE_FILE')
variants_file = getenv('VARIANTS_FILE')
threads = getenv('THREADS')
hash_size = getenv('HASH')

variant = input("Enter the variant (or leave blank): ")
analysis_time = float(input("Enter the number of seconds to analyze: "))
opening_book = input("Enter the opening book file: ")
write_to = input("Enter file name to write game records to (or leave blank): ")

with open(opening_book) as f:
    opening_fens = [i.rstrip('\n') for i in f.readlines()]

# ----------------------------------------------------------------
# ENGINE

engine = my.engine(sf_location)

my.put(engine, "uci")
my.put(engine, "setoption name UCI_Chess960 value true")
my.put(engine, f"setoption name Threads value {threads}")
my.put(engine, f"setoption name Hash value {hash_size}")
my.put(engine, f"load {variants_file}")
if variant: my.put(engine, "setoption name UCI_Variant value " + variant)

# ----------------------------------------------------------------
# ANALYSIS

eval_list = []
bestmove_list = []

for i in range(len(opening_fens)):
    my.put(engine, f"position fen '{opening_fens[i]}'")
    my.put(engine, f"go movetime {analysis_time * 1000}")

    sleep(analysis_time)

    std_output = my.get(engine)
    
    # Validate move: continuously gets output until satisfied
    while True:
        try:
            if not findall('bestmove .{4,5}', std_output[-1]):
                raise RuntimeError
            if not findall("score (cp|mate) [-]?\d+", std_output[-2]):
                raise RuntimeError
            break
        except:
            std_output += my.get(engine)

    # Parse engine output
    bestmove = std_output[-1].split()[1]
    engine_eval = std_output[-2].split()[8:10]

    eval_list += [engine_eval]
    bestmove_list += [bestmove]

    print("Analyzed Position", i+1)

    # Write to file
    if write_to:
        with open(write_to, "a") as f:
            f.write(f"Position {i+1}: {' '.join(engine_eval)} ({bestmove})\n")            

my.put(engine, "quit")

for i in range(len(opening_fens)):
    print(f"Position {i+1}: {' '.join(eval_list[i])} ({bestmove_list[i]})")

input("\nPress enter to exit. ")
