# Parameters
param N := read "network.csv" as "1n" use 1 comment "#";
set Ns := {0..N-1};
set N0 := {1..N-1};
param L := read "network.csv" as "2n" use 1 comment "#";
set Ls := {1..L};

param fromBus[Ls] := read "network.csv" as "<1n> 2n" skip 1 use L comment "#";
param toBus[Ls] := read "network.csv" as "<1n> 3n" skip 1 use L comment "#";
param C[Ls] := read "network.csv" as "<1n> 6n" skip 1 use L comment "#";

param minCurtail := read "accessRequests.dat" as "2n" use 1 comment "#";
param EPS := read "accessRequests.dat" as "3n" use 1 comment "#";
param g[Ns] := read "accessRequests.dat" as "<1n> 2n" skip 1 use N comment "#";
param G[Ns] := read "accessRequests.dat" as "<1n> 3n" skip 1 use N comment "#";

# Variables
var fL[<line> in Ls] >= -C[line] <= C[line];
var fU[<line> in Ls] >= -C[line] <= C[line];
var rL0 >= -infinity;
var rU0 >= -infinity;
var dg[<n> in Ns] >= 0 <= -g[n];
var dG[<n> in Ns] >= 0 <= G[n];

var maxDg >= 0;
var maxDG >= 0;

# Objective
minimize accessRestrictions: 
	maxDg + maxDG;

subto maxDgDefinition:
	forall <n> in Ns:
		maxDg >= dg[n]/(if abs(g[n]) >= minCurtail then abs(g[n]) else EPS end);

subto maxDGDefinition:
	forall <n> in Ns:
		maxDG >= dG[n]/(if abs(G[n]) >= minCurtail then abs(G[n]) else EPS end);
		
subto BalanceNodeL:
	forall <n> in Ns :
		g[n] + dg[n]
		+ if (n==0) then rL0 else 0*rL0 end
		- sum <line> in Ls : if (fromBus[line] == n) then fL[line] else 0*fL[line] end
		+ sum <line> in Ls : if (toBus[line] == n) then fL[line] else 0*fL[line] end
		== 0;
							
subto BalanceNodeU:
	forall <n> in Ns :
		G[n] - dG[n]
		+ if (n==0) then rU0 else 0*rU0 end
		- sum <line> in Ls : if (fromBus[line] == n) then fU[line] else 0*fU[line] end
		+ sum <line> in Ls : if (toBus[line] == n) then fU[line] else 0*fU[line] end
		== 0;		