// ==========================================================================
// Project:   Nav
// ==========================================================================
/*globals Nav */
Nav = Nav; // reduce jslint warnings about unresolved variable
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
		// TODO: only show the flows that have conversations in them 
		Nav.contactsController.set('content', Nav.store.find(Nav.query.GET_CONTACTS));
		
		/*
		 * The reason for invokeLast here is to make sure the flows and conversations
		 * are loaded AFTER the contacts are loaded and created. This is because
		 * conversations have a reference to a contact and the UI is notified
		 * when the conversation changes. When UI starts rendering the conversation,
		 * we want the contacts to be available.
		 */
		Nav.flowsController.invokeLast(function(){
				this.set('content', Nav.store.find(Nav.query.GET_FLOWS));});
					
		// show the page
		Nav.getPath('flowsPage.mainPane').append();
	},
	
	willLoseFirstResponder: function () {
		// hide the page
	    Nav.getPath('flowsPage.mainPane').remove();
	},
	
	// advance selection to the next sender
	settings : function () {
		return;
	},
	
	toFlowState : function(flow) {
		Nav.states.flow.set('content', flow);
		var flowID = flow.get('guid');
		Nav.states.main.go('flow/' + flowID); //TODO: need a better way to go from state to send state than by a URL fragment
	},
	
	/**
	 * Handles click/touch on the conversation summary.
	 * The conversation view's content is set to the selected conversation
	 * 
	 * Nav.conversationController is already set to a conversation record
	 * we want to show. However, it may be that the store doesn't
	 * yet have all the messages cached. So we need to run a query to
	 * load potentially missing Message records.
	 * 
	 * No need to modify the actual controller because it should already have all
	 * IDs to Message objects. After the query runs, those IDs won't be dandling
	 * anymore. 
	 */
	showConversationView : function() {
		var conversationGuid = Nav.conversationController.get('content').get('guid');
		
		Nav.store.find(
				SC.Query.local(Nav.model.Conversation, {
					conditions: 'guid={conversationGuid}',
					conversationGuid: conversationGuid
				})
		);
		
		var conversationView = Nav.getPath('flowsPage.mainPane.conversation');
		conversationView.adjust('width', 724);
		
		//Nav.getPath('flowsPage.mainPane.flows').adjust('width', 300);
	},
	/**
	 * Handles click/touch on the 'full screen' button.
	 * Hides the conversation view, moves the dashboard back to the full view
	 * mode
	 */
	showFlowsFullScreen : function() {
		Nav.getPath('flowsPage.mainPane.flows').adjust('width', 1024); // TODO remove 1024
		Nav.getPath('flowsPage.mainPane.conversation').adjust('width', 0);
	}
});
