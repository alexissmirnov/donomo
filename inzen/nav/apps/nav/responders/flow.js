sc_require('responders/state');

/** @namespace

  Hanles sender classification commands
  
  @extends SC.Responder
*/
App.state.FLOW = SC.Responder.create({
	// when we become first responder, show classification panel
	didBecomeFirstResponder: function () {	
		var flow = this.get('content');
		
		// conversationsBrowserController will react to setting of 'flow'
		// by querying for conversations
		App.conversationsBrowserController.set('flow', flow);
		 
		// show the page
		App.getPath('conversationFlowPage.mainPane').append();
	},

	willLoseFirstResponder: function () {
		// hide the page and reset the current conent
		App.conversationsBrowserController.set('flow', null);
	    App.getPath('conversationFlowPage.mainPane').remove();
	},
	
	nextArticle: function() {
		if (!App.conversationsBrowserController.get("hasNextConversation")) 
			return;
		App.conversationsBrowserController.selectObject(
				App.conversationsBrowserController.get("nextConversation"));
	},
	  
	previousConversation: function() {
		if (!App.conversationsBrowserController.get("hasPreviousConversation")) 
			return;
		App.conversationsBrowserController.selectObject(
				App.conversationsBrowserController.get("previousConversation"));
	},
	
	toFlows: function() {
		console.log('toFlows');
		App.state.transitionTo('FLOWS');
	}
});