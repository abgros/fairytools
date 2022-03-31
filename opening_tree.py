from re import findall
from os import getenv
from dotenv import load_dotenv
from time import time
from anytree import Node, RenderTree

import my_functions as my

load_dotenv()

variant = input("Enter the variant (or leave blank): ")
custom_fen = input("Enter custom FEN (or leave blank): ")
multi_pv = input("Enter maximum branching factor (or leave blank): ")
analysis_time = float(input("Enter the time (s) to spend analyzing: "))
analysis_depth = int(input("Enter the number of plies to analyze: "))
eval_thres = int(input("Enter the maximum acceptable centipawn loss: "))
write_to = input("Enter file name to write game records to (or leave blank): ")
nnue = input("Enter a NNUE file to use (or leave blank): ")

if write_to:
    write_fen = input("Write results as FEN rather than moves (Y/N): ").lower() == 'y'

if not multi_pv: multi_pv = 500

root = Node("START", cp_loss = 0)

# ----------------------------------------------------------------
# ENGINE

print("\nStarting engine.\n")

sf_location = getenv('ENGINE_FILE')
variants_file = getenv('VARIANTS_FILE')
threads = getenv('THREADS')
hash_size = getenv('HASH')

engine = my.engine(sf_location)

my.put(engine, "uci")
my.put(engine, f"setoption name Threads value {threads}")
my.put(engine, f"setoption name Hash value {hash_size}")
my.put(engine, f"setoption name MultiPv value {multi_pv}")
my.put(engine, f"load {variants_file}")
if variant: my.put(engine, f"setoption name UCI_Variant value {variant}")
if nnue: my.put(engine, f"setoption name EvalFile value {nnue}")

# ----------------------------------------------------------------
# SEARCH LOOP

for i in range(analysis_depth):
    moves_to_analyze = root.leaves
    
    for variation in moves_to_analyze:
        path = findall("'.*'", str(variation))[0][8:-1].replace('/', ' ')

        if custom_fen:
            my.put(engine, f"position fen {custom_fen} moves {path}")
        else:
            my.put(engine, f"position startpos moves {path}")
            
        my.put(engine, f"go movetime {analysis_time*1000}")

        std_output = my.get(engine)

        while True:
            try:
                if not findall('bestmove .{4,5}', std_output[-1]):
                    raise RuntimeError
                if not findall("score (cp|mate) [-]?\d+", std_output[-2]):
                    raise RuntimeError
                break
            except:
                std_output += my.get(engine)

        possible_lines = std_output[-2:-2-int(std_output[-2].split()[6]):-1][::-1]
        
        for line in possible_lines:
            cp_loss = int(possible_lines[0].split()[9]) - int(line.split()[9])
            if cp_loss > eval_thres:
                break
            else:
                variation.children += (Node(line.split()[line.split().index("pv")+1], cp_loss = cp_loss),)
            
        print(f"Analyzed variation: START -> {path} ({len(variation.children)} moves found)")
        
print("\nOpening tree:")
print(RenderTree(root).by_attr())

# Write to file
if write_to:
    for variation in root.leaves:
        output = findall("'.*'", str(variation))[0][8:-1].replace('/', ' ')

        # Convert variations to FENs
        if write_fen:
            if custom_fen:
                my.put(engine, f"position fen {custom_fen} moves {output}")
            else:
                my.put(engine, f"position startpos moves {output}")

            my.put(engine, "d")
            std_output = my.get(engine)
            
            while True:
                try:
                    if std_output[-1].startswith("Checkers:"):
                        break
                except:
                    std_output += my.get(engine)

            output = std_output[-4][5:]
            
        with open(write_to, "a") as f:
            f.write(output + "\n")

my.put(engine, "quit")

input("\nPress enter to quit. ")
