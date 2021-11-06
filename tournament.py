# Engine 1v1 tournament script

import os
from re import findall
from dotenv import load_dotenv
from time import time
from random import randint, choices

import my_functions as my

load_dotenv()

# ----------------------------------------------------------------
# SETTINGS

selfplay = input("Do selfplay? (Y/N) ").lower() == "y"
variant = input("Enter the variant (or leave blank): ")
n_games = int(input("Enter the number of games to play: "))

movetime = None
if input("Use fixed time per move? (Y/N) ").lower() == "y":   
    movetime = float(input("How much time per move (s)? "))
else:  
    clock = float(input("How much time to begin (s)? "))
    inc = float(input("How much increment (s)? "))

opening_book = input("Enter file name of opening book (or leave blank): ")

do_random = True
if opening_book:
    do_random = input("Choose openings randomly? (Y/N) ").lower() == "y"
else:
    custom_fen = input("Enter custom FEN (or leave blank): ")

if not do_random:
    opening_repeats = int(input("Enter the number of times to repeat each opening: "))

alternate = False
if not selfplay:
    alternate = input("Alternate black and white engines? (Y/N) ").lower() == "y"

    invert_order = False
    if not alternate:
        invert_order = input("Have the second engine play white? (Y/N) ").lower() == "y"

write_to = input("Enter file name to write game records to (or leave blank): ")

# Draw adjudication
# If d_moves in a row have been at most d_cp cp away from perfect balance (0 cp), the game is ended if after move d_move_number
# This should never be disabled, otherwise games may last forever

print("\nDraw Adjudication")

try:
    longest_game = int(input("Automatically draw games after a certain amount of moves (or leave blank): "))
except:
    longest_game = 999999
    
try:
    d_move_number = int(input("Minimum game moves for draw adjudication (or leave blank): "))
except:
    d_move_number = 0
    
d_cp = int(input("Draw cp: "))
d_moves = int(input("Number of moves below draw cp (at least 3): "))

# Resign adjudication
# If resign is set to True:
#   If the losing side sees a mating line, it will resign
#   If the losing side evaluates its position as worse than r_cp cp, it will resign

print("\nResign Adjudication")

resign = input("Resign if a mating line has been found? (Y/N) ").lower() == "y"
if resign:
    try:
        r_cp = int(input("Resign if eval drop below a certain value (or leave blank): "))
    except:
        r_cp = -999999

# ----------------------------------------------------------------
# SETUP

sf_location = os.getenv('ENGINE_FILE')
sf_location2 = os.getenv('ENGINE_FILE2')
variants_file = os.getenv('VARIANTS_FILE')
threads = os.getenv('THREADS')

if selfplay:
    engines = [my.engine(sf_location)]
    engine_names = {engines[0]: os.path.basename(sf_location)}
else:
    engines = [my.engine(sf_location), my.engine(sf_location2)]
    engine_names = {engines[0]: os.path.basename(sf_location), engines[1]: os.path.basename(sf_location2)}
    winners = {engines[0]: 0, engines[1]: 0}

# Hash is divided between engines
hash_size = int(os.getenv('HASH'))//len(engines)

opening_fens = [None]
if opening_book:
    with open(opening_book) as f:
        opening_fens = [i.rstrip('\n') for i in f.readlines()]

result_count = {"White": 0, "Black": 0, "Draw": 0}
codes = {"White": "1-0", "Black": "0-1", "Draw": "1/2-1/2"}

# ----------------------------------------------------------------
# ENGINE START

for e in engines:
    my.put(e, "uci")
    my.put(e, "setoption name UCI_Chess960 value true")
    my.put(e, f"setoption name Threads value {threads}")
    my.put(e, f"setoption name Hash value {hash_size}")
    my.put(e, f"load {variants_file}")
    if variant: my.put(e, f"setoption name UCI_Variant value {variant}")

print(f"\nCommencing {n_games} game(s) of {variant if variant else 'chess'}.")
print(f"Competing engines: {engine_names[engines[0]]} vs {engine_names[engines[-1]]}")

if movetime:
    print(f"Time control: {movetime} seconds per move.\n")
else:
    print(f"Time control: {clock}+{inc}\n")
    
# ----------------------------------------------------------------
# GENERATE PAIRINGS & OPENINGS

if selfplay:
    pairings = [(engines[0], engines[0])] * n_games
elif alternate:
    pairings = [(engines[i%2], engines[1 - i%2]) for i in range(n_games)]
elif invert_order:
    pairings = [(engines[1], engines[0])] * n_games
else:
    pairings = [(engines[0], engines[1])] * n_games

# Generates a list of indices of opening_fens
if opening_book:
    if do_random:
        opening_list = [randint(0, len(opening_fens)-1) for i in range(n_games)]
    else:
        opening_list = my.flatten([[i % len(opening_fens)] * opening_repeats for i in range(n_games)])[:n_games]

