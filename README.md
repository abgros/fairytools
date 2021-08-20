# fairytools
This is a collection of Python scripts to help with computer analysis of chess games and variants.
In particular, it fully supports all variants you can configure with Fairy-Stockfish.

Tested on: Python 3.9.5, Windows 10
Modules used: dotenv, anytree

960.txt - This is an opening book of all Chess960 starting positions.
48000.txt - All "Capa960" (pychess rules) staring positions in alphabetical order.

my_functions.py - Functions that are used in the scripts. It doesn't do anything by itself.

Scripts
note - before running any scripts make sure you take a look at the ".env" file.
note - the scripts can automatically create a new output file, so don't worry about creating one yourself.

auto_analysis.py - Analyzes all positions in an opening book for a specified amount of time.
opening_tree.py - Generates openings for a variant. You can configure the threshold for opening quality.
perft_script.py - Takes in as input in the form of a tournament.py output file. Calculates the average perft (number of legal moves) for each game ply.
tournament.py - This is the most useful script. You can make an engine play itself or compare the strengths of two engines.
