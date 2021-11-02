import subprocess

def engine(sf_location):
    engine = subprocess.Popen(
        sf_location,
        universal_newlines=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        bufsize=1,
    )
    return engine

def put(engine, command):
    #print("INPUT:", command)
    engine.stdin.write(command + "\n")

def get(engine):
    engine.stdin.write("isready\n")
    output = []
    while True:
        text = engine.stdout.readline().strip()
        if text == "readyok":
            break
        if text != "":
            output += [text]
    return output

def flatten(some_list):
    output = []
    for item in some_list:
        if isinstance(item, list): 
            output += flatten(item)
        else: 
            output += [item]
    return output