# ----------------------------------------------------------------
# GAME LOOP

for i in range(n_games):
    moves = []
    draw_counting = 0
    
    if not movetime:
        w_clock = clock
        b_clock = clock

    if opening_book:
        custom_fen = opening_fens[opening_list[i]]

    if custom_fen:
        if custom_fen.split()[-5] == "b":
            white_to_move = False
        else:
            white_to_move = True
    else:
        white_to_move = True  

    # Checks that both engines are ready
    for e in engines:
        my.get(e)

    # MOVE LOOP
    while True:
        player = pairings[i][not white_to_move]
        my.get(player)
        
        if custom_fen:
            my.put(player, f"position fen {custom_fen} moves {' '.join(moves)}")
        else:
            my.put(player, f"position startpos moves {' '.join(moves)}")
        
        if movetime:
            my.put(player, f"go movetime {movetime*1000}")
        else:
            my.put(player, f"go wtime {w_clock*1000} btime {b_clock*1000} winc {inc*1000} binc {inc*1000}")

        start = time()

        # Parse engine output
        std_output = []
        while True:
            if std_output:                    
                bestmove_found = findall('bestmove .+', std_output[-1])
                if bestmove_found: 
                    bestmove = bestmove_found[0].split()[1]
                    engine_eval = findall("(?:cp|mate) [-]?\d+", ''.join(std_output))[-1].split() # Find the last occurrence
                    break
            std_output += my.get(player)
        
        # Clock
        timeused = time() - start
        if not movetime:
            if white_to_move:
                w_clock -= timeused
                w_clock += inc
            else:
                b_clock -= timeused
                b_clock += inc           

        # If side to move runs out of time
        if not movetime:
            if white_to_move:
                if w_clock <= 0:
                    print("White lost on time!")
                    result = "Win"
                    break
            else:
                if b_clock <= 0:
                    print("Black lost on time!")
                    result = "Win"
                    break

        # If game is over (checkmate/stalemate)
        if std_output[0] == "info depth 0 score mate 0": # hack
            result = "Win"
            break
        
        if bestmove == "(none)":
            if engine_eval[0] == "mate":
                result = "Win"
            else:
                result = "Draw"
            break
            
        # Resign adjudication
        if resign:
            if engine_eval[0] == "mate" and int(engine_eval[1]) < 0:
                print(f"{['Black', 'White'][white_to_move]} resigned! (mating line found)")
                result = "Win"
                break
            elif engine_eval[0] == "cp" and int(engine_eval[1]) < r_cp:
                print(f"{['Black', 'White'][white_to_move]} resigned! (Eval exceeded threshold)")
                result = "Win"
                break
            
        # Draw adjudication
        if longest_game:
            if len(moves) >= longest_game:
                result = "Draw"
                break
            
        if engine_eval[0] == "cp" and abs(int(engine_eval[1])) <= d_cp:
            draw_counting += 1
        else:
            draw_counting = 0
            
        if len(moves) >= d_move_number and draw_counting >= d_moves:
            result = "Draw"
            break
        
        # Engine makes a move
        print(f"{['BLACK', 'WHITE'][white_to_move]} made move: {bestmove} after {round(timeused, 4)} seconds.")
        print(f"ENGINE EVAL: {' '.join(engine_eval)}")
        if not movetime:
            print(f"TIME (s): {round(w_clock, 4)} - {round(b_clock, 4)}")
        print("")
        
        moves += [bestmove]
        white_to_move = not white_to_move
        
    print(f"\nGame #{i+1} completed.")

    # Game result recorded
    if result == "Win":
        # The last side to move either resigned or was checkmated, thus the other side wins
        result = ['White', 'Black'][white_to_move]

        if selfplay:
            print(f"{result} wins\n")
        else:
            winning_engine = pairings[i][white_to_move]
            winners[winning_engine] += 1
            print(f"{engine_names[winning_engine]} ({result}) wins\n")
    else:
        print("Draw\n")
        
    result_count[result] += 1

    # Generate game record
    game_record = ""
    if opening_book:
        game_record = f"[Position {opening_list[i]+1}] "
    game_record += f"{' '.join(moves)} {codes[result]}\n"
    
    print(f"Game recorded: {game_record}\n")

    # Write to file
    if write_to:
        with open(write_to, "a") as f:
            f.write(f"Game {i+1} ({engine_names[pairings[i][0]]}-{engine_names[pairings[i][1]]}): ")
            f.write(game_record)

# ----------------------------------------------------------------
# QUIT

for e in engines:
    my.put(e, "quit")
print(f"White wins: {result_count['White']} \nBlack wins: {result_count['Black']} \nDraws: {result_count['Draw']}")
if not selfplay:
    print(f"{engine_names[engines[0]]} wins: {winners[engines[0]]} \n{engine_names[engines[1]]} wins: {winners[engines[1]]}\n")
print(f"{n_games} game(s) completed.\n")

input("Press enter to exit. ")
