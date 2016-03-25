# Parameters
param N := read "network.csv" as "1n" use 1 comment "#";
set Ns := {0..N-1};
set N0 := {1..N-1};
param Lines := read "network.csv" as "2n" use 1 comment "#";
set Ls := {1..Lines};
param piTp := read "network.csv" as "3n" use 1 comment "#";
param piTd := read "network.csv" as "4n" use 1 comment "#";
param T := read "baselines.dat" as "2n" use 1 comment "#";
set Ts := {1..T};
param Sb := read "network.csv" as "5n" use 1 comment "#";
param Vb := read "network.csv" as "6n" use 1 comment "#";

param fromBus[Ls] := read "network.csv" as "<1n> 2n" skip 1 use Lines comment "#";
param toBus[Ls] := read "network.csv" as "<1n> 3n" skip 1 use Lines comment "#";
param Yg[Ls] := read "network.csv" as "<1n> 4n" skip 1 use Lines comment "#";
param Yb[Ls] := read "network.csv" as "<1n> 5n" skip 1 use Lines comment "#";
param C[Ls] := read "network.csv" as "<1n> 6n" skip 1 use Lines comment "#";

param V0 := read "network.csv" as "2n" skip 1+Lines use 1 comment "#";
param Vmin[Ns] := read "network.csv" as "3n" skip 1+Lines use N comment "#";
param Vmax[Ns] :=  read "network.csv" as "4n" skip 1+Lines use N comment "#";
param QPRatio[Ns] := read "network.csv" as "5n" skip 1+Lines use N comment "#";

param dP[Ns] := read "qualified-flex.csv" as "<1n> 2n" skip 1 use N comment "#";
param dM[Ns] := read "qualified-flex.csv" as "<1n> 3n" skip 1 use N comment "#";

param EPS := read "baselines.dat" as "5n" use 1 comment "#";
param dt := read "baselines.dat" as "4n" use 1 comment "#";
param injectionL[Ns*Ts] := read "baselines.dat" as "<1n,2n> 3n" skip 1 use N*T comment "#";
param injectionU[Ns*Ts] := read "baselines.dat" as "<1n,2n> 4n" skip 1 use N*T comment "#";
param dpLMax[Ns*Ts] := read "baselines.dat" as "<1n,2n> 5n" skip 1 use N*T comment "#";
param dpUMax[Ns*Ts] := read "baselines.dat" as "<1n,2n> 6n" skip 1 use N*T comment "#";

param l[Ns] := read "baselines.dat" as "<1n> 2n" skip 1+N*T use N comment "#";
param L[Ns] := read "baselines.dat" as "<1n> 3n" skip 1+N*T use N comment "#";

# Circle approximation parameters
param maxCPs:=4;
set cps := {1..maxCPs};
param cpCos[{0..maxCPs}] := <0> 1, <1> 0.923879532511287, <2> 0.707106781186548, <3> 0.382683432365090, <4> 0;
param cpSin[{0..maxCPs}] := <0> 0, <1> 0.382683432365090, <2> 0.707106781186547, <3> 0.923879532511287, <4> 1;

# Variables
var pL[<line,t> in Ls*Ts] >= -C[line]/Sb <= C[line]/Sb;
var qL[<line,t> in Ls*Ts] >= -C[line]/Sb <= C[line]/Sb;
var eL[Ns*Ts] >= -infinity;
var fL[Ns*Ts] >= -infinity;
var rL[Ns*Ts] >= -infinity;
var rLL[N0*Ts] >= 0;
var rLU[N0*Ts] >= 0;
var q0L[Ts] >= -infinity;	
var zetaL[Ns*Ts] >= 0;
var nuL[Ns*Ts] >= 0;

var pU[<line,t> in Ls*Ts] >= -C[line]/Sb <= C[line]/Sb;
var qU[<line,t> in Ls*Ts] >= -C[line]/Sb <= C[line]/Sb;
var eU[Ns*Ts] >= -infinity;
var fU[Ns*Ts] >= -infinity;
var rU[Ns*Ts] >= -infinity;
var rUU[N0*Ts] >= 0;
var rUL[N0*Ts] >= 0;
var q0U[Ts] >= -infinity;
var zetaU[Ns*Ts] >= 0;
var nuU[Ns*Ts] >= 0;	

var dpL[<n,t> in N0*Ts] >= 0 <= dpLMax[n,t];
var dpU[<n,t> in N0*Ts] >= 0 <= dpUMax[n,t];

# Objective
minimize Costs: 
	sum <n,t> in N0*Ts: (dP[n]*rU[n,t] + dM[n]*rL[n,t] + EPS*dpL[n,t] + EPS*dpU[n,t] )
	+ sum <n,t> in Ns*Ts : ((zetaL[n,t]+zetaU[n,t])*piTd*dt*Sb + (nuL[n,t]+nuU[n,t])*piTp*dt*Sb);

# Constraints
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

subto SlackVolgateEU:
	forall <t> in Ts:
		eU[0,t] == V0/Vb;

subto SlackVolgateFU:
	forall <t> in Ts:
		fU[0,t] == 0;

