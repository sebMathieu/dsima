# Parameters
param N := read "network.csv" as "1n" use 1 comment "#";
set Ns := {0..N-1};
set N0 := {1..N-1};
param L := read "network.csv" as "2n" use 1 comment "#";
set Ls := {1..L};
param piTp := read "network.csv" as "3n" use 1 comment "#";
param piTd := read "network.csv" as "4n" use 1 comment "#";

param fromBus[Ls] := read "network.csv" as "<1n> 2n" skip 1 use L comment "#";
param toBus[Ls] := read "network.csv" as "<1n> 3n" skip 1 use L comment "#";
param C[Ls] := read "network.csv" as "<1n> 6n" skip 1 use L comment "#";

param T := read "baselines-full.dat" as "2n" use 1 comment "#";
set Ts := {1..T};
param gamma := read "baselines-full.dat" as "3n" use 1 comment "#";
param dt := read "baselines-full.dat" as "4n" use 1 comment "#";
param p[Ns*Ts] := read "baselines-full.dat" as "<1n,2n> 3n" skip 1 use (N*T) comment "#";

param piIP[Ts] := read "prices.csv" as "<1n> 3n" skip 1 use T comment "#";
param piIM[Ts] := read "prices.csv" as "<1n> 4n" skip 1 use T comment "#";

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
var f[<line,t> in Ls*Ts] >= -C[line] <= C[line];
var z[Ns*Ts] binary;
var I[Ts] >= -infinity;
var IP[Ts] >=0;
var IM[Ts] >=0;
 
var r[Ns*Ts] >= -infinity;
var x[<j,t> in Fs*Ts] >= mF[j,t] <= MF[j,t];
var xU[<j,t> in Fs*Ts] >= 0;
var xL[<j,t> in Fs*Ts] >= 0;
var v[<j> in Bs] >= w[j] <= W[j];

var trippingCost[Ns*Ts] >= 0;

# Objective
minimize Costs: 
	sum <j> in Fs : piAF[j]*(sum <t> in Ts : (xU[j,t] + xL[j,t]))
	+ sum <j> in Bs : piAB[j]*v[j]
	+ sum <n,t> in Ns*Ts : trippingCost[n,t]
	+ sum <t> in Ts : (gamma*piIP[t]*IP[t]+gamma*piIM[t]*IM[t])
	;

# Constraints
subto TrippingCostProductionDefinition:
	forall <n,t> in Ns*Ts :
		trippingCost[n,t]>=z[n,t]*piTp*dt*p[n,t];

subto TrippingCostConsumptionDefinition:
	forall <n,t> in Ns*Ts :
		trippingCost[n,t]>=z[n,t]*piTd*dt*(-p[n,t]);

subto FlexActivation:
	forall <n,t> in N0*Ts :
		r[n,t] == 
		+ sum <j> in Fs : if (nodeF[j] == n) then x[j,t] else 0*x[j,t] end
		+ sum <j> in Bs : if (nodeB[j] == n and tauB[j] == t) then v[j] else 0*v[j] end;

subto totalImbalance:
	forall <t> in Ts :
		I[t] == IP[t] - IM[t];

subto Imbalance:
	forall <t> in Ts :
		IP[t] - IM[t] == sum <n> in N0: r[n,t];
		
subto RealProductionNode:
	forall <n,t> in Ns*Ts :
		r[n,t] + (1-z[n,t])*p[n,t]
		== sum <line> in Ls : if (fromBus[line] == n) then f[line,t] else 0*f[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then f[line,t] else 0*f[line,t] end;
		
subto TrippingMinFlexibilityC:
	forall <j> in Bs:
		w[j]*(1-z[nodeB[j],tauB[j]]) <= v[j];
		
subto TrippingMaxFlexibilityC:
	forall <j> in Bs:
		v[j] <= W[j]*(1-z[nodeB[j],tauB[j]]);
		
subto TrippingMinFlexibilityF:
	forall <j,t> in Fs*Ts:
		mF[j,t]*(1-z[nodeF[j],t]) <= x[j,t];
		
subto TrippingMaxFlexibilityF:
	forall <j,t> in Fs*Ts:
		x[j,t] <= MF[j,t]*(1-z[nodeF[j],t]);

subto FlexSignF:
	forall <j,t> in Fs*Ts:
		x[j,t] == xU[j,t] - xL[j,t];
		
subto ConstantEnergy:
	forall <j> in Fs:
		sum <t> in Ts : x[j,t] == 0;				
		