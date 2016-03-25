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
 
param T := read "baselines-full.dat" as "2n" use 1 comment "#";
set Ts := {1..T};
param dt := read "baselines-full.dat" as "4n" use 1 comment "#";
param EPS := read "baselines-full.dat" as "5n" use 1 comment "#";
param injection[Ns*Ts] := read "baselines-full.dat" as "<1n,2n> 3n" skip 1 use (N*T) comment "#";

# Circle approximation parameters
param maxCPs:=4;
set cps := {1..maxCPs};
param cpCos[{0..maxCPs}] := <0> 1, <1> 0.923879532511287, <2> 0.707106781186548, <3> 0.382683432365090, <4> 0;
param cpSin[{0..maxCPs}] := <0> 0, <1> 0.382683432365090, <2> 0.707106781186547, <3> 0.923879532511287, <4> 1;

# Variables
var p[<line,t> in Ls*Ts] >= -C[line]/Sb-EPS <= C[line]/Sb+EPS;
var q[<line,t> in Ls*Ts] >= -C[line]/Sb-EPS <= C[line]/Sb+EPS;
var e[Ns*Ts] >= -infinity;
var f[Ns*Ts] >= -infinity;
var r0[Ts] >= -infinity;
var q0[Ts] >= -infinity;
var zeta[Ns*Ts] >= 0;
var nu[Ns*Ts] >= 0;

var pr[Ls*Ts] >= -infinity;
var qr[Ls*Ts] >= -infinity;
var er[Ns*Ts] >= -infinity;
var fr[Ns*Ts] >= -infinity;
var r0r[Ts] >= -infinity;
var q0r[Ts] >= -infinity;

var flowViolation[Ls*Ts] >= 0;
var voltageViolation[Ns*Ts] >= 0;

var z[Ns*Ts] binary;
var trippingCost[Ns*Ts] >= 0;

# Objective
minimize Costs: 
	sum <n,t> in Ns*Ts : (trippingCost[n,t] + zeta[n,t]*EPS + nu[n,t]*EPS) + sum <n,t> in Ns*Ts : EPS*voltageViolation[n,t] + sum <line,t> in Ls*Ts : EPS*flowViolation[line,t];

# Constraints
subto TrippingCostProductionDefinition:
	forall <n,t> in Ns*Ts :
		trippingCost[n,t]>=z[n,t]*piTp*dt*injection[n,t];

subto TrippingCostConsumptionDefinition:
	forall <n,t> in Ns*Ts :
		trippingCost[n,t]>=z[n,t]*piTd*dt*(-injection[n,t]);

subto SlackVolgateEr:
	forall <t> in Ts:
		er[0,t] == V0/Vb;

subto SlackVolgateFr:
	forall <t> in Ts:
		fr[0,t] == 0;

subto LinkVoltagePr:
	forall <line,t> in Ls*Ts : 
		pr[line,t] == V0/Vb * (Yg[line]*(er[fromBus[line],t] - er[toBus[line],t]) - Yb[line]*(fr[fromBus[line],t] - fr[toBus[line],t])) ;

subto LinkVoltageQr:
	forall <line,t> in Ls*Ts : 
		qr[line,t] == -V0/Vb * (Yb[line]*(er[fromBus[line],t] - er[toBus[line],t]) + Yg[line]*(fr[fromBus[line],t] - fr[toBus[line],t])) ;

