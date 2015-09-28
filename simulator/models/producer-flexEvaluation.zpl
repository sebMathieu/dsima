# Parameters
param T := read "producer.dat" as "1n" use 1 comment "#";
set Ts := {1..T};

set Ns := {read "producer.dat" as "<n+>" skip 1 use 1 comment "#"};
param N := card(Ns);

param pMin[Ns*Ts] := read "producer.dat" as "<1n,2n> 3n" skip 2 use (N*T) comment "#";
param pMax[Ns*Ts] := read "producer.dat" as "<1n,2n> 4n" skip 2 use (N*T) comment "#";
param c[Ns*Ts] := read "producer.dat" as "<1n,2n> 5n" skip 2 use (N*T) comment "#";

param EPS := read "prices.csv" as "2n" use 1 comment "#";
param pii := read "prices.csv" as "3n" use 1 comment "#";
param piE[Ts] := read "prices.csv" as "<1n> 2n" skip 1 use T comment "#";
param piIP[Ts] := read "prices.csv" as "<1n> 3n" skip 1 use T comment "#";
param piIM[Ts] := read "prices.csv" as "<1n> 4n" skip 1 use T comment "#";

param Pb[Ts] := read "producer-baselines.dat" as "<1n> 2n" skip 2 use T comment "#";
param pb[Ns*Ts] := read "producer-baselines.dat" as "<1n,2n> 3n" skip (2+T) use (N*T) comment "#";
param fP[Ns*Ts] := read "flexBids.dat" as "<1n,2n> 3n" skip 2 use (N*T) comment "#";
param fM[Ns*Ts] := read "flexBids.dat" as "<1n,2n> 4n" skip 2 use (N*T) comment "#";
param d[Ns*Ts] := read "flexBids.dat" as "<1n,2n> 5n" skip 2 use (N*T) comment "#";
param D[Ns*Ts] := read "flexBids.dat" as "<1n,2n> 6n" skip 2 use (N*T) comment "#";

param k[Ns] := read "flexBids.dat" as "<1n> 2n" skip 2+N*T use N comment "#";
param K[Ns] := read "flexBids.dat" as "<1n> 3n" skip 2+N*T use N comment "#";

param F := read "ecBids.dat" as "1n" use 1 comment "#";
set Fs := {0..F-1};
param nodeF[Fs] := read "ecBids.dat" as "<1n> 2n" skip 1 use F comment "#";
param piRF[Fs] := read "ecBids.dat" as "<1n> 3n" skip 1 use F comment "#";
param piAF[Fs] := read "ecBids.dat" as "<1n> 4n" skip 1 use F comment "#";
param mF[Fs*Ts] := read "ecBids.dat" as "<1n,2n> 3n" skip (1+F) use (F*T) comment "#";
param MF[Fs*Ts] := read "ecBids.dat" as "<1n,2n> 4n" skip (1+F) use (F*T) comment "#";

param B := read "spBids.dat" as "1n" use 1 comment "#";
set Bs := {0..B-1};
param nodeB[Bs] := read "spBids.dat" as "<1n> 2n" skip 1 use B comment "#";
param tauB[Bs] := read "spBids.dat" as "<1n> 3n" skip 1 use B comment "#";
param piRB[Bs] := read "spBids.dat" as "<1n> 4n" skip 1 use B comment "#";
param piAB[Bs] := read "spBids.dat" as "<1n> 5n" skip 1 use B comment "#";
param mB[Bs] := read "spBids.dat" as "<1n> 6n" skip 1 use B comment "#";
param MB[Bs] := read "spBids.dat" as "<1n> 7n" skip 1 use B comment "#";

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
var pP[<n,t> in Ns*Ts] >= max(pMin[n,t],k[n]) <= min(pMax[n,t],K[n]);
var pM[<n,t> in Ns*Ts] >= max(pMin[n,t],k[n]) <= min(pMax[n,t],K[n]);

var u[Ns*Ts] >= -infinity;
var x[<j,t> in Fs*Ts] >= mF[j,t] <= MF[j,t];
var xU[<j,t> in Fs*Ts] >= 0;
var xL[<j,t> in Fs*Ts] >= 0;
var y[Fs] binary;
var z[Ns*Ts] binary;
var v[<j> in Bs] >= mB[j] <= MB[j];
var w[<j> in Bs] >= mB[j] <= 0;
var W[<j> in Bs] >= 0 <= MB[j];
				
# Objective
minimize costs: 
	sum <t> in Ts : (piIP[t]*IP[t]+piIM[t]*IM[t]
					+sum <n> in Ns : ( 
						c[n,t]*p[n,t]
						+ EPS*(iP[n,t]+iM[n,t]) 
						+ pii*(id[n,t]+iD[n,t])
						)
					)
	+ sum <j> in Fs : (piRF[j]*y[j] + piAF[j]*(sum <t> in Ts : (xU[j,t] + xL[j,t])))
	+ sum <j> in Bs : (piAB[j]*v[j] + piRB[j]*(W[j]-w[j]))
	;
					
# Constraints		
subto TotalProduction:
	forall <t> in Ts : 
		P[t] == sum <n> in Ns: p[n,t];
	
subto TotalImbalance:
	forall <t> in Ts :
		I[t] == P[t]-Pb[t];
	
subto TotalUpwardImbalance:
	forall <t> in Ts :
		IP[t] >= I[t];
		
subto TotalDownwardImbalance:
	forall <t> in Ts :
		IM[t] >= -I[t];

subto FlexPdef:
	forall <n,t> in Ns*Ts:
		fP[n,t]<=pP[n,t]-pb[n,t];

subto FlexMdef:
	forall <n,t> in Ns*Ts:
		fM[n,t]<=pb[n,t]-pM[n,t];

subto FlexActivation:
	forall <n,t> in Ns*Ts :
		u[n,t] == 
		+ sum <j> in Fs : if (nodeF[j] == n) then x[j,t] else 0*x[j,t] end
		+ sum <j> in Bs : if (nodeB[j] == n and tauB[j] == t) then v[j] else 0*v[j] end;
		
subto NodeBalance:
	forall <n,t> in Ns*Ts:
		pb[n,t]+i[n,t]+u[n,t]==p[n,t];

subto UpwardNodeImbalance:
	forall <n,t> in Ns*Ts:
		iP[n,t] >= i[n,t];
		
subto DownwardNodeImbalance:
	forall <n,t> in Ns*Ts:
		iM[n,t] >= -i[n,t];
		
subto ModulationMinC:
	forall <j> in Bs:
		w[j] <= v[j];
		
subto ModulationMaxC:
	forall <j> in Bs:
		v[j] <= W[j];
		
subto MinFlexibilityF:
	forall <j,t> in Fs*Ts:
		mF[j,t]*y[j] <= x[j,t];
		
subto MaxFlexibilityF:
	forall <j,t> in Fs*Ts:
		x[j,t] <= MF[j,t]*y[j];

subto FlexSignF:
	forall <j,t> in Fs*Ts:
		x[j,t] == xU[j,t] - xL[j,t];
		
subto ConstantEnergy:
	forall <j> in Fs:
		sum <t> in Ts : x[j,t] == 0;

subto DynamicDownwardRestriction:
	forall <n,t> in Ns*Ts:
		id[n,t] >= d[n,t]-p[n,t];

subto DynamicUpwardRestriction:
	forall <n,t> in Ns*Ts:
		iD[n,t] >= p[n,t]-D[n,t];
