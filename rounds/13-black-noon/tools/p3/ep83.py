import sys; sys.path.insert(0,'/home/claude/v13/tools')
from run import act
act({"arousal":0.3,"tension":0.15,"valence":-0.4,"care":0.85},[
 {"type":"glaze","color":"#141a30","opacity":0.4,"region":{"type":"poly","pts":[[1085,300],[1200,230],[1200,620],[1120,520],[1090,450]]},"feather":20},
 {"type":"glaze","color":"#f2f2ea","opacity":0.4,"region":{"type":"poly","pts":[[0,300],[60,280],[120,320],[110,390],[0,410]]},"feather":25},
 {"type":"glaze","color":"#f2f2ea","opacity":0.35,"region":{"type":"poly","pts":[[850,430],[905,450],[940,500],[900,530],[845,490]]},"feather":20},
 {"type":"glaze","color":"#eeeee6","opacity":0.3,"region":{"type":"poly","pts":[[690,60],[770,40],[790,120],[760,200],[700,180]]},"feather":20},
])
