// ==========================================================================
// Project:   Nav
// ==========================================================================
/*globals Nav */
Nav = Nav;
require('responders/main');

/** @namespace

  Hanles sender classification commands
  
  @extends SC.Responder
*/
Nav.states.senderClassification = SC.Responder.create({
	// returns a complete array of flows 
	// array of {included (bool), flow (object), name (string)} for a given contact
	 _createContactFlowArray: function (contact) {
		var allFlows = Nav.store.find(Nav.query.GET_FLOWS);
		var contactFlows = contact.get('flows');
		var a = [];
		
		contactFlows.forEach( function (f) { a.pushObject( {
				included: true, 
				flow: f, name: 
				f.get('name')}); });
		
		allFlows.forEach( function (f) {
			var found = a.find( function(item) { return item.flow.get('guid') === f.get('guid'); } , f);
			if ( !found )
				a.pushObject({
					included: false, 
					flow: f, 
					name: f.get('name')});
		});
		
		return a;
	},
	
	// when we become first responder, show classification panel
	didBecomeFirstResponder: function () {
		// setup a controller for the classification page
		var senders = Nav.store.find(Nav.query.GET_TOP_UNCLASSIFIED_CONTACTS);
		var controller = Nav.senderClassificationController;
		
		controller.set('contentBinging', senders);
		
		// show the page
		Nav.getPath('senderClassificationPage.mainPane').append();
	},
	
	willLoseFirstResponder: function () {
		// hide the page
	    Nav.getPath('senderClassificationPage.mainPane').remove();
	},

	// advance selection to the next sender
	nextSender : function () {
		var controller = Nav.senderClassificationController;
		
		// reached the end, go to flows
		var currentIndex = controller.get('senderSelectionIndex');
		if( !currentIndex || currentIndex === controller.get('length') - 1) {
			Nav.states.main.go('flows');
			return;
		}
			
		nextSenderIndex = controller.get('senderSelectionIndex') + 1;
			
		controller.selectObject(controller.objectAt(nextSenderIndex));
		controller.set('senderSelectionIndex', nextSenderIndex);
		
		// set the flows. 
		Nav.senderClassificationFlowsController.set(
				'content', 
				Nav.states.senderClassification._createContactFlowArray(
						controller.objectAt(nextSenderIndex)));
		
	},
	
	newFlowPlanel: function () {
		Nav.getPath('senderClassificationPage.newFlowPane').append();
	},
	
	closeNewFlowPlanel: function () {
		Nav.getPath('senderClassificationPage.newFlowPane').remove();
	},
	
	createNewFlow: function (name) {
		Nav.store.createRecord(Nav.model.Flow, {
			'name' : name
		});
	}
});
