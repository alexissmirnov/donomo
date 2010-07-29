// ==========================================================================
// Project:   Nav
// ==========================================================================
/*globals Nav */
require('responders/main');
require('responders/flow');

/** @namespace

  Hanles sender classification commands
  
  @extends SC.Responder
*/
Nav.states.flows = SC.Responder.create({
	// when we become first responder, show classification panel
	didBecomeFirstResponder: function () {
		
		// set the controller to show all flows 
		// TODO: only show the flows that have messages in them 
		Nav.flowsController.set('content', Nav.store.find(SC.Query.local(Nav.model.Flow)));
		
		// create controllers for top messages for each of the flow
		Nav.flowsController.forEach( function(flow) {
			var topMessages = SC.ArrayController.create();
			topMessages.set('content', []);
			var contacts = flow.get('contacts');
			contacts.forEach( function (contact) {
				contact.get('sentMessages').forEach( function (message) {
					topMessages.pushObject(message);
				});
			});
			
			flow.set('topFlowMessageController', topMessages);
		});
			
		// show the page
		Nav.getPath('flowsPage.mainPane').append();
	},
	
	willLoseFirstResponder: function () {
		// hide the page
	    Nav.getPath('flowsPage.mainPane').remove();
	},

	// advance selection to the next sender
	settings : function () {
	},
	
	toFlowState : function(content) {
		Nav.states.flow.set('content', content);
		var flowID = content.get('guid');
		Nav.states.main.go('flow/' + flowID);
	}
});
