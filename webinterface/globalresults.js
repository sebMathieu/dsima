/** Global results xml document. **/
var globalResults=null;

/** List of global attributes to display.*/
var globalAttributes=["Welfare",
			"",
			"Protections cost",
			"DSOs costs",
			"TSOs surplus",
			"Producers surplus",
			"Retailers surplus",
			"",
			"Total production",
			"Total consumption",
			"",
			"Total imbalance",
			"Max. imbalance",
			"Total usage of flex.",
			"Total opp. usage of flex.",
			"Total energy shed"
			];


/** Format a number to have 2 fixed decimals.
* @param v Number to format.
*/
function fixedFormat(v) {
	return (Math.round(v*100)/100).toFixed(2);
}

/** Build the daily results chart of the global results. **/
function buildDailyResultsChart() {
	targetContainer=document.getElementById('dailyResultsChart');
	if (targetContainer != null) {
		timedataId=document.getElementById('dailyResultsChartSelect').value;

		// Retrieve data
		xmlElement=$(globalResults).find('dayresults > timedata[id="'+timedataId+'"]')[0];
		var dataList=[$(xmlElement).text().split(',')];
		var labelList=[timedataId];

		createLineChart(targetContainer,dataList,labelList,null,$(xmlElement).attr('unit'));
	}
}

/** Display the global results.
* @param xmlData XML data with the global results.
**/
function displayGlobalResults(xmlData) {
	var xmlDoc = $($.parseXML(xmlData)).children()[0];
	globalResults=xmlDoc;

	// General results
	var htmlContent="<h2>General results</h2>";
	htmlContent+='<table><col width="30%"><col width="20%"><col width="20%"><col width="20%"><col width="20%">';
	htmlContent+='<thead><tr><th></th><th colspan="3">Value</th><th></th></tr>';
	htmlContent+='<tr><td></td><td class="subtitle">min</td><td class="subtitle">mean</td><td class="subtitle">max</td><td></td></tr></thead><tbody>';
	for (var a of globalAttributes) {
		if (a === "") {
			htmlContent+='<tr><td class="property">&nbsp;</td><td class="number"></td><td class="number"></td><td class="number"></td><td class="unit"></tr>';
		}
		else {
			xmlElement=$(xmlDoc).find('> attributes > attribute[id="'+a+'"]')[0];
			if (a === "Welfare"){
				htmlContent+='<tr class="highlight">';
			}
			else if (a === "Protections cost" && xmlElement === undefined) { // Retrocompatibility
				xmlElement=$(xmlDoc).find('> attributes > attribute[id="Shedding costs"]')[0];
			}
			else{
				htmlContent+='<tr>';
			}
			htmlContent+='<td class="property">'+a+'</td>';
			htmlContent+='<td class="number">'+fixedFormat($(xmlElement).find('min').text())+'</td>';
			htmlContent+='<td class="number">'+fixedFormat($(xmlElement).find('mean').text())+'</td>';
			htmlContent+='<td class="number">'+fixedFormat($(xmlElement).find('max').text())+'</td>';
			htmlContent+='<td class="unit">'+$(xmlElement).attr("unit")+'</td>';
			htmlContent+='</tr>';
		}
	}
	htmlContent+='</tbody></table>';

	// Daily results graphs
	htmlContent+='<h2>Daily results <select id="dailyResultsChartSelect" onChange="buildDailyResultsChart()"  onResize="buildDailyResultsChart()">';
	$(xmlDoc).find('> dayresults > timedata').sort(
		function(a,b){return $(a).attr("id").localeCompare($(b).attr("id"));}
		).each(function() {
		htmlContent+='<option>'+$(this).attr('id')+'</option>';
	});
	htmlContent+='</select></h2><div id="dailyResultsChart"></div>';

	// Actor costs
	htmlContent+='<h2>Actors costs</h2>';
	htmlContent+='<table><col width="30%"><col width="20%"><col width="20%"><col width="20%"><col width="20%">';
	htmlContent+='<thead><tr><th></th><th colspan="3">Value</th><th></th></tr>';
	htmlContent+='<tr><td></td><td class="subtitle">min</td><td class="subtitle">mean</td><td class="subtitle">max</td><td></td></tr></thead><tbody>';
	$(xmlDoc).find('> actors > actor').sort(
		function(a,b){return $(a).attr("id").localeCompare($(b).attr("id"));}
		).each(function() {
		htmlContent+='<tr><td class="property">'+$(this).attr("id")+'</td>';
		htmlContent+='<td class="number">'+fixedFormat($(this).find('min').text())+'</td>';
		htmlContent+='<td class="number">'+fixedFormat($(this).find('mean').text())+'</td>';
		htmlContent+='<td class="number">'+fixedFormat($(this).find('max').text())+'</td>';
		htmlContent+='<td class="unit">'+$(this).attr("unit")+'</td>';
		htmlContent+='</tr>';
	});
	htmlContent+='</tbody></table>';

	// Set the content
	$('#globalResultsContent').html(htmlContent);

	$('#dailyResultsChartSelect').val('Welfare');
	buildDailyResultsChart();
}

