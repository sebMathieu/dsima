# Parameters
param N := read "network.csv" as "1n" use 1 comment "#";
set Ns := {0..N-1};
set N0 := {1..N-1};
param L := read "network.csv" as "2n" use 1 comment "#";
set Ls := {1..L};

param fromBus[Ls] := read "network.csv" as "<1n> 2n" skip 1 use L comment "#";
param toBus[Ls] := read "network.csv" as "<1n> 3n" skip 1 use L comment "#";
param C[Ls] := read "network.csv" as "<1n> 6n" skip 1 use L comment "#";

param p[Ns] := read "baselines.dat" as "<1n> 2n" skip 1 use N comment "#";

param dP[Ns] := read "qualified-flex.csv" as "<1n> 2n" skip 1 use N comment "#";
param dM[Ns] := read "qualified-flex.csv" as "<1n> 3n" skip 1 use N comment "#";

# Variables
var f[<line> in Ls] >= -C[line] <= C[line];
var rU[Ns] >= 0;
var rL[Ns] >= 0;

# Objective
minimize flexRequirement: 
	sum <n> in Ns : (dP[n]*rU[n] + dM[n]*rL[n]);

# Constraints
subto BalanceNode:
	forall <n> in Ns :
		p[n] + rU[n] - rL[n] 
		- sum <line> in Ls : if (fromBus[line] == n) then f[line] else 0*f[line] end
		+ sum <line> in Ls : if (toBus[line] == n) then f[line] else 0*f[line] end
		== 0;
									