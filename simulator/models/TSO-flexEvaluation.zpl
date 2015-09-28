# Parameters
param T := read "tso.dat" as "1n" use 1 comment "#";
set Ts := {1..T};
param piSP := read "tso.dat" as "2n" use 1 comment "#";
param piSM := read "tso.dat" as "3n" use 1 comment "#";
param SP[Ts] := read "tso.dat" as "<1n> 2n" skip 1 use T comment "#";
param SM[Ts] := read "tso.dat" as "<1n> 3n" skip 1 use T comment "#";

param EPS := read "prices.csv" as "2n" use 1 comment "#";
param piIP[Ts] := read "prices.csv" as "<1n> 3n" skip 1 use T comment "#";
param piIM[Ts] := read "prices.csv" as "<1n> 4n" skip 1 use T comment "#";

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
var AP[Ts] >=0;
var AM[Ts] >= -infinity <=0;
var WCP[<t> in Ts] >=0 <= SP[t]; # min(SP,AP)
var WCM[<t> in Ts] >= SM[t] <=0; # max(SM,AM)

var x[<j,t> in Fs*Ts] >=0;
var y[Fs] binary;
var v[<j> in Bs] >= 0;
var w[<j> in Bs] >= mB[j] <= 0;
var W[<j> in Bs] >= 0 <= MB[j];
				
# Objective
minimize costs: 
	- sum <t> in Ts : (piSP*WCP[t]+piSM*WCM[t])
	+ sum <j> in Fs : (piRF[j]*y[j] + abs(piAF[j])*(sum <t> in Ts : x[j,t]))
	+ sum <j> in Bs : (abs(piAB[j])*v[j] + piRB[j]*(W[j]-w[j]))
	;
					
# Constraints
subto WelfareContributionP:
	forall <t> in Ts :
		WCP[t] <= AP[t];

subto WelfareContributionM:
	forall <t> in Ts :
		WCM[t] >= AM[t];

subto UpwardFlexNeeds:
	forall <t> in Ts : 
		AP[t] == sum <j> in Bs: if (tauB[j] == t) then W[j] else 0*W[j] end + sum <j> in Fs: MF[j,t]*y[j];
		
subto DownwardFlexNeeds:
	forall <t> in Ts : 
		AM[t] == sum <j> in Bs: if (tauB[j] == t) then w[j] else 0*w[j] end + sum <j> in Fs: mF[j,t]*y[j];
		
subto ModulationMinC:
	forall <j> in Bs:
		-w[j] <= v[j];
		
subto ModulationMaxC:
	forall <j> in Bs:
		v[j] >= W[j];
	
subto MinFlexibilityF:
	forall <j,t> in Fs*Ts:
		-mF[j,t]*y[j] <= x[j,t];
		
subto MaxFlexibilityF:
	forall <j,t> in Fs*Ts:
		x[j,t] >= MF[j,t]*y[j];
		