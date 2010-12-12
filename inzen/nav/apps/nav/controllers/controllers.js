/*globals Nav,console*/


App.schemaVersionController = SC.ObjectController.create({
	contentDidChange: function() {
		console.log('%@.contentDidChange. %@ '.fmt(this.toString(), this.get('content').toString()));
		if( this.get('content') ) {
			schemaVersion = Number(this.get('content').objectAt(0).get('version').split('.')[1]);
			codeVersion = Number(App.VERSION.split('.')[1]);
			if( codeVersion > schemaVersion ) {
				this.get('content').objectAt(0).set('version', App.VERSION);

				App.model.Contact.objects().all().del();
				App.model.Message.objects().all().del();
				App.model.Conversation.objects().all().del();
				App.model.Flow.objects().all().del();
				App.model.Address.objects().all().del();
				App.model.SyncTracker.objects().all().del();
//				
//				App.contactsController.set('content', App.store.find(SC.Query.local(App.model.Contact)));
//				App.messagesController.set('content', App.store.find(SC.Query.local(App.model.Message)));
//				App.conversationsController.set('content', App.store.find(SC.Query.local(App.model.Conversation)));
//				App.documentsController.set('content', App.store.find(SC.Query.local(App.model.Document)));
//				App.flowsController.set('content', App.store.find(SC.Query.local(App.model.Flow)));
//				App.addressesController.set('content', App.store.find(SC.Query.local(App.model.Address)));
//				App.syncTrackerController.set('content', App.store.find(SC.Query.local(App.model.SyncTracker)));
//
//				this.invokeLater(function() {
//					var obj = App.store.recordsFor(App.model.SyncTracker);
//					obj.forEach(function(o) {App.store.destroyRecord(App.model.SyncTracker, o.get('guid'));});
//
//					var obj = App.store.recordsFor(App.model.Message);
//					obj.forEach(function(o) {App.store.destroyRecord(App.model.Message, o.get('guid'));});
//
//					var obj = App.store.recordsFor(App.model.Address);
//					obj.forEach(function(o) {App.store.destroyRecord(App.model.Address, o.get('guid'));});
//
//					var obj = App.store.recordsFor(App.model.Contact);
//					obj.forEach(function(o) {App.store.destroyRecord(App.model.Contact, o.get('guid'));});
//
//					var obj = App.store.recordsFor(App.model.Conversation);
//					obj.forEach(function(o) {App.store.destroyRecord(App.model.Conversation, o.get('guid'));});
//
//					var obj = App.store.recordsFor(App.model.Flow);
//					obj.forEach(function(o) {App.store.destroyRecord(App.model.Flow, o.get('guid'));});
//				}, 500);

				this.invokeLater(function() { App.state.transitionTo('START');}, 800);			
			} else {
				App.userController.set('content', App.store.find(SC.Query.local(App.model.User)));
				this.invokeLater(function() {App.accountsController.set('content', App.store.find(SC.Query.local(App.model.Account)));}, 500);
			}
		}
	}.observes('.content')	
});
App.accountController = SC.ObjectController.create();
App.signupController = SC.ObjectController.create();

App.contactsController = SC.ArrayController.create();
App.conversationsController = SC.ArrayController.create();
App.messagesController = SC.ArrayController.create();
App.documentsController = SC.ArrayController.create();
App.syncTrackerController = SC.ObjectController.create({
	timestamp: function() {
		if( this.content.objectAt(0) )
			return this.content.objectAt(0).get('date');
		else
			return undefined;
	}
});
App.addressesController = SC.ArrayController.create();

App.senderClassificationController = SC.ArrayController.create({
	senderSelectionIndex: null,
	allowsMultipleSelection: NO
});

App.senderClassificationFlowsController = SC.ArrayController.create({
	allowsMultipleSelection: NO,
	enumerableContentDidChange: function(start, len) {
		sc_super();
		
		//console.log('senderClassificationFlowsController.enumerableContentDidChange: ' + start + ',' + len);
		
		if( !this.hasSelection() && this.length() > 0 ) {
			this.selectObject(this.objectAt(0));
			this.set('senderSelectionIndex', 0);
			
			// set the flows. 
			App.senderClassificationFlowsController.set(
					'content', 
					App.states.senderClassification._createContactFlowArray(this.objectAt(0)));
		}
	}
});


