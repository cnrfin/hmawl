import numpy as np
def flatten(P, ratio, hc=np.array([0,1.03,-0.03])):
    c=P.mean(0); X=P-c; w,v=np.linalg.eigh(X.T@X/len(X)); a=v[:,2]
    if a@(c-hc)<0: a=-a
    t=(P-c)@a; t0=np.percentile(t,3)            # inner end (against the head) stays put
    return P+np.outer((t-t0)*(ratio-1),a)
