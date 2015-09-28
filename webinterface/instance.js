/**
* This file contains the code relative to the instance generation interface.
*/

// General parameters
/** List of available network names. */
var networks=["bus75","example","example2","ylpic"];
/** Predefined interaction models parameters. */
var interactionModels=[
{name:"Unrestricted", accessRestriction:"none", accessBoundsComputation:"installed", DSOIsFSU:false, DSOFlexCost:"normal",DSOImbalancePriceRatio:100,productionFlexObligations:0,consumptionFlexObligations:0,relativeDeviation:0.1},
{name:"Imbalance paid", accessRestriction:"flexible", accessBoundsComputation:"installed", DSOIsFSU:true, DSOFlexCost:"imbalance",DSOImbalancePriceRatio:100,productionFlexObligations:0,consumptionFlexObligations:0,relativeDeviation:0.1},
{name:"Activation paid", accessRestriction:"flexible", accessBoundsComputation:"installed", DSOIsFSU:true, DSOFlexCost:"normal",DSOImbalancePriceRatio:100,productionFlexObligations:0,consumptionFlexObligations:0,relativeDeviation:0.1},
{name:"Market-based", accessRestriction:"none", accessBoundsComputation:"installed", DSOIsFSU:true, DSOFlexCost:"normal",DSOImbalancePriceRatio:100,productionFlexObligations:0,consumptionFlexObligations:0,relativeDeviation:0.1},
{name:"Restricted", accessRestriction:"conservative", accessBoundsComputation:"installed", DSOIsFSU:false, DSOFlexCost:"normal",DSOImbalancePriceRatio:100,productionFlexObligations:0,consumptionFlexObligations:0,relativeDeviation:0.1},
{name:"Dynamic", accessRestriction:"dynamic", accessBoundsComputation:"installed", DSOIsFSU:true, DSOFlexCost:"normal",DSOImbalancePriceRatio:100,productionFlexObligations:0,consumptionFlexObligations:0,relativeDeviation:0.1},
{name:"Dynamic baseline", accessRestriction:"dynamicBaseline", accessBoundsComputation:"installed", DSOIsFSU:true, DSOFlexCost:"normal",DSOImbalancePriceRatio:100,productionFlexObligations:0,consumptionFlexObligations:0,relativeDeviation:0.1}
];

/** Activate or deactive elements for edition or reading mode.
* @param activate Activate the edition mode if true. If false, allows only reading.
*/
function editionMode(activate) {
	var form=document.instanceForm;
	$(form).find(":input").each(function() {
		if ($(this).prop('type')==="number"||$(this).prop('type')==="text") {
			// Text & number input
			$(this).prop('readonly', !activate);
		}
		else if ($(this).prop('type')==="select-one") {
			// Select elements
			if (activate) {
		        $(this).removeAttr('disabled');
		    } else {
		        $(this).attr('disabled', 'disabled');
		    }
		}
		else if ($(this).prop('type')==="button") {
		    $(this).removeAttr('disabled');
		}
	});
			
	// Show or hide some elements
	$('#sendInstanceGenerationRequest').toggle(activate);
	$('#generationDateLine').toggle(!activate);
	$('#instanceDelete').toggle(!activate);
}

