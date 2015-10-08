# Parameters
param N := read "network.csv" as "1n" use 1 comment "#";
set Ns := {0..N-1};
set N0 := {1..N-1};
param Lines := read "network.csv" as "2n" use 1 comment "#";
set Ls := {1..Lines};
param T := read "baselines.dat" as "2n" use 1 comment "#";
set Ts := {1..T};

param fromBus[Ls] := read "network.csv" as "<1n> 2n" skip 1 use Lines comment "#";
param toBus[Ls] := read "network.csv" as "<1n> 3n" skip 1 use Lines comment "#";
param C[Ls] := read "network.csv" as "<1n> 6n" skip 1 use Lines comment "#";

param dP[Ns] := read "qualified-flex.csv" as "<1n> 2n" skip 1 use N comment "#";
param dM[Ns] := read "qualified-flex.csv" as "<1n> 3n" skip 1 use N comment "#";

param EPS := read "baselines.dat" as "5n" use 1 comment "#";
param pL[Ns*Ts] := read "baselines.dat" as "<1n,2n> 3n" skip 1 use N*T comment "#";
param pU[Ns*Ts] := read "baselines.dat" as "<1n,2n> 4n" skip 1 use N*T comment "#";
param dpLMax[Ns*Ts] := read "baselines.dat" as "<1n,2n> 5n" skip 1 use N*T comment "#";
param dpUMax[Ns*Ts] := read "baselines.dat" as "<1n,2n> 6n" skip 1 use N*T comment "#";

param l[Ns] := read "baselines.dat" as "<1n> 2n" skip 1+N*T use N comment "#";
param L[Ns] := read "baselines.dat" as "<1n> 3n" skip 1+N*T use N comment "#";

# Variables
var fL[<line,t> in Ls*Ts] >= -C[line] <= C[line];
var fU[<line,t> in Ls*Ts] >= -C[line] <= C[line];
var rL[N0*Ts] >= 0;
var rU[N0*Ts] >= 0;
var rLL[N0*Ts] >= 0;
var rUL[N0*Ts] >= 0;
var rLU[N0*Ts] >= 0;
var rUU[N0*Ts] >= 0;
var dpL[<n,t> in N0*Ts] >= 0 <= dpLMax[n,t];
var dpU[<n,t> in N0*Ts] >= 0 <= dpUMax[n,t];

# Objective
minimize flexRequirement: 
	sum <n,t> in N0*Ts: (dP[n]*rU[n,t] + dM[n]*rL[n,t] + EPS*dpL[n,t] + EPS*dpU[n,t] );

# Constraints
subto BalanceNodeL:
	forall <n,t> in N0*Ts:
		pL[n,t] - dpU[n,t] + dpL[n,t] + rUL[n,t] - rLL[n,t] 
		- sum <line> in Ls : if (fromBus[line] == n) then fL[line,t] else 0*fL[line,t] end
		+ sum <line> in Ls : if (toBus[line] == n) then fL[line,t] else 0*fL[line,t] end
		== 0;

subto BalanceNodeU:
	forall <n,t> in N0*Ts:
		pU[n,t] - dpU[n,t] + dpL[n,t] + rUU[n,t] - rLU[n,t] 
		- sum <line> in Ls : if (fromBus[line] == n) then fU[line,t] else 0*fU[line,t] end
		+ sum <line> in Ls : if (toBus[line] == n) then fU[line,t] else 0*fU[line,t] end
		== 0;

subto minFlexBoundLL:
	forall <n,t> in N0*Ts:
		rL[n,t]>=rLL[n,t];

subto minFlexBoundLU:
	forall <n,t> in N0*Ts:
		rL[n,t]>=rLU[n,t];

subto minFlexBoundUL:
	forall <n,t> in N0*Ts:
		rU[n,t]>=rUL[n,t];

subto minFlexBoundUU:
	forall <n,t> in N0*Ts:
		rU[n,t]>=rUU[n,t];
					
