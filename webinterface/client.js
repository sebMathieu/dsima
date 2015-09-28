/**
* This file contains the javascript client of the engine.
*/

/** Server adress. */
var server="ws://139.165.16.33:8000/"; // ws://localhost:8000/
/** Current websocket. */
var websocket = null;

/** Polling delay in milliseconds. */
var POLLING_DELAY=1000;
/** List of dictionaries. Each dictionary must contain a field "handler" whose value is a function to call.*/
var nextHandlers = [];
/** Requests of non started actions.*/
var requestHandlers=[];
/** True if there is an handler prossessing. */
var isHandlerProcessing=false;

/** Predefined states.
* - SENT : 0
* - WAIT : 1
* - RECEIVED : 2
* - GENERATING : 3
* - POLL : 4
*/
var States={SENT:0,WAIT:1,RECEIVED:2,GENERATING:3,POLL:4};

/** Connection to the server by opening a websocket. **/
function connect() {
	log("Trying to connect to "+server+"...");
	websocket = new WebSocket(server);
	websocket.onopen = function(evt) {
		onOpen(evt);
	};
	websocket.onclose = function(evt) {
		onClose(evt);
	};
	websocket.onmessage = function(evt) {
		onMessage(evt);
	};
	websocket.onerror = function(evt) {
		onError(evt);
	};
}

/** Action when websocket is opened.
* @param evt Event.
**/
function onOpen(evt) {
	log("Connected.");
	$('#connectionButton').prop('value', "Disconnect");
	$('#simulationComputationStatus').removeClass().addClass('unknownStatus');
	callNextRequest();
}

/** Action when websocket is closed.
* @param evt Event.
**/
function onClose(evt) {
	log("Disconnected.");
	$('#connectionButton').prop('value', "Connect");
	$('#simulationComputationStatus').removeClass().addClass('unknownStatus');
	$('#serverTabLink').click();
	websocket=null;
}

/** Action when websocket receive a message.
* @param evt Event.
**/
function onMessage(evt) {
	if (nextHandlers.length === 0) {
		log("Unexpected message received:\n" + evt.data);
	}
	else {
		message=evt.data;

		// Clean message
		if (!(message === undefined) && (typeof message === 'string' || message instanceof String)) {
			message=message.trim().toLowerCase();
		}
		isHandlerProcessing=true;
		handler=nextHandlers.shift();
		handler.message=message;
		handler.handler(handler);
		isHandlerProcessing=false;
	}
}

/** Action when there is an error with the websocket.
* @param evt Event.
**/
function onError(evt) {
	log("Error: " + evt.data);
	$('#simulationComputationStatus').removeClass().addClass('errorStatus');
	websocket.close();
	websocket=null;
}

/** Send a message through the websocket assuming it is connected.
* @param message Message to send.
**/
function send(message) {
	if (websocket != null) {
		websocket.send(message);
	}
	else {
		log("Trying to send a message into a null websocket.");
	}
}

/** Disconnect the websocket if it is existing. **/
function disconnect() {
	nextHandlers=[];
	requestHandlers=[];
	isHandlerProcessing=false;
	if (websocket != null) {
		websocket.close();
	}
}

/** Call the next handler if one exists. **/
function callNextHandler() {
	if (!isHandlerProcessing && nextHandlers.length !== 0) {
		isHandlerProcessing=true;
		var h=nextHandlers.shift();
		h.handler(h);
		isHandlerProcessing=false;
	}
}

/** Call the next handler if there is only one. **/
function callNextRequest() {
	if (requestHandlers.length !== 0 && nextHandlers.length === 0) {
		isHandlerProcessing=true;
		var h=requestHandlers.shift();
		h.handler(h);
		isHandlerProcessing=false;
	}
}

