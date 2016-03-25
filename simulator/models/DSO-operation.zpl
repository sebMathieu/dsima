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
param dt := read "baselines-full.dat" as "4n" use 1 comment "#";
param EPS := read "baselines-full.dat" as "5n" use 1 comment "#";
param p[Ns*Ts] := read "baselines-full.dat" as "<1n,2n> 3n" skip 1 use (N*T) comment "#";

# Variables
var f[<line,t> in Ls*Ts] >= -C[line]-EPS <= C[line]+EPS ;
var r0[Ts] >= -infinity;

var fr[Ls*Ts] >= -infinity;
var r0r[Ts] >= -infinity;
var flowViolation[Ls*Ts] >= 0;

var z[Ns*Ts] binary;
var trippingCost[Ns*Ts] >= 0;

# Objective
minimize Costs: 
	sum <n,t> in Ns*Ts : trippingCost[n,t] + sum <line,t> in Ls*Ts : EPS*flowViolation[line,t];

# Constraints
subto TrippingCostProductionDefinition:
	forall <n,t> in Ns*Ts :
		trippingCost[n,t]>=z[n,t]*piTp*dt*p[n,t];

subto TrippingCostConsumptionDefinition:
	forall <n,t> in Ns*Ts :
		trippingCost[n,t]>=z[n,t]*piTd*dt*(-p[n,t]);

subto ObservedProductionNode:
	forall <n,t> in Ns*Ts :
		p[n,t]
		+ if (n == 0) then r0r[t] else 0*r0r[t] end
		== sum <line> in Ls : if (fromBus[line] == n) then fr[line,t] else 0*fr[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then fr[line,t] else 0*fr[line,t] end;	

subto RealProductionNode:
	forall <n,t> in Ns*Ts :
		(1-z[n,t])*p[n,t]
		+ if (n == 0) then r0[t] else 0*r0[t] end
		== sum <line> in Ls : if (fromBus[line] == n) then f[line,t] else 0*f[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then f[line,t] else 0*f[line,t] end;	

subto FlowViolationUp:
	forall <line,t> in Ls*Ts:
		fr[line,t] <= C[line] + flowViolation[line,t];			
		
subto FlowViolationDown:
	forall <line,t> in Ls*Ts:
		fr[line,t] >= -C[line] - flowViolation[line,t];
		