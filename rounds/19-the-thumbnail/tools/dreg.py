import json
X,Y,N=560,2380,2
r=json.load(open('/home/claude/teodor-work/19/plan/m/regions.json'))
def tf(pts): return [[round((x-X+0.5)*N-0.5,1),round((y-Y+0.5)*N-0.5,1)] for x,y in pts]
face={'type':'poly','pts':tf(r['face_work'])}
json.dump(face,open('/home/claude/teodor-work/19/p3/d_face.json','w'))