/** Delete an instance from the server.
* Suppose that the state is the hash of the instance to delete.
* @param h Handler dictionary.
**/
function deleteInstance(h) {
	var processFinished=false;

	// State dependent reaction
	if (websocket == null) {
		// Establish a connection
		requestHandlers.push(h);
		connect();
	}
	else if (h.state === undefined && h.hash != null && h.hash !== "new")  {
		// Request the deletion
		log("Request deletion of instance \""+h.hash+"\".");
		h.state=States.WAIT;
		nextHandlers.push(h);
		send("delete instance \""+h.hash+"\"");
	}
	else if (h.state === States.WAIT) {
		if (h.message.indexOf('ok deleted') === 0) {
			log(h.message);

			// First list then, get the instance
			requestHandlers.push({handler:listGeneratedInstances});
			requestHandlers.push({handler:getInstance,hash:"new"});
		}
		else {
			log("Unknown problem when deleting an instance. Message: \n\t"+h.message);
		}
		processFinished=true;
	}
	else {
		log("Unknown problem when deleting an instance. Message: \n\t"+h.message+"\nState: "+h.state);
		processFinished=true;
	}

	if (processFinished) {
		callNextRequest();

	}
}

/** Reset an instance from the server.
* Suppose that the state is the hash of the instance to delete.
* @param h Handler dictionary.
**/
function resetInstance(h) {
	var processFinished=false;

	// State dependent reaction
	if (websocket == null) {
		// Establish a connection
		requestHandlers.push(h);
		connect();
	}
	else if (h.state === undefined && h.hash != null && h.hash !== "new")  {
		// Request the deletion
		log("Request reset of instance \""+h.hash+"\".");
		h.state=States.WAIT;
		nextHandlers.push(h);
		send("reset instance \""+h.hash+"\"");
	}
	else if (h.state === States.WAIT) {
		if (h.message.indexOf('ok reset') === 0) {
			log(h.message);

			// First list then, get the instance
			requestHandlers.push({handler:getInstance,hash:h.hash});
		}
		else {
			log("Unknown problem when reseting an instance. Message: \n\t"+h.message);
		}
		processFinished=true;
	}
	else {
		log("Unknown problem when reseting an instance. Message: \n\t"+h.message+"\nState: "+h.state);
		processFinished=true;
	}

	if (processFinished) {
		callNextRequest();

	}
}

/** Request the instance simulation interaction.
* @param h Handler dictionary.
**/
function requestInstanceSimulation(h) {
	if (websocket == null) {
		// Establish a connection
		requestHandlers.push(h);
		connect();
	}
	else {
		// Ask to simulate an instance
		hash=$("#instanceSelect").val();

		// Reset progress
		var progress=0;
		$('#progressBar').val(progress);
		$('#progressText').html((progress*100).toFixed(2)+' %');

		// Send the request
		log("Request the simulation of "+hash+".");
		nextHandlers.push({handler:instanceSimulation,hash:hash,state:States.WAIT});
		send("instance simulation request \""+hash+"\"");
		$('#progressTabLink').click();
	}
}

/** Instance simulation interaction.
* @param h Handler dictionary.
**/
var disconnectAndRun=false;
function instanceSimulation(h) {
	$('#disconnectRunButton').show();

	if (websocket == null) {
		log("Websocket closed in instance simulation process. Message: \n\t"+h.message);
	}
	else if (h.state === undefined || h.state===States.POLL) { // Poll
		h.state=States.WAIT;
		nextHandlers.push(h);
		send("ready?");
	}
	else if (h.state === States.WAIT) { // Receive server's answer
		// Wait for the instance generation to complete.
		if (h.message.indexOf("ok running") === 0) {
			$('#jobProgressStatus').hide();

			// Polling
			if (disconnectAndRun) {
				log("Ask to run disconnected.");
				nextHandlers.push(h);
				send("run disconnected");
				disconnectAndRun=false;
			}
			else {
				h.state=States.POLL;
				window.setTimeout(function() {
					requestHandlers.push(h);
					callNextRequest();
				},POLLING_DELAY);
			}
		}
		else if (h.message.indexOf("ok waiting") === 0) {
			$('#jobProgressStatus').show();
			$('#jobProgressStatus').html("Job is waiting...");

			// Polling
			if (disconnectAndRun) {
				log("Ask to run disconnected.");
				nextHandlers.push(h);
				send("run disconnected");
				disconnectAndRun=false;

				$('#jobProgressStatus').hide();
				$('#jobProgressStatus').html("");
			}
			else {
				h.state=States.POLL;
				window.setTimeout(function() {
					requestHandlers.push(h);
					callNextRequest();
				},POLLING_DELAY);
			}
		}
		else if (h.message.indexOf("ok instance simulated") === 0) {
			$('#disconnectRunButton').hide();
			log("Instance simulated.");
			requestHandlers.push({handler:getInstance,hash:h.hash});
			callNextRequest();

			// Play sound
			var audio = new Audio('webinterface/end.mp3');
			audio.play();

			$('#instanceTabLink').click();
		}
		else if (h.message.indexOf("ok run disconnected") === 0) {
			$('#disconnectRunButton').hide();
			log("Run disconnected.");
			disconnect();
			callNextRequest();
		}
		else {
			// Play sound
			var audio = new Audio('webinterface/error.mp3');
			audio.play();

			log("Unknown problem in the instance simulation process. Message: \n\t"+h.message);
			disconnect();
			callNextRequest();
		}
	}
}

