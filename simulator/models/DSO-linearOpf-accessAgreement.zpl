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

param minCurtail := read "accessRequests.dat" as "2n" use 1 comment "#";
param EPS := read "accessRequests.dat" as "3n" use 1 comment "#";
param g[Ns] := read "accessRequests.dat" as "<1n> 2n" skip 1 use N comment "#";
param G[Ns] := read "accessRequests.dat" as "<1n> 3n" skip 1 use N comment "#";

# Circle approximation parameters
param maxCPs:=4;
set cps := {1..maxCPs};
param cpCos[{0..maxCPs}] := <0> 1, <1> 0.923879532511287, <2> 0.707106781186548, <3> 0.382683432365090, <4> 0;
param cpSin[{0..maxCPs}] := <0> 0, <1> 0.382683432365090, <2> 0.707106781186547, <3> 0.923879532511287, <4> 1;

# Variables
var pL[<line> in Ls] >= -C[line]/Sb <= C[line]/Sb;
var qL[<line> in Ls] >= -C[line]/Sb <= C[line]/Sb;
var eL[<n> in Ns] >= -infinity;
var fL[<n> in Ns] >= -infinity;
var r0L >= -infinity;
var q0L >= -infinity;
var zetaL[Ns] >= 0;
var nuL[Ns] >= 0;

var pU[<line> in Ls] >= -C[line]/Sb <= C[line]/Sb;
var qU[<line> in Ls] >= -C[line]/Sb <= C[line]/Sb;
var eU[<n> in Ns] >= -infinity;
var fU[<n> in Ns] >= -infinity;
var r0U >= -infinity;
var q0U >= -infinity;
var zetaU[Ns] >= 0;
var nuU[Ns] >= 0;

var dg[<n> in Ns] >= 0 <= -g[n];
var dG[<n> in Ns] >= 0 <= G[n];

var maxDg >= 0;
var maxDG >= 0;

# Objective
minimize accessRestrictions: 
	maxDg*piTd + maxDG*piTp
	+ sum<n> in Ns: ((zetaL[n]+zetaU[n])*piTd*Sb + (nuL[n]+nuU[n])*piTp*Sb);

subto maxDgDefinition:
	forall <n> in Ns:
		maxDg >= dg[n]/(if abs(g[n]) >= minCurtail then abs(g[n]) else EPS end);

subto maxDGDefinition:
	forall <n> in Ns:
		maxDG >= dG[n]/(if abs(G[n]) >= minCurtail then abs(G[n]) else EPS end);

subto SlackVolgateEL:
		eL[0] == V0/Vb;

subto SlackVolgateFL:
		fL[0] == 0;

subto LinkVoltagePL:
	forall <line> in Ls : 
		pL[line] == V0/Vb * (Yg[line]*(eL[fromBus[line]] - eL[toBus[line]]) - Yb[line]*(fL[fromBus[line]] - fL[toBus[line]])) ;

subto LinkVoltageQL:
	forall <line> in Ls : 
		qL[line] == -V0/Vb * (Yb[line]*(eL[fromBus[line]] - eL[toBus[line]]) + Yg[line]*(fL[fromBus[line]] - fL[toBus[line]])) ;

subto BalanceNodePL:
	forall <n> in Ns :
		(g[n] + dg[n])/Sb
		+ if (n==0) then r0L else 0*r0L end
		- sum <line> in Ls : if (fromBus[line] == n) then pL[line] else 0*pL[line] end
		+ sum <line> in Ls : if (toBus[line] == n) then pL[line] else 0*pL[line] end
		== 0;

subto BalanceNodeQL:
	forall <n> in Ns :
		(g[n] + dg[n])*QPRatio[n]/Sb
		+ if (n==0) then q0L else 0*q0L end
		- sum <line> in Ls : if (fromBus[line] == n) then qL[line] else 0*qL[line] end
		+ sum <line> in Ls : if (toBus[line] == n) then qL[line] else 0*qL[line] end
		== 0;
				
