import json, subprocess, sys
sys.path.insert(0,'/home/claude/v13/tools')
SHIM = "import sys,runpy; sys.argv=['/home/claude/v13/studio.py','act',open('/home/claude/v13/tools/last_act.json').read()]; runpy.run_path('/home/claude/v13/studio.py', run_name='__main__')"
def act(felt, do):
    s=json.dumps({"felt":felt,"do":do})
    open('/home/claude/v13/tools/last_act.json','w').write(s)
    r=subprocess.run(['python3','-c',SHIM],capture_output=True,text=True,cwd='/home/claude/v13')
    print(r.stdout[-300:], r.stderr[-1500:])
    subprocess.run(['python3','/home/claude/v13/studio.py','look','full'],cwd='/home/claude/v13')
