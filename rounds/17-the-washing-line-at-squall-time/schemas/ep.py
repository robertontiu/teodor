import json,sys
sys.path.insert(0,'/home/claude/teodor-work/17/schema'); import regions, numpy as np
M=dict(np.load('/home/claude/teodor-work/17/schema/masks.npz'))
def P(n,r=None,k=None):
    ps=[{"type":"poly","pts":p} for p in regions.polys(M[n],r)]
    return ps if k is None else ps[:k]
def save(path,felt,do): json.dump({"felt":felt,"do":do},open(path,'w'))