/** Check if the server agreed to receive the instance parameters and sends it.
* @param h Handler dictionary.
**/
function instanceGeneration(h) {
	var processFinished=false;

	// State dependent reaction
	if (websocket == null) {
		// Establish a connection
		requestHandlers.push(h);
		connect();
	}
	else if (h.state === undefined)  {
		// Ask to generate an instance
		log("Request an instance generation.");
		h.state=States.SENT;
		nextHandlers.push(h);
		send("instance generation request");
		$('#loading').show(0);
	}
	else if (h.state===States.SENT) {
		// Wait for the server to accept to generate an instance.
		if (h.message.indexOf("ok instance generation request") === 0) {
			log(h.message);
			// Send the instance XML file
			h.state=States.RECEIVED;
			nextHandlers.push(h);
			send(buildXMLInstance());
		}
		else {
			log("Server did not accepted the instance generation request. Message :\n\t"+h.message);
			disconnect();
		}
	}
	else if (h.state===States.RECEIVED) {
		// Wait the confirmation of the reception of the instance.
		if (h.message.indexOf("ok instance received") === 0) {
			log(h.message);
			h.state=States.GENERATING;
			nextHandlers.push(h);
			send("ready?");
		}
		else {
			log("Server did not received the instance generation request. Message: \n\t"+h.message);
			disconnect();
		}
	}
	else if (h.state===States.POLL) {
		h.state=States.GENERATING;
		nextHandlers.push(h);
		send("ready?");
	}
	else if (h.state===States.GENERATING) {
		// Wait for the instance generation to complete.
		if (h.message.indexOf("ok running") === 0 || h.message.indexOf("ok waiting") === 0) {
			// Polling
			h.state=States.POLL;
			window.setTimeout(function(){
				requestHandlers.push(h);
				callNextRequest();
			},POLLING_DELAY);
		}
		else if (h.message.indexOf("ok instance generated") === 0) {
			log(h.message);
			hash=h.message.match(/"(\w\w\w\w\w\w\w\w)"/)[1];

			// First list then, get the instance
			requestHandlers.push({handler:listGeneratedInstances});
			requestHandlers.push({handler:getInstance,hash:hash});

			processFinished=true;
		}
		else {
			log("Unknown problem in the instance generation process. Message: \n\t"+h.message);
			processFinished=true;
			disconnect();
			callNextRequest();
		}
	}
	else {
		log("Unknown problem in the instance generation process. Message: \n\t"+h.message);
		processFinished=true;
	}

	if (processFinished) {
		callNextRequest();
		$('#loading').hide();
	}
}

/** List the generated instances by the server.
* @param h Handler dictionary.
**/
function listGeneratedInstances(h) {
	var processFinished=false;

	// State dependent reaction
	if (websocket == null) {
		// Establish a connection
		requestHandlers.push(h);
		connect();
	}
	else if (h === undefined || h.state === undefined)  {
		// Set the list of instances to loading
		var selectElement=$("#instanceSelect")[0];
		$(selectElement).empty();
		var option = document.createElement('option');
		option.text="Loading...";
		selectElement.add(option);

		// Ask to generate an instance
		log("Ask for the list of generated instances");
		h.state=States.WAIT;
		nextHandlers.push(h);
		send("list generated instances");
	}
	else if (h.state === States.WAIT) {
		var selectElement=$("#instanceSelect")[0];
		$(selectElement).empty();

		// Create the new option
		var option = document.createElement('option');
		option.value="new";
		option.text="New...";
		selectElement.add(option);

		// Create an option for each generated instance
		if (h.message !== "") {
			$(h.message.split("\n")).each(function() {
				var args=this.split(";");
				option = document.createElement('option');
				option.value=args[0];
				if (args[1] !== "") {
					option.text = args[0] + " - " + args[1];
				}
				else {
					option.text = args[0];
				}
				selectElement.add(option);
			});
		}
		log("List of generated instances received.");
		processFinished=true;
	}
	else {
		log("Unknown problem in the listing of generated instances. Message: \n\t"+h.message);
		processFinished=true;
	}

	if (processFinished) {
		callNextRequest();

	}
}

