// ==========================================================================
// Project:   Nav
// ==========================================================================
/*globals Nav */
sc_require('responders/state');
sc_require('responders/flow');

/** @namespace

  
  @extends SC.Responder
*/
App.state.FLOWS = SC.Responder.create({
	name: 'FLOWS',
	
	// when we become first responder, show classification panel
	didBecomeFirstResponder: function () {
		// set the controller to show all flows 
		// TODO: only show the flows that have conversations in them 
		App.contactsController.set('content', App.store.find(App.query.GET_CONTACTS));
		
		/*
		 * The reason for invokeLast here is to make sure the flows and conversations
		 * are loaded AFTER the contacts are loaded and created. This is because
		 * conversations have a reference to a contact and the UI is notified
		 * when the conversation changes. When UI starts rendering the conversation,
		 * we want the contacts to be available.
		 */
		App.flowsController.invokeLast(function(){
				this.set('content', App.store.find(App.query.GET_FLOWS));});
		
		App.store.dataSource.getNestedDataSource().startDownloadMessages();
		
		// show the page
		App.getPath('flowsPage.mainPane').append();
	},
	
	willLoseFirstResponder: function () {
		// hide the page
	    App.getPath('flowsPage.mainPane').remove();
	},
	
	// advance selection to the next sender
	settings : function () {
		return;
	},
	
	toFlowState : function(flow) {
		App.state.FLOW.set('content', flow);
		App.state.transitionTo(App.state.FLOW);
	},
	
	showConversationView : function() {
		var conversationView = App.getPath('flowsPage.mainPane.conversation');
		conversationView.adjustToShow();
	},
	
	/**
	 * Handles click/touch on the conversation summary.
	 * The conversation view's content is set to the selected conversation
	 * 
	 * Assumes that all messages that make-up the conversation are loaded and are available  
	 */
	selectConversation: function(conversation) {
		App.conversationController.set('content', conversation);
		this.showConversationView();
	},
	/**
	 * Handles click/touch on the 'full screen' button.
	 * Hides the conversation view, moves the dashboard back to the full view
	 * mode
	 */
	showFlowsFullScreen : function() {
		App.getPath('flowsPage.mainPane.conversation').adjust('width', 0);
	},
	
	setCurrentSenderAsNewsletter: function(contact) {
		contact.set('type', App.model.Contact.BUSINESS);
		
		var conversationView = App.getPath('flowsPage.mainPane.conversation');
		conversationView.adjustToNewsletterLayout();
		//TODO: store it
	}
});
