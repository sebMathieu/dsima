/**
* display
* Link the data and the svg display.
*/

/** Parsed xml data. */
var xml = null;
/** Current period. */
var t=-1;
/** Total number of periods. */
var T=0;
/** First index of periods.*/
var PERIOD_START=1;
/** Popup box element pointer.*/
var popupBox=null;

/**
* Parse and format to 2 decimals the text is a float.
* @param text Text to format.
* @return String.
*/
function formatIfFloat(text) {
	if (/^-?(0|[1-9]\d*|(?=\.))(\.\d+)?$/.test(text)) {
		text=""+parseFloat(text).toFixed(2);
	}
	return text;
}

/**
* Build the display.
* The display includes the information popups for the nodes and the update of the image.
*/
function buildDisplay() {
	var image = document.getElementById("xmlImage");
	var svgTree = image.contentDocument;
	var svgContent = $($(svgTree).children()[0]).children()[0];

	// SVG elements
	var generalElements=$(xml).find('elements')[0];
	$(svgContent).children().each(function() {
		if ($(this).prop("tagName").toLowerCase() === "g") {
			associate(this,generalElements);
		}
	});

	$('#imageSVGLink').click(function() {
		var XMLS = new XMLSerializer();
		var svgText=XMLS.serializeToString(svgTree);
		console.log(svgText);
		open("data:image/svg+xml," + encodeURIComponent(svgText));
	});

	displayGeneralText();
}

/**
* Build and display the general (non element-specific) text.
*/
function displayGeneralText() {
	var generalXML=$(xml).find('> general')[0];
	var generalContent="<h2>General</h2>";

	// External elements
	var externalElements=$(xml).find('> externals')[0];
	var externalIds=[];
	if (externalElements != null) {
		generalContent+="<h3>External elements</h3>";
		$(externalElements).find('> element').each(function(){
			var id=$(this).attr("id");
			externalIds.push(id);
			generalContent+='<a href="#" class="externalElementLink" id="'+id+'">'+$(this).attr("name")+'</a>';
		});
	}

	// Attributes
	var data=$(generalXML).find('> data');
	if (data.length > 0) {
		generalContent+="<h3>Data</h3><table>";
		$(data).each(function() {
			generalContent+="<tr><th>"+$(this).attr("id")+"</th><td>"+formatIfFloat($(this).text().trim())+"</td></tr>";
		});
		generalContent+="</table>";
	}

	// Temporal Attributes
	if (t > 0) {
		data=$(generalXML).find('> timedata');
		if (data.length > 0) {
			generalContent+="<h3>Time-related data</h3><table>";
			$(data).each(function() {
				generalContent+="<tr><th>"+$(this).attr("id")+"</th><td>"+formatIfFloat($(this).text().trim().split(",")[t])+"</td></tr>";
			});
			generalContent+="</table>";
		}
	}

	// Timegraph
	var timegraphsToRender=[];
	if (t <= 0) {
		var timegraphs=$(generalXML).find('> timegraph');
		if (timegraphs.length > 0) {
			generalContent+="<h3>Time graphs</h3>";
			$(timegraphs).each(function() {
				var chartId="general-"+$(this).attr("id");
				generalContent+='<div class="smallChart" id="'+chartId+'"></div>';
				timegraphsToRender.push(this);
			});
		}
	}

	// Description
	var descriptions=$(generalXML).find('> description');
	if (descriptions.length > 0) {
		generalContent+="<h3>Description</h3>";
		$(descriptions).each(function() {
			generalContent+="<p>"+$(this).text().trim()+"</p>";
		});
	}

	// Set the content
	$("#rightBox").html(generalContent);

	// Create small graphs
	if (t<=0) {
		$(timegraphsToRender).each(function() {
			var chartId="general-"+$(this).attr("id");

			// Retrieve data
			var dataList=[];
			var labelList=[];
			$(this).find('> timegraphdata').each(function() {
				dataList.push($(this).text().trim().split(","));
				labelList.push($(this).attr("id"));
			});

			createLineChart(chartId,dataList,labelList,$(this).attr("title"),$(this).attr("ylabel"));
		});
	}

	// External elements association as the content has been set
	for (var id of externalIds) {
		associate(document.getElementById(id),externalElements);
	}
}