/** Get an instance from the server.
* Suppose that the state is the hash of the instance to get.
* @param h Handler dictionary.
**/
function getInstance(h) {
	var processFinished=false;

	// State dependent reaction
	if (websocket == null) {
		// Establish a connection
		requestHandlers.push(h);
		connect();
	}
	else if (h.state === undefined && h.hash != null)  {
		if (h.hash === "new") {
			loadXMLInstance();
		}
		else{
			// Request an instance
			log('Request instance "'+h.hash+'".');
			h.state=States.WAIT;
			nextHandlers.push(h);
			send('get instance "'+h.hash+'"');
		}
	}
	else if (h.state === States.WAIT) {
		if (typeof h.message === "string" && h.message.indexOf("error unknown instance") === 0) {
			log("Instance not found: "+h.message);
		}
		else {
			var reader = new FileReader();
			reader.addEventListener("loadend", function() {
				loadXMLInstance(reader.result);
				log("Instance obtained.");
			});
			reader.readAsText(h.message);
		}
		processFinished=true;

	}
	else {
		log("Unknown problem when fetching an instance. Message: \n\t"+h.message);
		processFinished=true;
	}

	if (processFinished) {
		callNextRequest();

	}
}

/** Get a daily result of an instance from the server.
* Suppose that the hash is provided in the handler dictionary.
* @param h Handler dictionary.
**/
function getDailyResult(h) {
	var processFinished=false;

	// State dependent reaction
	if (websocket == null) {
		// Establish a connection
		requestHandlers.push(h);
		connect();
	}
	else if (h.state === undefined && h.hash != null)  {
		// Request an instance
		log('Request daily result instance "'+h.hash+'" day "'+h.day+'".');
		h.state=States.WAIT;
		nextHandlers.push(h);
		$('#loading').show(0);
		send('get daily result "'+h.hash+'" "'+h.day+'"');
	}
	else if (h.state === States.WAIT && typeof h.message !== "string") {
		var reader = new FileReader();
		reader.addEventListener("loadend", function() {
			log('Daily result instance "'+h.hash+'" day "'+h.day+'" obtained.');
			var zip = new JSZip(reader.result);
			var xmlContent=zip.file(/.xml$/)[0].asText();
			displayXML(xmlContent);
			$('#loading').hide();
		});
		reader.readAsArrayBuffer(h.message);
		processFinished=true;
	}
	else {
		log("Unknown problem when fetching a daily result. Message: \n\t"+h.message);
		processFinished=true;
		$('#loading').hide();
	}

	if (processFinished) {
		callNextRequest();

	}
}

/** Fetch the XML result file with the global result.
* Suppose that the hash is provided in the handler dictionary.
* @param h Handler dictionary.
**/
function getGlobalResults(h) {
	var processFinished=false;

	// State dependent reaction
	if (websocket == null) {
		// Establish a connection
		requestHandlers.push(h);
		connect();
	}
	else if (h.state === undefined && h.hash != null)  {
		// Request an instance
		log('Request global results instance "'+h.hash+'".');
		h.state=States.WAIT;
		nextHandlers.push(h);
		send('get global results "'+h.hash+'"');
	}
	else if (h.state === States.WAIT && typeof h.message !== "string") {
		var reader = new FileReader();
		reader.addEventListener("loadend", function() {
			log('Daily result instance "'+h.hash+'" obtained.');
			var xmlContent=reader.result;
			displayGlobalResults(xmlContent);
		});
		reader.readAsText(h.message);
		processFinished=true;
	}
	else {
		log("Unknown problem when fetching the global result \""+h.hash+"\". Message: \n\t"+h.message);
		processFinished=true;
	}

	if (processFinished) {
		callNextRequest();

	}
}

