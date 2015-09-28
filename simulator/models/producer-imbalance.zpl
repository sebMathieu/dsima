# Parameters
param T := read "producer.dat" as "1n" use 1 comment "#";
set Ts := {1..T};

set Ns := {read "producer.dat" as "<n+>" skip 1 use 1 comment "#"};
param N := card(Ns);

param pMin[Ns*Ts] := read "producer.dat" as "<1n,2n> 3n" skip 2 use (N*T) comment "#";
param pMax[Ns*Ts] := read "producer.dat" as "<1n,2n> 4n" skip 2 use (N*T) comment "#";
param c[Ns*Ts] := read "producer.dat" as "<1n,2n> 5n" skip 2 use (N*T) comment "#";
param E[Ts] := read "producer.dat" as "<1n> 2n" skip 2+N*T use T comment "#";

param EPS := read "prices.csv" as "2n" use 1 comment "#";
param pii := read "prices.csv" as "3n" use 1 comment "#";
param piE[Ts] := read "prices.csv" as "<1n> 2n" skip 1 use T comment "#";
param piIP[Ts] := read "prices.csv" as "<1n> 3n" skip 1 use T comment "#";
param piIM[Ts] := read "prices.csv" as "<1n> 4n" skip 1 use T comment "#";

param Pa[Ts] := read "producer-baselines.dat" as "<1n> 2n" skip 2 use T comment "#";
param pa[Ns*Ts] := read "producer-baselines.dat" as "<1n,2n> 3n" skip (2+T) use (N*T) comment "#";

param u[Ns*Ts] := read "activatedFlex.dat" as "<1n,2n> 3n" skip 2 use (N*T) comment "#";
param h[Ns*Ts] := read "flexToActivate.dat" as "<1n,2n> 3n" skip 2 use (N*T) comment "#";
param bsp[Ns*Ts] := read "flexToActivate.dat" as "<1n,2n> 4n" skip 2 use (N*T) comment "#";
param d[Ns*Ts] := read "flexToActivate.dat" as "<1n,2n> 5n" skip 2 use (N*T) comment "#";
param D[Ns*Ts] := read "flexToActivate.dat" as "<1n,2n> 6n" skip 2 use (N*T) comment "#";

param k[Ns] := read "flexToActivate.dat" as "<1n> 2n" skip 2+N*T use N comment "#";
param K[Ns] := read "flexToActivate.dat" as "<1n> 3n" skip 2+N*T use N comment "#";

# Variables
var P[Ts] >= -infinity;
var i[<n,t> in Ns*Ts] >= -infinity;
var iP[<n,t> in Ns*Ts] >= 0;
var iM[<n,t> in Ns*Ts] >= 0;
var I[Ts] >= -infinity;
var IP[Ts] >=0;
var IM[Ts] >=0;
var id[Ns*Ts] >= 0;
var iD[Ns*Ts] >= 0;
var p[<n,t> in Ns*Ts] >= max(pMin[n,t],k[n]) <= min(pMax[n,t],K[n]);

# Objective
maximize profit: 
	sum <t> in Ts : (-piIP[t]*IP[t]-piIM[t]*IM[t]
					+sum <n> in Ns :( - c[n,t]*p[n,t]
									  - ( (EPS*(1-bsp[n,t])+bsp[n,t]*pii)*iP[n,t] + (EPS*(1-bsp[n,t])+bsp[n,t]*pii)*iM[n,t] )
									  - pii*(id[n,t]+iD[n,t])
									)
					);
					
# Constraints		
subto TotalProduction:
	forall <t> in Ts : 
		P[t] == sum <n> in Ns: p[n,t];
	
subto TotalImbalance:
	forall <t> in Ts :
		I[t] == P[t] - (Pa[t] + sum <n> in Ns: (h[n,t]+u[n,t])) + E[t];
	
subto TotalUpwardImbalance:
	forall <t> in Ts :
		IP[t] >= I[t];
		
subto TotalDownwardImbalance:
	forall <t> in Ts :
		IM[t] >= -I[t];
		
subto NodeBalance:
	forall <n,t> in Ns*Ts:
		i[n,t]==p[n,t]-(pa[n,t]+h[n,t]+u[n,t]);

subto UpwardNodeImbalance:
	forall <n,t> in Ns*Ts:
		iP[n,t] >= i[n,t];
		
subto DownwardNodeImbalance:
	forall <n,t> in Ns*Ts:
		iM[n,t] >= -i[n,t];
		
subto DynamicDownwardRestriction:
	forall <n,t> in Ns*Ts:
		id[n,t] >= d[n,t]-p[n,t];

subto DynamicUpwardRestriction:
	forall <n,t> in Ns*Ts:
		iD[n,t] >= p[n,t]-D[n,t];
		