/**
* Create a line chart from data for each periods.
* @param containerId Identification tag of the chart's container.
* @param data List of array with data for each period.
* @param labels List of labels for each data set.
* @param title Chart title.
* @param ylabel Ordinates label.
*/
function createLineChart(containerId,data,labels,title,ylabel) {
	// Create the dataPoints structure
	var chartData=[];
	var i=0;
	$(data).each(function() {
		dataPoints=[];
		var t=PERIOD_START;
		$(this).each(function() {
			dataPoints.push({ x: t, y: this*1.0, label:t});
			dataPoints.push({ x: t+1, y: this*1.0, label:t});
			t+=1;
		});
		chartData.push({type: "stepLine",showInLegend: true,dataPoints: dataPoints,legendText: labels[i]});
		i+=1;
	});

	// Create chart
	var chart = new CanvasJS.Chart(containerId,
	{
		title:{text: ""},
		axisX: {title:"Period"},
		axisY:{title: ylabel},
		data: chartData,
    	legend: {
            cursor: "pointer",
            itemclick: function (e) {
                if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
                    e.dataSeries.visible = false;
                } else {
                    e.dataSeries.visible = true;
                }
                e.chart.render();
            }
        }
	});
	chart.render();
}

/**
* Display the popup text of an xml element.
* @param id Id of the element.
* @param name Name of the element
* @param xmlElement Xml data of the element.
*/
function elementPopupText(id,name,xmlElement) {
	// To render after
	var timegraphsToRender=[];

	var popupText="";

	// Back button
	popupText+='<a href="#" onClick="changeTime('+t+')" class="backLink">Back</a>';
	popupText+='<h2>'+name+'</h2>';

	// Attributes
	var data=$(xmlElement).find('> data');
	if (data.length > 0) {
		popupText+="<h3>Data</h3><table>";
		$(data).each(function() {
			popupText+="<tr><th>"+$(this).attr("id")+"</th><td>"+formatIfFloat($(this).text().trim())+"</td></tr>";
		});
		popupText+="</table>";
	}

	// Temporal Attributes
	if (t > 0) {
		data=$(xmlElement).find('> timedata, > timegraph > timegraphdata');
		if (data.length > 0) {
			popupText+="<h3>Time-related data</h3><table>";
			$(data).each(function() {
				popupText+="<tr><th>"+$(this).attr("id")+"</th><td>"+formatIfFloat($(this).text().trim().split(",")[t-1])+"</td></tr>";
			});
			popupText+="</table>";
		}
	}

	// Timegraph
	if (t <= 0) {
		var timegraphs=$(xmlElement).find('> timegraph');
		if (timegraphs.length > 0) {
			popupText+="<h3>Time graphs</h3>";
			$(timegraphs).each(function() {
				var chartId=id+"-"+$(this).attr("id");
				popupText+='<div class="smallChart" id="'+chartId+'"></div>';
				timegraphsToRender.push(this);
			});
		}
	}

	// Description
	var descriptions=$(xmlElement).find('> description');
	if (descriptions.length > 0) {
		popupText+="<h3>Description</h3>";
		$(descriptions).each(function() {
			popupText+="<p>"+$(this).text().trim()+"</p>";
		});
	}

	// Back button
	popupText+='<a href="#" onClick="changeTime('+t+')" class="backLink">Back</a>';

	// Assign the popup text
	$("#rightBox").html(popupText);

	// Create small graphs
	if (t<=0) {
		$(timegraphsToRender).each(function() {
			var chartId=id+"-"+$(this).attr("id");

			// Retrieve data
			var dataList=[];
			var labelList=[];
			$(this).find('> timegraphdata').each(function() {
				dataList.push($(this).text().trim().split(","));
				labelList.push($(this).attr("id"));
			});

			createLineChart(chartId,dataList,labelList,$(this).attr("title"),$(this).attr("ylabel"));
		});
	}
}

