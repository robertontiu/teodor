# Face planes in head-local coords (translate(375,895) rotate(16)); light from upper left.
import json, sys
sys.path.insert(0, '/home/claude/teodor-work/16/tools')
from face import strokes
lit_fore = [
 ([(-85,-80),(-40,-92),(10,-92),(55,-80)], 26, "#f7cdb0", .8),
 ([(-90,-58),(-45,-66),(0,-66),(45,-58)], 24, "#f4c2a4", .8),
 ([(-70,-100),(-20,-112),(30,-108)], 18, "#fad8c0", .7),
 ([(55,-80),(85,-62),(98,-35)], 18, "#c98a90", .7),   # forehead turning into shadow
]
cheeks = [
 ([(-95,0),(-75,15),(-52,20),(-30,14)], 30, "#f4b494", .85),   # left cheek mound, lit
 ([(-88,-6),(-64,4),(-44,6)], 14, "#fcd4b8", .75),             # its top light
 ([(-100,30),(-90,55),(-70,75)], 22, "#e49880", .8),           # left jaw turning
 ([(30,14),(55,20),(80,14),(100,0)], 28, "#c97a86", .85),      # right cheek in half shadow
 ([(40,4),(62,6),(80,0)], 12, "#e0a094", .7),                  # its top catching light
 ([(100,25),(96,55),(80,82)], 22, "#9a6a96", .8),              # right jaw, cold violet shadow
 ([(-60,-22),(-30,-18),(-12,-20)], 12, "#f6c6a6", .7),         # under-eye mound L
 ([(18,-18),(40,-16),(64,-20)], 12, "#d8988e", .7),            # under-eye mound R
]
brow = [
 ([(-90,-44),(-60,-50),(-25,-44)], 16, "#f2bfa0", .8),
 ([(20,-42),(52,-48),(85,-40)], 16, "#d49496", .8),
 ([(-18,-40),(-6,-30),(6,-30),(18,-40)], 12, "#f0bc9e", .7),   # glabella
]
nose = [
 ([(-4,-20),(-2,5),(1,30)], 14, "#f6c8aa", .8),
 ([(10,-15),(14,10),(18,36)], 10, "#c07a84", .7),              # shadow side of nose
 ([(-6,36),(3,44),(14,42)], 13, "#f2b49a", .8),                # tip
]
chin = [
 ([(-40,125),(-10,135),(25,132)], 20, "#e6a08a", .8),
 ([(25,130),(50,118),(70,100)], 18, "#9e6c90", .8),
 ([(-70,95),(-60,115),(-40,128)], 16, "#e09482", .75),
]
ep = {"felt":{"arousal":0.3,"tension":0.25,"valence":0.6,"care":0.95},
 "do":[
  {"type":"strokes","brush":"filbert","strokes":strokes(lit_fore+brow),"fat":0.9,"impasto":0.75,"wetmix":0.25,"cover":0.97},
  {"type":"strokes","brush":"filbert","strokes":strokes(cheeks),"fat":0.9,"impasto":0.7,"wetmix":0.25,"cover":0.97},
  {"type":"strokes","brush":"filbert","strokes":strokes(nose+chin),"fat":0.9,"impasto":0.7,"wetmix":0.25,"cover":0.97},
 ]}
json.dump(ep, open('/home/claude/teodor-work/16/ep_56.json','w'))
