/*globals Nav,console*/
App.accountController = SC.ObjectController.create();
App.signupController = SC.ObjectController.create();

App.contactsController = SC.ArrayController.create();
App.conversationsController = SC.ArrayController.create();
App.messagesController = SC.ArrayController.create();
App.documentsController = SC.ArrayController.create();
App.syncTrackerController = SC.ArrayController.create();
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
	allowsMultipleSelection: NO//,
	
//	enumerableContentDidChange: function(start, len) {
//		sc_super();
//		if( len === 0 )
//			return;
//		
//		// create controllers for top conversations for each of the flow
//		this.forEach( function(flow) {
//			var topConversations = App.ConversationsController.create();
//			topConversations.set('content', flow.get('conversations'));
//			
//			flow.set('topConversationsController', topConversations);
//		});
//	}
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
