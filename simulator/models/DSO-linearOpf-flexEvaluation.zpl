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
param gamma := read "baselines-full.dat" as "3n" use 1 comment "#";
param dt := read "baselines-full.dat" as "4n" use 1 comment "#";
param injection[Ns*Ts] := read "baselines-full.dat" as "<1n,2n> 3n" skip 1 use (N*T) comment "#";

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
var p[<line,t> in Ls*Ts] >= -C[line]/Sb <= C[line]/Sb;
var q[<line,t> in Ls*Ts] >= -C[line]/Sb <= C[line]/Sb;
var e[Ns*Ts] >= -infinity;
var f[Ns*Ts] >= -infinity;
var r0[Ts] >= -infinity;
var q0[Ts] >= -infinity;
var zeta[Ns*Ts] >= 0;
var nu[Ns*Ts] >= 0;

var I[Ts] >= -infinity;
var IP[Ts] >=0;
var IM[Ts] >=0;

var r[Ns*Ts] >= -infinity;
var x[<j,t> in Fs*Ts] >= mF[j,t] <= MF[j,t];
var xU[<j,t> in Fs*Ts] >= 0;
var xL[<j,t> in Fs*Ts] >= 0;
var y[Fs] binary;
var z[Ns*Ts] binary;
var v[<j> in Bs] >= mB[j] <= MB[j];
var w[<j> in Bs] >= mB[j] <= 0;
var W[<j> in Bs] >= 0 <= MB[j];
 
var trippingCost[Ns*Ts] >= 0;

# Circle approximation parameters
param maxCPs:=4;
set cps := {1..maxCPs};
param cpCos[{0..maxCPs}] := <0> 1, <1> 0.923879532511287, <2> 0.707106781186548, <3> 0.382683432365090, <4> 0;
param cpSin[{0..maxCPs}] := <0> 0, <1> 0.382683432365090, <2> 0.707106781186547, <3> 0.923879532511287, <4> 1;

# Objective
minimize Costs: 
	sum <j> in Fs : (piRF[j]*y[j] + piAF[j]*(sum <t> in Ts : (xU[j,t] + xL[j,t])))
	+ sum <j> in Bs : (piAB[j]*v[j] + piRB[j]*(W[j]-w[j]))
	+ sum <n,t> in Ns*Ts :  (trippingCost[n,t] + zeta[n,t]*piTd*dt + nu[n,t]*piTp*dt)
	+ sum <t> in Ts : (gamma*piIP[t]*IP[t]+gamma*piIM[t]*IM[t])
	;

# Constraints
subto TrippingCostProductionDefinition:
	forall <n,t> in Ns*Ts :
		trippingCost[n,t]>=z[n,t]*piTp*dt*injection[n,t];

subto TrippingCostConsumptionDefinition:
	forall <n,t> in Ns*Ts :
		trippingCost[n,t]>=z[n,t]*piTd*dt*(-injection[n,t]);

subto FlexActivation:
	forall <n,t> in N0*Ts :
		r[n,t] == 
		+ sum <j> in Fs : if (nodeF[j] == n) then x[j,t] else 0*x[j,t] end
		+ sum <j> in Bs : if (nodeB[j] == n and tauB[j] == t) then v[j] else 0*v[j] end;
		
subto totalImbalance:
	forall <t> in Ts :
		I[t] == IP[t] - IM[t];

subto Imbalance:
	forall <t> in Ts :
		IP[t] - IM[t] == sum <n> in N0: r[n,t];
		
subto TrippingMinFlexibilityC:
	forall <j> in Bs:
		mB[j]*(1-z[nodeB[j],tauB[j]]) <= w[j];
		
subto TrippingMaxFlexibilityC:
	forall <j> in Bs:
		W[j] <= MB[j]*(1-z[nodeB[j],tauB[j]]);

subto ModulationMinC:
	forall <j> in Bs:
		w[j] <= v[j];
		
subto ModulationMaxC:
	forall <j> in Bs:
		v[j] <= W[j];
		
subto MinFlexibilityF:
	forall <j,t> in Fs*Ts:
		mF[j,t]*y[j] <= x[j,t];
		
subto MaxFlexibilityF:
	forall <j,t> in Fs*Ts:
		x[j,t] <= MF[j,t]*y[j];
		
subto TrippingMinFlexibilityF:
	forall <j,t> in Fs*Ts:
		mF[j,t]*(1-z[nodeF[j],t]) <= x[j,t];
		
subto TrippingMaxFlexibilityF:
	forall <j,t> in Fs*Ts:
		x[j,t] <= MF[j,t]*(1-z[nodeF[j],t]);

subto FlexSignF:
	forall <j,t> in Fs*Ts:
		x[j,t] == xU[j,t] - xL[j,t];
		
subto ConstantEnergy:
	forall <j> in Fs:
		sum <t> in Ts : x[j,t] == 0;
			
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

subto BalanceNodeP:
	forall <n,t> in Ns*Ts :
		r[n,t] + (1-z[n,t])*injection[n,t]/Sb
		+ if (n == 0) then r0[t] else 0*r0[t] end
		== sum <line> in Ls : if (fromBus[line] == n) then p[line,t] else 0*p[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then p[line,t] else 0*p[line,t] end;	

subto BalanceNodeQ:
	forall <n,t> in Ns*Ts :
		r[n,t]*QPRatio[n]/Sb + (1-z[n,t])*injection[n,t]*QPRatio[n]/Sb
		+ if (n == 0) then q0[t] else 0*q0[t] end
		== sum <line> in Ls : if (fromBus[line] == n) then q[line,t] else 0*q[line,t] end
		- sum <line> in Ls : if (toBus[line] == n) then q[line,t] else 0*q[line,t] end;	

subto MaxPowerNEQuadrant:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*p[line,t]+(cpCos[cp-1]-cpCos[cp])*q[line,t] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerNWQuadrant:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*p[line,t]+(cpCos[cp-1]-cpCos[cp])*q[line,t] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSEQuadrant:
	forall <line,t,cp> in Ls*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*p[line,t]-(cpCos[cp-1]-cpCos[cp])*q[line,t] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSWQuadrant:
	forall <line,t,cp> in Ls*Ts*cps:
		-(cpSin[cp]-cpSin[cp-1])*p[line,t]-(cpCos[cp-1]-cpCos[cp])*q[line,t] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MinVoltage:
	forall <n,t> in Ns*Ts :
		Vmin[n]-zeta[n,t] <= e[n,t];

subto NEVoltageBound:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*e[n,t]+(cpCos[cp-1]-cpCos[cp])*f[n,t] <= (Vmax[n]+nu[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SEVoltageBound:
	forall <n,t,cp> in Ns*Ts*cps:
		(cpSin[cp]-cpSin[cp-1])*e[n,t]-(cpCos[cp-1]-cpCos[cp])*f[n,t] <= (Vmax[n]+nu[n,t])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);
