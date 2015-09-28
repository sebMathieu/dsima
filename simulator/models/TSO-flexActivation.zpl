# Parameters
param T := read "tso.dat" as "1n" use 1 comment "#";
set Ts := {1..T};

param E[Ts] := read "tso.dat" as "<1n> 4n" skip 1 use T comment "#";

param EPS := read "prices.csv" as "2n" use 1 comment "#";
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
var IP[Ts] >=0;
var IM[Ts] >=0;

var x[<j,t> in Fs*Ts] >= mF[j,t] <= MF[j,t];
var xU[<j,t> in Fs*Ts] >= 0;
var xL[<j,t> in Fs*Ts] >= 0;
var v[<j> in Bs] >= w[j] <= W[j];

# Objective
minimize costs:
	sum <j> in Fs : piAF[j]*(sum <t> in Ts : (xU[j,t] + xL[j,t]))
	+ sum <j> in Bs : piAB[j]*v[j]
	+ sum <t> in Ts : (piIP[t]*IP[t]+piIM[t]*IM[t])
	;
					
# Constraints
subto FlexActivation:
	forall <t> in Ts :
		0 == E[t] + IP[t] - IM[t]
		+ sum <j> in Fs : x[j,t]
		+ sum <j> in Bs : if (tauB[j] == t) then v[j] else 0*v[j] end;
		
subto FlexSignF:
	forall <j,t> in Fs*Ts:
		x[j,t] == xU[j,t] - xL[j,t];
		
subto ConstantEnergy:
	forall <j> in Fs:
		sum <t> in Ts : x[j,t] == 0;	
		