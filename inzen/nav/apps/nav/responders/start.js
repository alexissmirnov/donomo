/**
 * START state
 * 
 * 
 */
sc_require('responders/state');
sc_require('models');

App.state.CLEAR = SC.Responder.create({
	name: 'CLEAR',
	didBecomeFirstResponder : function() {
		console.log('deleting all local data');
		App.store.dataSource._dropAllTables();
		App.store.reset();
		window.localStorage.clear();
		document.cookie = "sessionid=;expires=%@;;".fmt((new Date()).toGMTString());

		App.state.transitionTo('START');
	}
});

App.state.REDOWNLOAD = SC.Responder.create({
	name: 'REDOWNLOAD',
	didBecomeFirstResponder : function() {
		
		App.store.destroyRecord(App.model.SyncTracker, App.model.SyncTracker.prototype.ID);
		this.invokeLast(function() { App.state.transitionTo('START');});
	}
});

App.state.UPGRADE = SC.Responder.create({
	name: 'UPGRADE',
	didBecomeFirstResponder : function() {
		
		schemaVersion = App.store.find(App.model.SchemaVersion);
		schemaVersion.objectAt(0).set('version', '0.0.0');
		this.invokeLater(function() { App.state.transitionTo('START');}, 200);
	}
});


App.state.START = SC.Responder.create({
	name: 'START',
	
	/**
	 * This responder is set by the main entry point. This function:
	 *  - creates the store and connects it to data source
	 *  - shows the main surface pane 
	 *  - tries to retrieve the Profile object from the database 
	 *  and connect it to the profile controller
	 * 
	 * @returns this
	 */
	didBecomeFirstResponder : function() {
		// register Nav.state.route() as the route handler
		// The route is the URL's fragment (after #) is set to the state name
		SC.routes.add(':location', App.state, 'routeHandler');

		// create the in-memory store, connect it to the Lawnchair DS
		// connect Lawnchair DS to the ServerDataSource
		var store = SC.Store.create( {
			commitRecordsAutomatically : YES
		}).from(LawnchairSC.DataSource.create({
				nestedDataSource: 'Nav.ServerDataSource'
			}));
		App.set('store', store);

		// initialize controllers with the queries
		// initially these queries will return nothing, but
		// when the user and account records are created they will be updated
		// accountsController will set the the app to the appropriate state
		// (READY or MANAGING_PROFILE)
		// depending if accounts are available.
		//SC.LOG_OBSERVERS = YES;
		//SC.LOG_BINDINGS = YES;
		//FIXME: do a proper state sequence
		App.schemaVersionController.set('content', App.store.find(SC.Query.local(App.model.SchemaVersion)));
//		App.userController.set('content', App.store.find(SC.Query.local(App.model.User)));
//		App.contactsController.set('content', App.store.find(SC.Query.local(App.model.Contact)));
//		App.messagesController.set('content', App.store.find(SC.Query.local(App.model.Message)));
//		App.conversationsController.set('content', App.store.find(SC.Query.local(App.model.Conversation)));
//		App.documentsController.set('content', App.store.find(SC.Query.local(App.model.Document)));
//		App.flowsController.set('content', App.store.find(SC.Query.local(App.model.Flow)));
//		App.addressesController.set('content', App.store.find(SC.Query.local(App.model.Address)));
//		App.syncTrackerController.set('content', App.store.find(SC.Query.local(App.model.SyncTracker)));
//		App.getPath('mainPage.mainPane').append();
//		App.accountsController.set('content', App.store.find(SC.Query.local(App.model.Account)));
				
				
		App.statusMessageController.set('content', 'Starting up');
		// now show the main page.
		// this page has the navigation buttons such as 'profile'
		App.getPath('mainPage.mainPane').append();
		return this;
	}
});
