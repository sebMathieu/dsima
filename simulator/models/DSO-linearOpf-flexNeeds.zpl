# Parameters
param N := read "network.csv" as "1n" use 1 comment "#";
set Ns := {0..N-1};
set N0 := {1..N-1};
param L := read "network.csv" as "2n" use 1 comment "#";
set Ls := {1..L};
param piTp := read "network.csv" as "3n" use 1 comment "#";
param piTd := read "network.csv" as "4n" use 1 comment "#";
param Sb := read "network.csv" as "5n" use 1 comment "#";
param Vb := read "network.csv" as "6n" use 1 comment "#";

param fromBus[Ls] := read "network.csv" as "<1n> 2n" skip 1 use L comment "#";
param toBus[Ls] := read "network.csv" as "<1n> 3n" skip 1 use L comment "#";
param Yg[Ls] := read "network.csv" as "<1n> 4n" skip 1 use L comment "#";
param Yb[Ls] := read "network.csv" as "<1n> 5n" skip 1 use L comment "#";
param C[Ls] := read "network.csv" as "<1n> 6n" skip 1 use L comment "#";

param V0 := read "network.csv" as "2n" skip 1+L use 1 comment "#";
param Vmin[Ns] := read "network.csv" as "3n" skip 1+L use N comment "#";
param Vmax[Ns] :=  read "network.csv" as "4n" skip 1+L use N comment "#";
param QPRatio[Ns] := read "network.csv" as "5n" skip 1+L use N comment "#";

param injection[Ns] := read "baselines.dat" as "<1n> 2n" skip 1 use N comment "#";
param dt := read "baselines.dat" as "4n" use 1 comment "#";

param dP[Ns] := read "qualified-flex.csv" as "<1n> 2n" skip 1 use N comment "#";
param dM[Ns] := read "qualified-flex.csv" as "<1n> 3n" skip 1 use N comment "#";

# Circle approximation parameters
param maxCPs:=4;
set cps := {1..maxCPs};
param cpCos[{0..maxCPs}] := <0> 1, <1> 0.923879532511287, <2> 0.707106781186548, <3> 0.382683432365090, <4> 0;
param cpSin[{0..maxCPs}] := <0> 0, <1> 0.382683432365090, <2> 0.707106781186547, <3> 0.923879532511287, <4> 1;

# Variables
var p[<line> in Ls] >= -C[line]/Sb <= C[line]/Sb;
var q[<line> in Ls] >= -C[line]/Sb <= C[line]/Sb;
var e[Ns] >= -infinity;
var f[Ns] >= -infinity;
var r0 >= -infinity;
var q0 >= -infinity;
var zeta[Ns] >= 0;
var nu[Ns] >= 0;

var rU[Ns] >= 0;
var rL[Ns] >= 0;

# Objective
minimize flexRequirement: 
	sum <n> in N0 : (dP[n]*rU[n] + dM[n]*rL[n])
	+ sum<n> in Ns: (zeta[n]*piTd*dt*Sb + nu[n]*piTp*dt*Sb);

# Constraints
subto SlackVolgateE:
		e[0] == V0/Vb;

subto SlackVolgateF:
		f[0] == 0;

subto LinkVoltageP:
	forall <line> in Ls : 
		p[line] == V0/Vb * (Yg[line]*(e[fromBus[line]] - e[toBus[line]]) - Yb[line]*(f[fromBus[line]] - f[toBus[line]])) ;

subto LinkVoltageQ:
	forall <line> in Ls : 
		q[line] == -V0/Vb * (Yb[line]*(e[fromBus[line]] - e[toBus[line]]) + Yg[line]*(f[fromBus[line]] - f[toBus[line]])) ;

subto BalanceNodeP:
	forall <n> in Ns :
		(injection[n]+ rU[n] - rL[n])/Sb
		+ if (n == 0) then r0 else 0*r0 end
		== sum <line> in Ls : if (fromBus[line] == n) then p[line] else 0*p[line] end
		- sum <line> in Ls : if (toBus[line] == n) then p[line] else 0*p[line] end;	

subto BalanceNodeQ:
	forall <n> in Ns :
		(injection[n]+ rU[n] - rL[n])*QPRatio[n]/Sb
		+ if (n == 0) then q0 else 0*q0 end
		== sum <line> in Ls : if (fromBus[line] == n) then q[line] else 0*q[line] end
		- sum <line> in Ls : if (toBus[line] == n) then q[line] else 0*q[line] end;	

subto MaxPowerNEQuadrant:
	forall <line,cp> in Ls*cps:
		(cpSin[cp]-cpSin[cp-1])*p[line]+(cpCos[cp-1]-cpCos[cp])*q[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerNWQuadrant:
	forall <line,cp> in Ls*cps:
		-(cpSin[cp]-cpSin[cp-1])*p[line]+(cpCos[cp-1]-cpCos[cp])*q[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSEQuadrant:
	forall <line,cp> in Ls*cps:
		(cpSin[cp]-cpSin[cp-1])*p[line]-(cpCos[cp-1]-cpCos[cp])*q[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSWQuadrant:
	forall <line,cp> in Ls*cps:
		-(cpSin[cp]-cpSin[cp-1])*p[line]-(cpCos[cp-1]-cpCos[cp])*q[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MinVoltage:
	forall <n> in Ns :
		Vmin[n]-zeta[n] <= e[n];

subto NEVoltageBound:
	forall <n,cp> in Ns*cps:
		(cpSin[cp]-cpSin[cp-1])*e[n]+(cpCos[cp-1]-cpCos[cp])*f[n] <= (Vmax[n]+nu[n])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SEVoltageBound:
	forall <n,cp> in Ns*cps:
		(cpSin[cp]-cpSin[cp-1])*e[n]-(cpCos[cp-1]-cpCos[cp])*f[n] <= (Vmax[n]+nu[n])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

