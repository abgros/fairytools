# perft counter
# Note: doesn't work with an opening book

from os import getenv
from re import findall
from dotenv import load_dotenv
from statistics import mean

import my_functions as my

load_dotenv()

sf_location = getenv('ENGINE_FILE')
variants_file = getenv('VARIANTS_FILE')

variant = input("Enter the variant (or leave blank): ")
custom_fen = input("Enter custom FEN (or leave blank): ")
games_file = input("Enter the file to read from: ")

with open(games_file) as f:
    games_list = [i.rstrip('\n') for i in f.readlines()]
    n_games = len(games_list)

engine = my.engine(sf_location)

my.put(engine, "uci")
my.put(engine, "setoption name UCI_Chess960 value true")
my.put(engine, f"load {variants_file}")
if variant: my.put(engine, "setoption name UCI_Variant value " + variant)

perft_dict = {}

for i in range(len(games_list)):
    game_moves = games_list[i].split()[3:-1]
    
    for j in range(len(game_moves)):
        if custom_fen:
            my.put(engine, f"position fen '{custom_fen}' moves {' '.join(game_moves[:j])}")            
        else:
            my.put(engine, f"position startpos moves {' '.join(game_moves[:j])}")

        my.put(engine, "go perft 1")
        std_output = my.get(engine)
        while True:
            try:
                if findall("Nodes searched: \d+", std_output[-1]):
                    perft_dict[j] = perft_dict.get(j, []) + [int(std_output[-1].split()[-1])]
                    break
                raise RuntimeError
            except:   
                std_output += my.get(engine)

    print(f"Game {i+1} processed.")

my.put(engine, "quit")

for key in perft_dict.keys():
    print(f"Ply {key+1}: {mean(perft_dict[key])}")

input("\nPress enter to exit.")