/** Load an instance from XML data.
* @param xmlData Plain text XML data.
*/
function loadXMLInstance(xmlData) {
	editionMode(xmlData === undefined);
	$("#hashLine").toggle(!(xmlData === undefined));
	$("#statusLine").toggle(!(xmlData === undefined));
	if (xmlData === undefined) {
		$("#simulateInstance").hide();
		$("#resetInstance").hide();
		$("#generateInstance").show();
		$("#dailyResultsTab").hide();
		$("#globalResultsTab").hide();
	}
	else {
		var form=document.instanceForm;
		var xml = $($.parseXML(xmlData));

		var hash=xml.find("hash").text();
		$("#hashField").html(hash);
		document.getElementById("instanceSelect").value=hash;

		$("#generationDateOutput").html(xml.find("date").text());
		form.title.value=xml.find("title").text();
		form.description.value=xml.find("description").text();
		form.network.value=xml.find("network").text();
		$(form.network).trigger("change"); // Trigger the onchange event
		form.periods.value=xml.find("periods").text();
		form.producersNumber.value=xml.find("producers").text();
		form.retailersNumber.value=xml.find("retailers").text();

		// Production
		var productionTag=xml.find("production");
		form.meanProduction.value=productionTag.find("mean").text();
		form.maxProduction.value=productionTag.find("max").text();
		form.flexProduction.value=productionTag.find("flexibility").text()*100.0;
		form.producersExternalImbalance.value=productionTag.find("externalimbalance").text()*100.0;

		// Consumption
		var consumptionTag=xml.find("consumption");
		form.meanConsumption.value=consumptionTag.find("mean").text();
		form.maxConsumption.value=consumptionTag.find("max").text();
		form.flexConsumption.value=consumptionTag.find("flexibility").text()*100.0;
		form.retailersExternalImbalance.value=consumptionTag.find("externalimbalance").text()*100.0;
		form.retailersFlexReservationCost.value=consumptionTag.find("flexreservationcost").text();

		// Prices
		var pricesTag=xml.find("prices");
		form.meanPrice.value=pricesTag.find("mean").text();
		form.maxPrice.value=pricesTag.find("max").text();

		var dayTag=xml.find("days");
		dayStart=Number(dayTag.find("start").text());
		dayEnd=Number(dayTag.find("end").text()-1);
		form.dayStart.value=dayStart;
		form.dayEnd.value=dayEnd;

		dayResultsSelect=document.getElementById('dayResultsSelect');
		$(dayResultsSelect).empty();
		for (i=dayStart; i<=dayEnd; ++i) {
			var option = document.createElement('option');
			option.text = i;
			dayResultsSelect.add(option);
		}

		// TSO
		var tsoTag=xml.find("tso");
		form.tsoFlexibilityRequest.value=tsoTag.find('flexibilityrequest').text();
		form.tsoReservationPrice.value=tsoTag.find('reservationprice').text();

		// interaction model
		im=xml.find("im");
		$(im).children().each(function() {
			$('#'+$(this).attr('id')).val($(this).text());
		});
		findInteractionModel();

		// Status
		var statusTag=xml.find("status");
		var status="";
		if (statusTag) {
			status=statusTag.text().trim().toLowerCase();
		}
		$("#statusField").html(status);
		$("#simulateInstance").toggle(status === "" || status === "generated" || status === "reset simulation" || status.indexOf("error instance simulation") === 0);
		$('#resetInstance').toggle(status === "simulated");
		$("#generateInstance").toggle(status === "error instance generation");
		$("#dailyResultsTab").toggle(status === "simulated");
		if (status !== "simulated" && ($("#dailyResultsContent").is(":visible") || $("#globalResultsContent").is(":visible"))) {
			$("#instanceTabLink").click();
		}

		// Global results
		$("#globalResultsTab").toggle(status === "simulated");
		if (status == "simulated") {
			requestHandlers.push({handler:getGlobalResults,hash:hash});
			callNextRequest();
		}
	}
}

/** Build instance parameters request
* @return String with the xml content.
*/
function buildXMLInstance() {
	var form=document.instanceForm;
	var request="";

	var date=(new Date).toUTCString();
	var challenge=date+form.title.value
				+form.network.value
				+form.periods.toString()
				+form.meanProduction.value.toString()
				+form.maxProduction.value.toString()
				+form.flexProduction.value.toString()
				+form.meanConsumption.value.toString()
				+form.maxConsumption.value.toString()
				+form.flexConsumption.value.toString()
				+form.meanPrice.value.toString()
				+form.maxPrice.value.toString();
	var hash=hashFnv32a(challenge,true);

	request+='<?xml version="1.0" encoding="ISO-8859-1" ?>\n<xml>\n';
	request+='<hash>'+hash+'</hash>\n';
	request+='<date>'+date+'</date>\n';
	request+='<title>'+form.title.value.replace(';',',')+'</title>\n';
	request+='<description>\n'+form.description.value+'\n</description>\n';
	request+='<network>'+form.network.value+'</network>\n';
	request+='<periods>'+form.periods.value+'</periods>\n';
	request+='<producers>'+form.producersNumber.value+'</producers>\n';
	request+='<retailers>'+form.retailersNumber.value+'</retailers>\n';

	request+='<production>\n';
	request+='\t<mean>'+form.meanProduction.value+'</mean>\n\t<max>'+form.maxProduction.value+'</max>\n';
	request+='\t<flexibility>'+(form.flexProduction.value)/100.0+'</flexibility>\n';
	request+='\t<costs>'+form.costProduction.value+'</costs>\n';
	request+='\t<externalimbalance>'+(form.producersExternalImbalance.value/100.0)+'</externalimbalance>\n';
	request+='</production>\n';

	request+='<consumption>\n';
	request+='\t<mean>'+form.meanConsumption.value+'</mean>\n\t<max>'+form.maxConsumption.value+'</max>\n';
	request+='\t<flexibility>'+(form.flexConsumption.value)/100.0+'</flexibility>\n';
	request+='\t<benefits>'+form.benefitsConsumption.value+'</benefits>\n';
	request+='\t<externalimbalance>'+(form.retailersExternalImbalance.value/100.0)+'</externalimbalance>\n';
	request+='\t<flexreservationcost>'+form.retailersFlexReservationCost.value+'</flexreservationcost>\n';
	request+='</consumption>\n';

	request+='<prices>\n\t<mean>'+form.meanPrice.value+'</mean>\n\t<max>'+form.maxPrice.value+'</max>\n</prices>\n';

	dayEnd=Number(form.dayEnd.value)+1;
	if (dayEnd < form.dayStart.value+1) {
		dayEnd=Number(form.dayStart.value)+1;
	}
	request+='<days>\n\t<start>'+form.dayStart.value+'</start>\n\t<end>'+dayEnd+'</end>\n</days>\n';

	request+='<tso>\n';
	request+='\t<flexibilityrequest>'+form.tsoFlexibilityRequest.value+'</flexibilityrequest>\n';
	request+='\t<reservationprice>'+form.tsoReservationPrice.value+'</reservationprice>\n';
	request+='</tso>\n';

	request+='<im>\n';
	// Iterate over the parameters of the interaction model.
	for (var p in interactionModels[0]) {
		if (p === "name") {
			continue;
		}
		else {
			request+='\t<parameter id="'+p+'">'+$('#'+p).val()+'</parameter>\n';
		}
	}
	request+='</im>\n';

	request+='</xml>\n';
	return request;
}

