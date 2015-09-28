# Parameters
param T := read "retailer.dat" as "1n" use 1 comment "#";
set Ts := {1..T};
param piV := read "retailer.dat" as "3n" use 1 comment "#";

set Ns := {read "retailer.dat" as "<n+>" skip 1 use 1 comment "#"};
param N := card(Ns);

param pMin[Ns*Ts] := read "retailer.dat" as "<1n,2n> 3n" skip 2 use (N*T) comment "#";
param pMax[Ns*Ts] := read "retailer.dat" as "<1n,2n> 4n" skip 2 use (N*T) comment "#";

param V[Ns] := read "retailer.dat" as "<1n> 2n" skip (2+N*T) use N comment "#";

param EPS := read "prices.csv" as "2n" use 1 comment "#";
param pii := read "prices.csv" as "3n" use 1 comment "#";
param dt := read "prices.csv" as "4n" use 1 comment "#";
param piE[Ts] := read "prices.csv" as "<1n> 2n" skip 1 use T comment "#";
param piIP[Ts] := read "prices.csv" as "<1n> 3n" skip 1 use T comment "#";
param piIM[Ts] := read "prices.csv" as "<1n> 4n" skip 1 use T comment "#";

param alpha[Ns*Ts] := read "flexObligations.dat" as "<1n,2n> 3n" skip 2 use (N*T) comment "#";
param beta[Ns*Ts] := read "flexObligations.dat" as "<1n,2n> 4n" skip 2 use (N*T) comment "#";
param d[Ns*Ts] := read "flexObligations.dat" as "<1n,2n> 5n" skip 2 use (N*T) comment "#";
param D[Ns*Ts] := read "flexObligations.dat" as "<1n,2n> 6n" skip 2 use (N*T) comment "#";

param k[Ns] := read "flexObligations.dat" as "<1n> 2n" skip 2+(N*T) use N comment "#";
param K[Ns] := read "flexObligations.dat" as "<1n> 3n" skip 2+(N*T) use N comment "#";
param l[Ns] := read "flexObligations.dat" as "<1n> 4n" skip 2+(N*T) use N comment "#";
param L[Ns] := read "flexObligations.dat" as "<1n> 5n" skip 2+(N*T) use N comment "#";

param piFP[Ns*Ts] := read "flexIndicators.dat" as "<1n,2n> 3n" skip 2 use (N*T) comment "#";
param piFM[Ns*Ts] := read "flexIndicators.dat" as "<1n,2n> 4n" skip 2 use (N*T) comment "#";

# Variables
var Pa[Ts] >= -infinity;
var P[Ts] >= -infinity;
var i[<n,t> in Ns*Ts] >= -infinity;
var iP[<n,t> in Ns*Ts] >= 0;
var iM[<n,t> in Ns*Ts] >= 0;
var id[Ns*Ts] >= 0;
var iD[Ns*Ts] >= 0;
var I[Ts] >= -infinity;
var IP[Ts] >=0;
var IM[Ts] >=0;
var fP[Ns*Ts] >=0;
var fM[Ns*Ts] >=0;
var p[<n,t> in Ns*Ts] >= max(pMin[n,t],k[n]) <= min(pMax[n,t],K[n]);
var pP[<n,t> in Ns*Ts] >= max(pMin[n,t],k[n]) <= min(pMax[n,t],K[n]);
var pM[<n,t> in Ns*Ts] >= max(pMin[n,t],k[n]) <= min(pMax[n,t],K[n]);
var pa[<n,t> in Ns*Ts] >= k[n] <= K[n];
var obligations[Ns] >= 0;

# Objective
maximize profit: 
	sum <t> in Ts : (
			-piV*P[t]+piE[t]*Pa[t]
			-piIP[t]*IP[t]-piIM[t]*IM[t]
			+sum <n> in Ns: (
				piFP[n,t]*fP[n,t]
				+piFM[n,t]*fM[n,t] 
				- EPS*(iP[n,t]+iM[n,t])
				- pii*(id[n,t]+iD[n,t])
			)							  
		);
								  
# Constraints
subto TotalProductionAnnounced:
	forall <t> in Ts : 
		Pa[t] == sum <n> in Ns: pa[n,t];
		
subto TotalProduction:
	forall <t> in Ts : 
		P[t] == sum <n> in Ns: p[n,t];
	
subto TotalImbalance:
	forall <t> in Ts :
		I[t] == P[t]-Pa[t];
	
subto TotalUpwardImbalance:
	forall <t> in Ts :
		IP[t] >= I[t];
		
subto TotalDownwardImbalance:
	forall <t> in Ts :
		IM[t] >= -I[t];

subto FlexPdef:
	forall <n,t> in Ns*Ts:
		fP[n,t]<=pP[n,t]-pa[n,t];

subto FlexMdef:
	forall <n,t> in Ns*Ts:
		fM[n,t]<=pa[n,t]-pM[n,t];
		
subto DownwardFlexObligations:
	forall <n,t> in Ns*Ts:
		fM[n,t] >= obligations[n];
		
subto UpwardFlexObligations:
	forall <n,t> in Ns*Ts:
		fP[n,t] >= obligations[n];
		
subto ObligationFromMax:
	forall <n,t> in Ns*Ts:
		obligations[n] >= max(alpha[n,t],beta[n,t])*(pMax[n,t]-pMin[n,t]);
		
subto ObligationFromMin:
	forall <n,t> in Ns*Ts:
		obligations[n] >= max(alpha[n,t],beta[n,t])*(pMax[n,t]-pMin[n,t]);
				
subto ObligationFroml:
	forall <n,t> in Ns*Ts:
		obligations[n] >= l[n] - pa[n,t];
		
subto ObligationFromL:
	forall <n,t> in Ns*Ts:
		obligations[n] >= pa[n,t] - L[n];
		
subto flexAccesL:
	forall <n,t> in Ns*Ts:
		pM[n,t] <= L[n];
		
subto flexAccesl:
	forall <n,t> in Ns*Ts:
		l[n] <= pP[n,t];
		
subto NodeBalance:
	forall <n,t> in Ns*Ts:
		pa[n,t]+i[n,t]==p[n,t];

subto UpwardNodeImbalance:
	forall <n,t> in Ns*Ts:
		iP[n,t] >= i[n,t];
		
subto DownwardNodeImbalance:
	forall <n,t> in Ns*Ts:
		iM[n,t] >= -i[n,t];
		
subto TotalConso:
	forall <n> in Ns:
		V[n] == sum <t> in Ts: p[n,t]*dt;

subto DynamicDownwardRestriction:
	forall <n,t> in Ns*Ts:
		id[n,t] >= d[n,t]-p[n,t];

subto DynamicUpwardRestriction:
	forall <n,t> in Ns*Ts:
		iD[n,t] >= p[n,t]-D[n,t];

subto DynamicDownwardRestrictionM:
	forall <n,t> in Ns*Ts:
		id[n,t] >= d[n,t]-pM[n,t];

subto DynamicUpwardRestrictionP:
	forall <n,t> in Ns*Ts:
		iD[n,t] >= pP[n,t]-D[n,t];
		