/**
 * Updated by changing selection on any instance of
 * App.ConversationsController
 */
App.conversationController = SC.ObjectController.create({
	messagesDidChange: function() {
		console.log('%@: messagesDidChange. content.messages.length=%@'.fmt(this.toString(), this.get('content').get('messages').length()));
	}.observes('.content.messages'),
	contentDidChange: function() {
		console.log('%@: contentDidChange. content.messages.length=%@ content.subject=%@ '.fmt(this.toString(), this.get('content').get('messages').length(), this.get('content').get('subject')));
	}.observes('.content')
	
});

App.conversationMessagesController = SC.ArrayController.create();


/******************************************************************************
 * The content of this controller is set by
 * App.states.flows.didBecomeFirstResponder
 */
App.flowsController = SC.ArrayController.create({
	allowsMultipleSelection: NO,
	
	enumerableContentDidChange: function(start, len) {
		sc_super();
		if( len === 0 )
			return;
		
		this.forEach( function(flow) {
			console.log(flow.get('name'));
		});
	}
});

/******************************************************************************
 * This controller is included into every flow provided by flowController.
 * The selection indicates currently shown conversation.
 * The setup is done in App.states.flows.didBecomeFirstResponder
 * */
App.ConversationsController = SC.ArrayController.extend({
	flow: null,
	allowsMultipleSelection: NO,
	allowsEmptySelection: NO,

	hasPreviousConversation: function() {
	    return !!this.get('previousConversation');
	}.property('previousConversation').cacheable(),
	
	hasNextConversation: function() {
	    return !!this.get('nextConversation');
	}.property('nextConversation').cacheable(),
	
	previousConversation: function() {
		var ao = this.get('arrangedObjects'), set = this.get('selection').indexSetForSource(ao);
		if (!set) return null;
	
		var first = set.get('min');
	
		// now start trying indexes
		var idx = first - 1;
		if( idx >= 0 )
			return ao.objectAt(idx);
		return null;
	}.property('selection', 'arrangedObjects').cacheable(),
	
	nextConversation: function(){
		var ao = this.get('arrangedObjects'), set = this.get('selection').indexSetForSource(ao);
		if (!set) return null;
		
		var last = set.get('max');
		
		// now start trying indexes
		var idx = last + 1, len = ao.get('length');
		if ( idx < len )
			return ao.objectAt(idx);
		return null;
	}.property('arrangedObjects', 'selection').cacheable(),

	flowDidChange: function () {
		var flow = this.get('flow');
		var conversations = null;
		
		if( flow ) {
			// set flow's conversations as content
			var q = SC.Query.local(App.model.Conversation, '{id} AS_GUID_IN flows', {id: flow.get('guid')});
			conversations = App.store.find(q);
			this.set('content', conversations);
		}
		this.set('content', conversations);	
		
		// select the first conversation
		this.selectObject(this.get('arrangedObjects').objectAt(0));
	}.observes('flow'),
	
	selectionDidChange: function () {
		var ao = this.get('arrangedObjects'), set = this.get('selection').indexSetForSource(ao);
		if (!set) return null;
		
		var first = set.get('firstObject');
		App.conversationController.set('content', ao.objectAt(first));
	}.observes('selection'),
	
	flowName: function () {
		var flow = this.get('flow');
		if (flow)
			return flow.get('name');
		return null;
	}.property('flow').cacheable(),
	
	
	selectionMessages: function () {
		var ao = this.get('arrangedObjects'), set = this.get('selection').indexSetForSource(ao);
		if (!set) return null;
		
		var first = set.get('firstObject');
		return ao.objectAt(first).get('messages');
	}.property('selection').cacheable(),
	
	selectionSubject: function () {
		var ao = this.get('arrangedObjects'), set = this.get('selection').indexSetForSource(ao);
		if (!set) return null;
		
		var first = set.get('firstObject');
		return ao.objectAt(first).get('subject');
	}.property('selection').cacheable(),
	
	
	enumerableContentDidChange: function(start, length) {
		sc_super();
		console.log('ConversationsController.enumerableContentDidChange('+start+','+length+')');
	}
});

/**
 * Used by master/detail view to show all conversations in master view
 * and selected conversations in detail view
 */
App.conversationsBrowserController = App.ConversationsController.create();

App.statusMessageController = SC.ObjectController.create();
