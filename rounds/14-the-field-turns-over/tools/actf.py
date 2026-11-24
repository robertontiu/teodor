# run a studio act from a JSON file (avoids argument length limit)
import sys, runpy
sys.argv=['/home/claude/v14/studio.py','act',open(sys.argv[1]).read()]
sys.path.insert(0,'/home/claude/v14')
runpy.run_path('/home/claude/v14/studio.py',run_name='__main__')
