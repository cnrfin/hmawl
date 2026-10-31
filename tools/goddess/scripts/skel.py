import numpy as np
def qmat(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def world(nodes):
    Rs=[];Ts=[]
    for n in nodes:
        R=qmat(n['Q'])*np.array(n['S']); t=np.array(n['T'])
        if n['parent']>=0:
            pr,pt=Rs[n['parent']],Ts[n['parent']]; R=pr@R; t=pr@t+pt
        Rs.append(R);Ts.append(t)
    return np.array(Ts),Rs
