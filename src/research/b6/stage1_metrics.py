"""Shared deterministic aggregation. Invalid opportunities are never zero-R trades."""
import numpy as np
YEARS=(2020,2021,2022,2023)

def metrics(r,valid,years,gate):
    # Rows are chronological Entry dates. A weekly candidate holds <=24h, so
    # its Close order equals Entry order even after SL/fallback (no overlaps).
    r=np.asarray(r,dtype=float);valid=np.asarray(valid,dtype=bool)
    if r.shape!=valid.shape or r.ndim!=2:raise ValueError('metric matrix shape')
    if not np.isfinite(r[valid]).all():raise ValueError('nonfinite actual trade R')
    v=np.where(valid,r,0.0)  # Neutral aggregation only; valid mask controls N.
    n=valid.sum(axis=0);wins=((v>0)&valid).sum(axis=0);loss=((v<0)&valid).sum(axis=0)
    total=v.sum(axis=0);gain=np.maximum(v,0).sum(axis=0);pain=-np.minimum(v,0).sum(axis=0)
    avg=np.divide(total,n,out=np.full_like(total,np.nan),where=n>0)
    pf=np.divide(gain,pain,out=np.full_like(gain,np.nan),where=pain>0)
    pf[(pain==0)&(gain>0)]=np.inf
    if len(v):
        eq=np.cumsum(v,axis=0);peak=np.maximum.accumulate(np.maximum(eq,0),axis=0);dd=(peak-eq).max(axis=0)
    else:dd=np.zeros(r.shape[1])
    result=dict(N=n,Wins=wins,Losses=loss,ZeroTrades=n-wins-loss,PF=pf,AvgR=avg,TotalR=total,MaxDDR=dd,
                WinRate=np.divide(wins,n,out=np.full_like(total,np.nan),where=n>0))
    annual_n=[];annual_r=[]
    for y in YEARS:
        mask=np.asarray(years)==y;nv=valid[mask].sum(axis=0);rv=v[mask].sum(axis=0)
        annual_n.append(nv);annual_r.append(rv)
        vv=v[mask];gp=np.maximum(vv,0).sum(axis=0);lp=-np.minimum(vv,0).sum(axis=0)
        apf=np.divide(gp,lp,out=np.full_like(gp,np.nan),where=lp>0);apf[(lp==0)&(gp>0)]=np.inf
        if len(vv):
            ae=np.cumsum(vv,axis=0);ad=(np.maximum.accumulate(np.maximum(ae,0),axis=0)-ae).max(axis=0)
        else:ad=np.zeros(r.shape[1])
        result.update({f'N_{y}':nv,f'TotalR_{y}':rv,f'AvgR_{y}':np.divide(rv,nv,out=np.full_like(rv,np.nan),where=nv>0),f'PF_{y}':apf,f'MaxDDR_{y}':ad,f'Losses_{y}':((vv<0)&valid[mask]).sum(axis=0)})
    result['Pass']=((n>=gate['min_trades'])&(loss>=gate['min_losses'])&np.isfinite(pf)&(pf>=gate['min_pf'])
                    &(np.asarray(annual_n)>=gate['min_annual_trades']).all(axis=0)
                    &((np.asarray(annual_r)>0).sum(axis=0)>=gate['min_positive_years']))
    return result