/** Set the default parameters of the instance generation. */
function setDefaultParameters() {
	var form=document.instanceForm;

	// Add networks options
	networkSelect=form.network;
	$(networkSelect).empty();
	$(networks).each(function() {
		var option = document.createElement('option');
		option.text = this;
		networkSelect.add(option);
	});
	updateNetworkImage();

	// Other parameters
	form.periods.value=24;

	form.producersNumber.value=2;
	form.meanProduction.value=12.5;
	form.maxProduction.value=50;
	form.flexProduction.value=100.0;
	form.costProduction.value=-65+20; // -subsidies+maintenance cost
	form.producersExternalImbalance.value=1;

	form.retailersNumber.value=3;
	form.retailersFlexReservationCost.value=5;
	form.meanConsumption.value=5;
	form.maxConsumption.value=9.2;
	form.flexConsumption.value=20.0;
	form.benefitsConsumption.value=60.5;
	form.retailersExternalImbalance.value=1;

	form.meanPrice.value=47.45;
	form.maxPrice.value=82.3;

	form.dayStart.value=42;
	form.dayEnd.value=42;

	form.tsoFlexibilityRequest.value=3;
	form.tsoReservationPrice.value=45;

	// Create the interaction model select options
	imSelect=form.interactionModelSelect;
	$(imSelect).empty();
	var option = document.createElement('option');
	option.text = "Custom";
	option.value = "custom";
	imSelect.add(option);
	for (var im of interactionModels) {
		option = document.createElement('option');
		option.text = im.name;
		option.value = im.name;
		imSelect.add(option);
	}
	form.interactionModelSelect.value=interactionModels[0].name;
	updateInteractionModel();
}

/** Update the interaction model parameters. **/
function updateInteractionModel() {
	var form=document.instanceForm;
	var model=form.interactionModelSelect.value;
	for (var im of interactionModels) {
		if (im.name === model) {
			for (var p in im) {
				if (p === "name") {
					continue;
				}
				else {
					$('#'+p).val(''+im[p]);
				}
			}
			return;
		}
	}

	// Should return before this point.
	console.log('Interaction model "'+model+'" not found.');
}

/** Select the interaction model which corresponds to the given parameters.**/
function findInteractionModel() {
	for (var im of interactionModels) {
		var match=true;
		for (var p in im) {
			if (p !== "name" && ''+im[p] !== $('#'+p).val()) {
				match=false;
				break;
			}
		}

		if (match) {
			document.instanceForm.interactionModelSelect.value=im.name;
			return;
		}
	}
	document.instanceForm.interactionModelSelect.value="custom";
}

/** Update the network image in the div instancePicture. **/
function updateNetworkImage() {
	var netImage='webinterface/networks/'+document.instanceForm.network.value+'-image.svg';
	document.getElementById('instancePicture').data=netImage;
	document.getElementById('xmlImage').data=netImage;
}

// On page loading
$(document).ready(function() {
	setDefaultParameters();

	$(document.instanceForm.network).on('change',updateNetworkImage);

	$(document.instanceForm.interactionModelSelect).on('change',updateInteractionModel);
	// If we change one parameter, go to the custom mode.
	for (var p in interactionModels[0]) {
		if (p!=="name") {
			$('#'+p).change(function(){findInteractionModel();});
		}	
	}

	loadXMLInstance();
});
