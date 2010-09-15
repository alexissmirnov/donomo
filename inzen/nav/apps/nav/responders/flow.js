require('responders/main');

/** @namespace

  Hanles sender classification commands
  
  @extends SC.Responder
*/
Nav.states.flow = SC.Responder.create({
	// when we become first responder, show classification panel
	didBecomeFirstResponder: function () {	
		var flow = this.get('content');
		
		// conversationsBrowserController will react to setting of 'flow'
		// by querying for conversations
		Nav.conversationsBrowserController.set('flow', flow);
		 
		// show the page
		Nav.getPath('conversationFlowPage.mainPane').append();
	},

	willLoseFirstResponder: function () {
		// hide the page and reset the current conent
		Nav.conversationsBrowserController.set('flow', null);
	    Nav.getPath('conversationFlowPage.mainPane').remove();
	},
	
	nextArticle: function() {
		if (!Nav.conversationsBrowserController.get("hasNextConversation")) 
			return;
		Nav.conversationsBrowserController.selectObject(
				Nav.conversationsBrowserController.get("nextConversation"));
	},
	  
	previousConversation: function() {
		if (!Nav.conversationsBrowserController.get("hasPreviousConversation")) 
			return;
		Nav.conversationsBrowserController.selectObject(
				Nav.conversationsBrowserController.get("previousConversation"));
	},
	
	toFlows: function() {
		console.log('toFlows');
		Nav.states.main.go('flows');
	}
});