subto LinkVoltagePU:
	forall <line,t> in Ls*Ts : 
		pU[line,t] == V0/Vb * (Yg[line]*(eU[fromBus[line],t] - eU[toBus[line],t]) - Yb[line]*(fU[fromBus[line],t] - fU[toBus[line],t])) ;

subto LinkVoltageQU:
	forall <line,t> in Ls*Ts : 
		qU[line,t] == -V0/Vb * (Yb[line]*(eU[fromBus[line],t] - eU[toBus[line],t]) + Yg[line]*(fU[fromBus[line],t] - fU[toBus[line],t])) ;

subto BalanceNodePU:
	forall <n,t> in Ns*Ts :
		if (n == 0) then rU[0,t] else
		(injectionU[n,t]- dpU[n,t] + dpL[n,t] + rUU[n,t] - rLU[n,t])/Sb end
		== sum <line> in Ls : if (fromBus[line] == n) then pU[line,t] else 0*pU[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then pU[line,t] else 0*pU[line,t] end;	

subto BalanceNodeQU:
	forall <n,t> in Ns*Ts :
		if (n == 0) then q0U[t] else
		(injectionU[n,t]- dpU[n,t] + dpL[n,t] + rUU[n,t] - rLU[n,t])*QPRatio[n]/Sb end
		== sum <line> in Ls : if (fromBus[line] == n) then qU[line,t] else 0*qU[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then qU[line,t] else 0*qU[line,t] end;

subto MaxPowerNEQuadrantU:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*pU[line,t]+(cpCos[cp-1]-cpCos[cp])*qU[line,t] <= C[line]/Sb*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerNWQuadrantU:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*pU[line,t]+(cpCos[cp-1]-cpCos[cp])*qU[line,t] <= C[line]/Sb*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSEQuadrantU:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*pU[line,t]-(cpCos[cp-1]-cpCos[cp])*qU[line,t] <= C[line]/Sb*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSWQuadrantU:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*pU[line,t]-(cpCos[cp-1]-cpCos[cp])*qU[line,t] <= C[line]/Sb*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MinVoltageU:
	forall <n,t> in Ns*Ts :
		Vmin[n]-zetaU[n,t] <= eU[n,t];

subto NEVoltageBoundU:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*eU[n,t]+(cpCos[cp-1]-cpCos[cp])*fU[n,t] <= (Vmax[n]+nuU[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SEVoltageBoundU:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*eU[n,t]-(cpCos[cp-1]-cpCos[cp])*fU[n,t] <= (Vmax[n]+nuU[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SlackVolgateEL:
	forall <t> in Ts:
		eL[0,t] == V0/Vb;

subto SlackVolgateFL:
	forall <t> in Ts:
		fL[0,t] == 0;

subto LinkVoltagePL:
	forall <line,t> in Ls*Ts : 
		pL[line,t] == V0/Vb * (Yg[line]*(eL[fromBus[line],t] - eL[toBus[line],t]) - Yb[line]*(fL[fromBus[line],t] - fL[toBus[line],t])) ;

subto LinkVoltageQL:
	forall <line,t> in Ls*Ts : 
		qL[line,t] == -V0/Vb * (Yb[line]*(eL[fromBus[line],t] - eL[toBus[line],t]) + Yg[line]*(fL[fromBus[line],t] - fL[toBus[line],t])) ;

subto BalanceNodePL:
	forall <n,t> in Ns*Ts :
		if (n == 0) then rL[0,t] else
		(injectionL[n,t]- dpU[n,t] + dpL[n,t] + rUL[n,t] - rLL[n,t])/Sb end
		== sum <line> in Ls : if (fromBus[line] == n) then pL[line,t] else 0*pL[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then pL[line,t] else 0*pL[line,t] end;	

subto BalanceNodeQL:
	forall <n,t> in Ns*Ts :
		if (n == 0) then q0L[t] else
		(injectionU[n,t]- dpU[n,t] + dpL[n,t] + rUL[n,t] - rLL[n,t])*QPRatio[n]/Sb end
		== sum <line> in Ls : if (fromBus[line] == n) then qL[line,t] else 0*qL[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then qL[line,t] else 0*qL[line,t] end;

subto MaxPowerNEQuadrantL:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*pL[line,t]+(cpCos[cp-1]-cpCos[cp])*qL[line,t] <= C[line]/Sb*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerNWQuadrantL:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*pL[line,t]+(cpCos[cp-1]-cpCos[cp])*qL[line,t] <= C[line]/Sb*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSEQuadrantL:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*pL[line,t]-(cpCos[cp-1]-cpCos[cp])*qL[line,t] <= C[line]/Sb*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSWQuadrantL:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*pL[line,t]-(cpCos[cp-1]-cpCos[cp])*qL[line,t] <= C[line]/Sb*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MinVoltageL:
	forall <n,t> in Ns*Ts :
		Vmin[n]-zetaL[n,t] <= eL[n,t];

subto NEVoltageBoundL:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*eL[n,t]+(cpCos[cp-1]-cpCos[cp])*fL[n,t] <= (Vmax[n]+nuL[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SEVoltageBoundL:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*eL[n,t]-(cpCos[cp-1]-cpCos[cp])*fL[n,t] <= (Vmax[n]+nuL[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);
