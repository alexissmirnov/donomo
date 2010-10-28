sc_require('responders/state');
sc_require('responders/managing_profile');

App.userController = SC.ObjectController.create({
	user: function() {
		return this.get('content').objectAt(0);
	},
	
	contentDidChange: function() {
		//console.log('userController.contentDidChange. content=%@'.fmt(this.get('content')));
		if( this.get('content') && this.get('content').length() > 0 && this.content.objectAt(0).get('username')) {
			App.contactsController.set('content', App.store.find(SC.Query.local(App.model.Contact)));
			App.messagesController.set('content', App.store.find(SC.Query.local(App.model.Message)));
			App.conversationsController.set('content', App.store.find(SC.Query.local(App.model.Conversation)));
			App.documentsController.set('content', App.store.find(SC.Query.local(App.model.Document)));
			App.flowsController.set('content', App.store.find(SC.Query.local(App.model.Flow)));
			App.addressesController.set('content', App.store.find(SC.Query.local(App.model.Address)));
			App.syncTrackerController.set('content', App.store.find(SC.Query.local(App.model.SyncTracker)));

			App.state.transitionTo('FLOWS');
		}
	}.observes('content')
	
});

App.accountsController = SC.ArrayController.create( {
	
	/**
	 * Invoked several times:
	 *  - length 0 when the App.accountsController instance is created. At this
	 * point App.firstResponder isn't set yet.
	 * 
	 *  - length 0 in START state when START state sets the 'content' property of this controller
	 *  
	 *  - length 1 when the DB query returns the data, for content 
	 *  
	 *  - length 1 AGAIN (bug?) TODO
	 * 
	 */
    enumerableContentDidChange: function(start, length) {
        arguments.callee.base.apply(this,arguments);
        
        //console.log('accountsController.enumerableContentDidChange: len=%@, responder=%@'.fmt(length, App.firstResponder ? App.firstResponder.get('name') : 'none'));
		
		if( length === 0 && App.firstResponder && !App.store.dataHashes[App.store.storeKeyFor(App.model.User, '1')]) {
			App.state.transitionTo('MANAGING_PROFILE');	
		}
		
		
    }
});