subto MaxPowerNEQuadrantL:
	forall <line,cp> in Ls*cps:
		(cpSin[cp]-cpSin[cp-1])*pL[line]+(cpCos[cp-1]-cpCos[cp])*qL[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerNWQuadrantL:
	forall <line,cp> in Ls*cps:
		-(cpSin[cp]-cpSin[cp-1])*pL[line]+(cpCos[cp-1]-cpCos[cp])*qL[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSEQuadrantL:
	forall <line,cp> in Ls*cps:
		(cpSin[cp]-cpSin[cp-1])*pL[line]-(cpCos[cp-1]-cpCos[cp])*qL[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSWQuadrantL:
	forall <line,cp> in Ls*cps:
		-(cpSin[cp]-cpSin[cp-1])*pL[line]-(cpCos[cp-1]-cpCos[cp])*qL[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));
	
subto MinVoltageL:
	forall <n> in Ns :
		Vmin[n]-zetaL[n] <= eL[n];

subto NEVoltageBoundL:
	forall <n,cp> in Ns*cps:
		(cpSin[cp]-cpSin[cp-1])*eL[n]+(cpCos[cp-1]-cpCos[cp])*fL[n] <= (Vmax[n]+nuL[n])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SEVoltageBoundL:
	forall <n,cp> in Ns*cps:
		(cpSin[cp]-cpSin[cp-1])*eL[n]-(cpCos[cp-1]-cpCos[cp])*fL[n] <= (Vmax[n]+nuL[n])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SlackVolgateEU:
		eU[0] == V0/Vb;

subto SlackVolgateFU:
		fU[0] == 0;

subto LinkVoltagePU:
	forall <line> in Ls : 
		pU[line] == V0/Vb * (Yg[line]*(eU[fromBus[line]] - eU[toBus[line]]) - Yb[line]*(fU[fromBus[line]] - fU[toBus[line]])) ;

subto LinkVoltageQU:
	forall <line> in Ls : 
		qU[line] == -V0/Vb * (Yb[line]*(eU[fromBus[line]] - eU[toBus[line]]) + Yg[line]*(fU[fromBus[line]] - fU[toBus[line]])) ;
		
subto BalanceNodePU:
	forall <n> in Ns :
		(G[n] - dG[n])/Sb
		+ if (n==0) then r0U else 0*r0U end
		- sum <line> in Ls : if (fromBus[line] == n) then pU[line] else 0*pU[line] end
		+ sum <line> in Ls : if (toBus[line] == n) then pU[line] else 0*pU[line] end
		== 0;		
		
subto BalanceNodeQU:
	forall <n> in Ns :
		(G[n] - dG[n])*QPRatio[n]/Sb
		+ if (n==0) then q0U else 0*q0U end
		- sum <line> in Ls : if (fromBus[line] == n) then qU[line] else 0*qU[line] end
		+ sum <line> in Ls : if (toBus[line] == n) then qU[line] else 0*qU[line] end
		== 0;	
			
subto MaxPowerNEQuadrantU:
	forall <line,cp> in Ls*cps:
		(cpSin[cp]-cpSin[cp-1])*pU[line]+(cpCos[cp-1]-cpCos[cp])*qU[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerNWQuadrantU:
	forall <line,cp> in Ls*cps:
		-(cpSin[cp]-cpSin[cp-1])*pU[line]+(cpCos[cp-1]-cpCos[cp])*qU[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSEQuadrantU:
	forall <line,cp> in Ls*cps:
		(cpSin[cp]-cpSin[cp-1])*pU[line]-(cpCos[cp-1]-cpCos[cp])*qU[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));

subto MaxPowerSWQuadrantU:
	forall <line,cp> in Ls*cps:
		-(cpSin[cp]-cpSin[cp-1])*pU[line]-(cpCos[cp-1]-cpCos[cp])*qU[line] <= (C[line]/Sb)*(cpSin[cp-1]*(cpCos[cp-1]-cpCos[cp]) - cpCos[cp-1] * (cpSin[cp-1] - cpSin[cp]));
	
subto MinVoltageU:
	forall <n> in Ns :
		Vmin[n]-zetaU[n] <= eU[n];

subto NEVoltageBoundU:
	forall <n,cp> in Ns*cps:
		(cpSin[cp]-cpSin[cp-1])*eU[n]+(cpCos[cp-1]-cpCos[cp])*fU[n] <= (Vmax[n]+nuU[n])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);

subto SEVoltageBoundU:
	forall <n,cp> in Ns*cps:
		(cpSin[cp]-cpSin[cp-1])*eU[n]-(cpCos[cp-1]-cpCos[cp])*fU[n] <= (Vmax[n]+nuU[n])*(cpSin[cp]*cpCos[cp-1] - cpCos[cp]*cpSin[cp-1]);