subto ObservedProductionNodePr:
	forall <n,t> in Ns*Ts :
		injection[n,t]/Sb
		+ if (n == 0) then r0r[t] else 0*r0r[t] end
		== sum <line> in Ls : if (fromBus[line] == n) then pr[line,t] else 0*pr[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then pr[line,t] else 0*pr[line,t] end;	

subto ObservedProductionNodeQr:
	forall <n,t> in Ns*Ts :
		injection[n,t]*QPRatio[n]/Sb
		+ if (n == 0) then q0r[t] else 0*q0r[t] end
		== sum <line> in Ls : if (fromBus[line] == n) then qr[line,t] else 0*qr[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then qr[line,t] else 0*qr[line,t] end;

subto MaxPowerNEQuadrantR:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*pr[line,t]+(cpCos[cp-1]-cpCos[cp])*qr[line,t] <= ((C[line]+flowViolation[line,t])/Sb+EPS)*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto MaxPowerNWQuadrantR:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*pr[line,t]+(cpCos[cp-1]-cpCos[cp])*qr[line,t] <= ((C[line]+flowViolation[line,t])/Sb+EPS)*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto MaxPowerSEQuadrantR:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*pr[line,t]-(cpCos[cp-1]-cpCos[cp])*qr[line,t] <= ((C[line]+flowViolation[line,t])/Sb+EPS)*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto MaxPowerSWQuadrantR:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*pr[line,t]-(cpCos[cp-1]-cpCos[cp])*qr[line,t] <= ((C[line]+flowViolation[line,t])/Sb+EPS)*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto MinVoltageR:
	forall <n,t> in Ns*Ts :
		Vmin[n]-EPS-voltageViolation[n,t] <= er[n,t];

subto NEVoltageBoundR:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*er[n,t]+(cpCos[cp-1]-cpCos[cp])*fr[n,t] <= (Vmax[n]+EPS+voltageViolation[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SEVoltageBoundR:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*er[n,t]-(cpCos[cp-1]-cpCos[cp])*fr[n,t] <= (Vmax[n]+EPS+voltageViolation[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SlackVolgateE:
	forall <t> in Ts:
		e[0,t] == V0/Vb;

subto SlackVolgateF:
	forall <t> in Ts:
		f[0,t] == 0;

subto LinkVoltageP:
	forall <line,t> in Ls*Ts : 
		p[line,t] == V0/Vb * (Yg[line]*(e[fromBus[line],t] - e[toBus[line],t]) - Yb[line]*(f[fromBus[line],t] - f[toBus[line],t])) ;

subto LinkVoltageQ:
	forall <line,t> in Ls*Ts : 
		q[line,t] == -V0/Vb * (Yb[line]*(e[fromBus[line],t] - e[toBus[line],t]) + Yg[line]*(f[fromBus[line],t] - f[toBus[line],t])) ;

subto RealProductionNodeP:
	forall <n,t> in Ns*Ts :
		(1-z[n,t])*injection[n,t]/Sb
		+ if (n == 0) then r0[t] else 0*r0[t] end
		== sum <line> in Ls : if (fromBus[line] == n) then p[line,t] else 0*p[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then p[line,t] else 0*p[line,t] end;	

subto RealProductionNodeQ:
	forall <n,t> in Ns*Ts :
		(1-z[n,t])*injection[n,t]*QPRatio[n]/Sb
		+ if (n == 0) then q0[t] else 0*q0[t] end
		== sum <line> in Ls : if (fromBus[line] == n) then q[line,t] else 0*q[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then q[line,t] else 0*q[line,t] end;	

subto MaxPowerNEQuadrant:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*p[line,t]+(cpCos[cp-1]-cpCos[cp])*q[line,t] <= (C[line]/Sb+EPS)*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto MaxPowerNWQuadrant:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*p[line,t]+(cpCos[cp-1]-cpCos[cp])*q[line,t] <= (C[line]/Sb+EPS)*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto MaxPowerSEQuadrant:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*p[line,t]-(cpCos[cp-1]-cpCos[cp])*q[line,t] <= (C[line]/Sb+EPS)*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto MaxPowerSWQuadrant:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*p[line,t]-(cpCos[cp-1]-cpCos[cp])*q[line,t] <= (C[line]/Sb+EPS)*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto MinVoltage:
	forall <n,t> in Ns*Ts :
		Vmin[n]-EPS-zeta[n,t] <= e[n,t];

subto NEVoltageBound:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*e[n,t]+(cpCos[cp-1]-cpCos[cp])*f[n,t] <= (Vmax[n]+EPS+nu[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SEVoltageBound:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*e[n,t]-(cpCos[cp-1]-cpCos[cp])*f[n,t] <= (Vmax[n]+EPS+nu[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);