/** Poll the server to know if it is computing.
* @param h Handler dictionary.
**/
function isComputingSimulation(h) {
	var processFinished=false;

	// State dependent reaction
	if (websocket == null) {
		// Establish a connection
		requestHandlers.push(h);
		connect();
	}
	else if (h.state === undefined || h.state===States.POLL) { // Poll
		h.state=States.WAIT;
		nextHandlers.push(h);
		send("is computing simulation?");
	}
	else if (h.state === States.WAIT) {
		if (h.message.indexOf("is computing simulation") === 0) {
			$('#simulationComputationStatus').removeClass().addClass('runningStatus');

			// Display progression
			var matchedGroups=h.message.match(/is computing simulation with progression ([0-9\.]+) and ([0-9]+) jobs/);
			var progress=matchedGroups[1];
			var jobs=matchedGroups[2];
			if (h.progress === undefined || h.progress < progress-0.01) {
				log('Current job progression: '+(progress*100).toFixed(2)+' %');
				h.progress=progress;
			}
			$('#progressBar').val(progress);
			$('#progressText').html((progress*100).toFixed(2)+' %');
			$('#progressAdditionalInformations').html("Number of additional jobs in the queue: "+jobs);
			$('#progressTab').show();

			// Polling
			h.state=States.POLL;
			window.setTimeout(function(){
				requestHandlers.push(h);
				callNextRequest();
			},POLLING_DELAY);
		}
		else if (h.message.indexOf('is waiting for simulation') === 0) {
			$('#simulationComputationStatus').removeClass().addClass('waitingStatus');
			$('#progressTab').hide();

			// Polling
			h.state=States.POLL;
			window.setTimeout(function(){
				requestHandlers.push(h);
				callNextRequest();
			},POLLING_DELAY);
		}
		else {
			log("Unknown problem when polling simulation computing status. Message: \n\t"+h.message);
		}
		processFinished=true;
	}
	else  {
		log("Unknown problem when polling simulation computing status. Message: \n\t"+h.message);
		processFinished=true;
	}

	if (processFinished) {
		callNextRequest();
	}
}

/** Manage the connection button. **/
function connectionButtonManagement() {
	if (websocket == null) {
		server=$('#server').val();
		requestHandlers.push({handler:listGeneratedInstances});
		callNextRequest();
	}
	else {
		disconnect();
	}
}

// On page loading
$(document).ready(function() {
	// Set the server location if the field is empty
	if ($('#server').prop('value') === "") {
		$('#server').prop('value', server);
	}
	else {
		server=$('#server').prop('value');
	}

	// Reaction to the user's commands
	$('#connectionButton').click(connectionButtonManagement);
	$('#disconnectRunButton').click(function() {
		disconnectAndRun=true;
	});
	$('#generateInstance').click(function(){
		requestHandlers.push({handler:instanceGeneration});
		callNextRequest();
	});
	$('#simulateInstance').click(function() {
		$('#simulateInstance').hide();
		requestHandlers.push({handler:requestInstanceSimulation});
		callNextRequest();
	});
	$('#resetInstance').click(function() {
		hash=$("#instanceSelect").val();
		if (hash !== "new" && confirm("Are you sure to reset instance \""+hash+"\"?")) {
			requestHandlers.push({handler:resetInstance,hash:hash});
			callNextRequest();
		}
	});
	$('#instanceSelect').change(function(){
		hash=$("#instanceSelect").val();
		requestHandlers.push({handler:getInstance,hash:hash});
		callNextRequest();
	});
	$('#instanceDelete').click(function(){
		hash=$("#instanceSelect").val();
		if (hash !== "new" && confirm("Are you sure to delete instance \""+hash+"\"?")) {
			requestHandlers.push({handler:deleteInstance,hash:hash});
			callNextRequest();
		}
	});
	$('#getDailyResultButton').click(function(){
		hash=$("#instanceSelect").val();
		day=$("#dayResultsSelect").val();
		requestHandlers.push({handler:getDailyResult,hash:hash,day:day});
		callNextRequest();
	});

	// Show/hide elements
	$('#progressTab').hide();
	$('#loading').hide();
	$('#disconnectRunButton').hide();

	// First list the generated instances then check the computing status
	requestHandlers.push({handler:isComputingSimulation});
	requestHandlers.push({handler:listGeneratedInstances});
	callNextRequest();
});

// Disconnect if exits
$(window).unload(function() {
	disconnect();
});
