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

param Pa[Ts] := read "producer-baselines.dat" as "<1n> 2n" skip 2 use T comment "#";
param pa[Ns*Ts] := read "producer-baselines.dat" as "<1n,2n> 3n" skip (2+T) use (N*T) comment "#";

param fP[Ns*Ts] := read "flexBids.dat" as "<1n,2n> 3n" skip 2 use (N*T) comment "#";
param fM[Ns*Ts] := read "flexBids.dat" as "<1n,2n> 4n" skip 2 use (N*T) comment "#";
param d[Ns*Ts] := read "flexBids.dat" as "<1n,2n> 5n" skip 2 use (N*T) comment "#";
param D[Ns*Ts] := read "flexBids.dat" as "<1n,2n> 6n" skip 2 use (N*T) comment "#";

param k[Ns] := read "flexBids.dat" as "<1n> 2n" skip 2+N*T use N comment "#";
param K[Ns] := read "flexBids.dat" as "<1n> 3n" skip 2+N*T use N comment "#";

param B := read "acceptedFlex.dat" as "1n" use 1 comment "#";
set Bs := {0..B-1};
param nodeB[Bs] := read "acceptedFlex.dat" as "<1n> 2n" skip 1 use B comment "#";
param tauB[Bs] := read "acceptedFlex.dat" as "<1n> 3n" skip 1 use B comment "#";
param piAB[Bs] := read "acceptedFlex.dat" as "<1n> 5n" skip 1 use B comment "#";
param w[Bs] := read "acceptedFlex.dat" as "<1n> 6n" skip 1 use B comment "#";
param W[Bs] := read "acceptedFlex.dat" as "<1n> 7n" skip 1 use B comment "#";

param F := read "acceptedFlex.dat" as "2n" use 2 comment "#";
set Fs := {0..F-1};
param nodeF[Fs] := read "acceptedFlex.dat" as "<1n> 2n" skip (1+B) use F comment "#";
param piAF[Fs] := read "acceptedFlex.dat" as "<1n> 4n" skip (1+B) use F comment "#";
param mF[Fs*Ts] := read "acceptedFlex.dat" as "<1n,2n> 3n" skip (1+B+F) use (F*T) comment "#";
param MF[Fs*Ts] := read "acceptedFlex.dat" as "<1n,2n> 4n" skip (1+B+F) use (F*T) comment "#";

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

var u[Ns*Ts] >= -infinity;
var x[<j,t> in Fs*Ts] >= mF[j,t] <= MF[j,t];
var xU[<j,t> in Fs*Ts] >= 0;
var xL[<j,t> in Fs*Ts] >= 0;
var v[<j> in Bs] >= w[j] <= W[j];

# Objective
minimize costs: 
	sum <j> in Fs : piAF[j]*(sum <t> in Ts : (xU[j,t] + xL[j,t]))
	+ sum <j> in Bs : piAB[j]*v[j]
	+ sum <t> in Ts : (piIP[t]*IP[t]+piIM[t]*IM[t]
					+sum <n> in Ns : (
						c[n,t]*p[n,t]
						+ EPS*(iP[n,t]+iM[n,t])
						+ pii*(id[n,t]+iD[n,t]) 
						)
					)
	;
					
# Constraints
subto TotalProduction:
	forall <t> in Ts : 
		P[t] == sum <n> in Ns: p[n,t];
		
subto TotalImbalance:
	forall <t> in Ts :
		I[t] == P[t]-Pa[t]-sum<n> in Ns: u[n,t];
	
subto TotalUpwardImbalance:
	forall <t> in Ts :
		IP[t] >= I[t];
		
subto TotalDownwardImbalance:
	forall <t> in Ts :
		IM[t] >= -I[t];
	
subto FlexActivation:
	forall <n,t> in Ns*Ts :
		u[n,t] == 
		+ sum <j> in Fs : if (nodeF[j] == n) then x[j,t] else 0*x[j,t] end
		+ sum <j> in Bs : if (nodeB[j] == n and tauB[j] == t) then v[j] else 0*v[j] end;
		
subto NodeBalance:
	forall <n,t> in Ns*Ts:
		pa[n,t]+i[n,t]+u[n,t]==p[n,t];

subto UpwardNodeImbalance:
	forall <n,t> in Ns*Ts:
		iP[n,t] >= i[n,t];
		
subto DownwardNodeImbalance:
	forall <n,t> in Ns*Ts:
		iM[n,t] >= -i[n,t];
		
subto FlexSignF:
	forall <j,t> in Fs*Ts:
		x[j,t] == xU[j,t] - xL[j,t];
		
subto ConstantEnergy:
	forall <j> in Fs:
		sum <t> in Ts : x[j,t] == 0;	
		