import sys, json, subprocess
D="/home/claude/v14f"
FIG={"type":"poly","pts":json.load(open(f"{D}/fig_poly.json"))}
SH={"type":"poly","pts":json.load(open(f"{D}/shadow_poly.json"))}
def act(felt, do):
    s=json.dumps({"felt":dict(zip(("arousal","tension","valence","care"),felt)),"do":do}).replace('"FIG"',json.dumps(FIG)).replace('"SH"',json.dumps(SH))
    r=subprocess.run(["python3",f"{D}/studio.py","act",s],capture_output=True,text=True)
    if r.returncode: print(r.stderr[-1500:]); sys.exit(1)
def look(*a):
    subprocess.run(["python3",f"{D}/studio.py","look",*map(str,a)],check=True,capture_output=True)
def journal(line):
    open(f"{D}/journal.md","a").write(line+"\n")
