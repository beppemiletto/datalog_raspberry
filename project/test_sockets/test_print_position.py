import sys ,os

def print_xy(x,y,contents=None,color=None):
    sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (x, y, contents))
    sys.stdout.flush()


# _=os.system("clear")
sys.stdout.write("\x1b2J")      # clear Screen
sys.stdout.flush()

print("\n"*60)
for x in range(2,31,2):
    for y in [1,31,61]:
        stringa = "x={} y={}".format(x,y)
        print_xy(x,y,contents=stringa)

for x in range(2,31,2):
    for y in [1,31,61]:
        stringa = "Dato {},{}".format(x,y+10)
        print_xy(x,y+10,contents=stringa)


