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

param aP[Ns] := read "qualified-flex.csv" as "<1n> 2n" skip 1 use N comment "#";
param aM[Ns] := read "qualified-flex.csv" as "<1n> 3n" skip 1 use N comment "#";

# Variables
var f[Ls] >= -infinity;
var dC[Ls] >= 0;
var r0 >= -infinity;

# Objective
minimize flexRequirement: 
	sum <line> in Ls : dC[line];

# Constraints
subto LineCapaUp:
	forall <line> in Ls : 
		f[line] <= (C[line]+dC[line]);

subto LineCapaDown:
	forall <line> in Ls : 
		-(C[line]+dC[line]) <= f[line];

subto BalanceNode:
	forall <n> in Ns :
		p[n]
		+ if (n==0) then r0 else 0*r0 end
		- sum <line> in Ls : if (fromBus[line] == n) then f[line] else 0*f[line] end
		+ sum <line> in Ls : if (toBus[line] == n) then f[line] else 0*f[line] end
		== 0;
									