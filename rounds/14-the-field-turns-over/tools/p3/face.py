import numpy as np, json
rng=np.random.default_rng(52)
H=np.array([742.,1085.]); u=np.array([0.39,0.92]); v=np.array([0.92,-0.39])
P=lambda a,b: (H+u*a+v*b).round(1).tolist()
def mix(c1,c2,t):
    a=np.array([int(c1[i:i+2],16) for i in (1,3,5)]);b=np.array([int(c2[i:i+2],16) for i in (1,3,5)])
    c=(a*(1-t)+b*t).astype(int); return '#%02x%02x%02x'%tuple(c)
st=[]
# throat: strokes along the neck axis, light on the sun side (v>0)
for b in np.arange(-34,36,7):
    t=(b+34)/70
    col=mix('#5f86d8','#e9f0ff',t**0.8)
    st.append({"pts":[P(-135,b*0.95),P(-100,b),P(-66,b*0.9)],"size":10,"color":col})
# face plane, foreshortened: strokes across the face
for a in np.arange(-58,-8,6):
    w=np.sqrt(max(0,1-((a+33)/30)**2))*52+8
    t=1-(a+58)/50*0.5
    st.append({"pts":[P(a,-w),P(a,0),P(a,w)],"size":8,"color":mix('#9fc0f0','#f3f6ff',t)})
# brightest notes: chin crescent and cheek plane toward the sun
st.append({"pts":[P(-60,-30),P(-64,-8),P(-63,14),P(-57,34)],"size":5,"color":"#fffbea"})
st.append({"pts":[P(-40,18),P(-30,34),P(-20,42)],"size":6,"color":"#fffdf2"})
st.append({"pts":[P(-48,-4),P(-36,0),P(-24,2)],"size":4,"color":"#ffffff"})
print(json.dumps(st))