/**
* Try to associate an element (SVG or not) with the data in the provided xml document.
* @param element Element to associate (SVG or not).
* @param xmlData XML data element to look into
*/
function associate(element, xmlData) {
	// Fetch svg id
	var id=$(element).attr("id");

	var xmlElements=$(xmlData).find('> element[id="'+id+'"]');
	if (xmlElements.length > 0) {
		var xmlElement=xmlElements[0];
		var name=$(xmlElement).attr('name');
		if (name === "") {
			name=id;
		}

		// Create the tooltip
		$(element).hover(
			function() {
				// mouse enter
				popupBox.html(name);
			},
			function() {
				// mouse out
				popupBox.html('');
			}
		);

		// Style and text
		$(xmlElement).children().each(function() {
			if ($(this).prop("tagName").toLowerCase() === "timestyle") {
				var timestyles=this;
				var style;
				if (t > 0) {
					var styles=$(timestyles).find('> periods').text().split(',');
					style=styles[t-1];
				}
				else{
					style=$(timestyles).find('> default').text();
				}
				$(element).find('polygon,path').each(function() {
					$(this).attr('style', style);
				});
			}
			else if ($(this).prop("tagName").toLowerCase() === "timetext") {
				var timetexts=this;
				var text="";
				if (t > 0) {
					var texts=$(timetexts).find('> periods').text().split(',');
					text=texts[t-1];
				}
				else {
					text=$(timetexts).find('> default').text();
				}
				$(element).find('> text').each(function() {
					$(this).text(text);
				});
			}
		});

		// Create information
		$(element).click(function() {
			elementPopupText(id,name,xmlElement);
		});
	}
}

/**
* Change the current time period.
* The reference begins at 1, 0 being the genera view.
* @param newt New period.
*/
function changeTime(newt) {
	$('#loading').show(0);

	// Deactivate the old period
	if (t >= 0) {
		document.getElementById("periodLink_"+t).className="inactiveLink";
	}

	// Set the new active period
	t=newt;
	document.getElementById("periodLink_"+t).className="activeLink";

	// Build the new display
	buildDisplay();


	$('#loading').hide();
}

/**
* Display an element in full screen.
* @param id Element id.
*/
function displayFullscreen(id) {
	$('#'+id).addClass("fullScreen");

	$(document).keydown(function(e){
		if (e.keyCode === 27) {
			$('#'+id).removeClass("fullScreen");
			return false;
		}
	});
}

/**
* Build the timeline in the div with id : "timeline".
*/
function buildTimeline() {
	var div = document.getElementById("timeline");
	t=1;

	// Create the html content
	var content='<a class="inactiveLink" id="periodLink_0" onClick="changeTime(0)">General view</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Period : ';

	for (var tau = 1; tau <= T; tau++) {
		content+='<a class="inactiveLink" id="periodLink_'+tau+'" onClick="changeTime('+tau+')" >'+tau+'</a>';
	}

	content+='<a href="#" onClick="displayFullscreen(\'image\')" id="imageFullScreenLink">F</a><a href="#" id="imageSVGLink">SVG</a>';

	$(div).html(content);
}

/**
* Display the daily result given by its xml content.
* @param dataXml XML document with the data.
*/
function displayXML(dataXml) {
	xml=dataXml;
	popupBox=$("#popupBox");

	// Retrieve the number of periods
	T=0;
	$(xml).children().each(function() {
		if ($(this).prop("tagName").toLowerCase() === "periods") {
			T=parseInt($(this).text());
			return false;
		}
	});

	// Prepare the timeline related display
	if (document.getElementById('timeline') != null) {
		buildTimeline();
		changeTime(0);
	}
}

