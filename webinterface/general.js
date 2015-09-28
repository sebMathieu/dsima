/**
*This file contains the general javascript code.
**/

/** Log content string variable.*/
var logVar="Loading...\n";

/** Display logging information.
* @param str Content to log.
*/
function log(str) {
	logVar+=str+"\n";
	console.log(str);

	var logOutput = $("#logOutput");
	logOutput.html('<pre>'+$('<div/>').text(logVar).html()+'</pre>');
	logOutput.scrollTop(logOutput[0].scrollHeight);
}

/** Tabs activation. Sources: http://www.jacklmoore.com/notes/jquery-tabs/ */
function activateTabs() {
	$('.tabs').each(function () {
		// For each set of tabs, we want to keep track of
		// which tab is active and it's associated content
		var $active, $content, $links = $(this).find('a');
		// If the location.hash matches one of the links, use that as the active tab.
		// If no match is found, use the first link as the initial active tab.
		$active = $($links.filter('[href="' + location.hash + '"]')[0] || $links[0]);
		$active.addClass('active');
		$content = $($active[0].hash);

		// Hide the remaining content
		$links.not($active).each(function () {
			$(this.hash).hide();
		});

		// Bind the click event handler
		$(this).on('click', 'a', function (e) {
			// Make the old tab inactive.
			$active.removeClass('active');
			$content.hide();
			// Update the variables with the new link and content
			$active = $(this);
			$content = $(this.hash);
			// Make the tab active.
			$active.addClass('active');
			$content.show();
			// Prevent the anchor's default click action
			e.preventDefault();
		});
	});
}

/** Activate the togglers */
function activateTogglers() {
	$('.toggler').each(function () {
		var hash=$(this).prop("hash");
		$(hash).hide();
		$(this).click(function() {$(hash).toggle();});
	});
}

/**
 * Calculate a 32 bit FNV-1a hash
 * Source: http://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript-jquery
 * Found here: https://gist.github.com/vaiorabbit/5657561
 * Ref.: http://isthe.com/chongo/tech/comp/fnv/
 *
 * @param str String with the input value.
 * @param asString Boolean [asString=false] set to true to return the hash value as
 *     8-digit hex string instead of an integer.
 * @param seed Seed optionally pass the hash of the previous chunk.
 * @returns An integer or a string.
 */
function hashFnv32a(str, asString, seed) {
    /*jshint bitwise:false */
    var i, l,
        hval = (seed === undefined) ? 0x811c9dc5 : seed;

    for (i = 0, l = str.length; i < l; i++) {
        hval ^= str.charCodeAt(i);
        hval += (hval << 1) + (hval << 4) + (hval << 7) + (hval << 8) + (hval << 24);
    }
    if( asString ){
        // Convert to 8 digit hex string
        return ("0000000" + (hval >>> 0).toString(16)).substr(-8);
    }
    return hval >>> 0;
}

// On load
$(document).ready(function(){
	activateTabs();
	activateTogglers();
	log("Loaded.");
});
