var messages = {};

//Deal with the errors
function displayError(text){
	$('.error').text(text);
	$('.error:hidden').show();
}
function hideError(){
	$('.error:visible').hide();
	$('.error').text('');
}

//FROM http://ad1987.blogspot.com/2010/04/howto-create-facebook-status-message.html
function stripHTML(source){
	var strippedText = source.replace(/<\/?[^>]+(>|$)/g, "");
	return strippedText
}
function replaceURLWithHTMLLinks(source) {
	var exp = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    replaced = source.replace(exp,"<a href='$1' target='_blank'>$1</a>"); 
	return replaced;
}


// Deal With the shares
function add_to_db(message){
	d = {};
	d['timestamp'] = $('#sharebox input[name=timestamp]').val();
	d['security_hash'] = $('#sharebox input[name=security_hash]').val();
	d['title'] = $('#sharebox input[name=title]').val();
	d['message'] = message;
	$.ajax({
		  type: 'POST',
		  url: '/ajax',
		  data: d,
		  success: function(json){if (window.console && window.console.firebug) console.log(json.error);},
		  dataType: 'json'
	});
	$('#sharebox .sharebutton').attr('disabled', false);
	$('#sharebox .sharecontent').val('');
}

//Add the message to to the share list
function add_to_shares(message, embed){
	var post = '<li><p>'+replaceURLWithHTMLLinks(message)+'</p>';
	if (embed != null)
		post += embed;
	post += '</li>';
	$('#shares').prepend(post);
	add_to_db(message);
}

$(document).ready(function() {
	//Bind Handler
	$('#sharebox .sharebutton').bind('click', function(e){
		e.preventDefault();
		hideError();
		var text = stripHTML($('#sharebox .sharecontent').val());
		
		//If there is no content in the box just return.
		if (!text || !text.replace(/\s/g, ''))
			return false
		
		//Simple check to see if the user already posted that link.
		if (text in messages){
			displayError("You already posted that, be orginal.")
			return false
		} else {
			messages[text] = '';
		}
		//Disable the share button
		$('#sharebox .sharebutton').attr('disabled', true);
		
		// Fins all the urls in the post
		var exp = /(\bhttp:\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
		var urls = text.match(exp);
		// We only want one link.
		if (urls != null && urls.length > 1){
			displayError("You only get to post one link. Sorry.")
			return false
		}else if(urls != null){
			//Call Embedly
			$.embedly(urls[0], {maxWidth: 480, wrapElement: 'div', method : "afterParent"  }, function(oembed){
				if (oembed != null)
					add_to_shares(text, oembed.code);
				else
					add_to_shares(text)
			});
		} else {
			//No Url just add the text.
			add_to_shares(text, null);
		}
	});
	//Deal with the links already on the page.
	$('#shares').embedly({maxWidth: 480, wrapElement: 'div', method : "afterParent" });
	//Clear on Focus
	$('#sharebox .sharecontent').bind('focus', function(e){if ($(this).val().indexOf('Post a link') === 0)$(this).val('');});
	//Make sure the button doesn't stay disabled. 
	$('#sharebox .sharebutton').attr('disabled', false);
	
});