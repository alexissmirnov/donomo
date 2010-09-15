/*globals Nav,console*/
Nav.accountController = SC.ObjectController.create();
Nav.signupController = SC.ObjectController.create();
Nav.contactsController = SC.ArrayController.create();
Nav.senderClassificationController = SC.ArrayController.create({
	senderSelectionIndex: null,
	allowsMultipleSelection: NO
});

Nav.senderClassificationFlowsController = SC.ArrayController.create({
	allowsMultipleSelection: NO,
	enumerableContentDidChange: function(start, len) {
		sc_super();
		
		console.log('senderClassificationFlowsController.enumerableContentDidChange: ' + start + ',' + len);
		
		if( !this.hasSelection() && this.length() > 0 ) {
			this.selectObject(this.objectAt(0));
			this.set('senderSelectionIndex', 0);
			
			// set the flows. 
			Nav.senderClassificationFlowsController.set(
					'content', 
					Nav.states.senderClassification._createContactFlowArray(this.objectAt(0)));
		}
	}
});


/**
 * Updated by changing selection on any instance of
 * Nav.ConversationsController
 */
Nav.conversationController = SC.ObjectController.create();


/******************************************************************************
 * The content of this controller is set by
 * Nav.states.flows.didBecomeFirstResponder
 */
Nav.flowsController = SC.ArrayController.create({
	allowsMultipleSelection: NO//,
	
//	enumerableContentDidChange: function(start, len) {
//		sc_super();
//		if( len === 0 )
//			return;
//		
//		// create controllers for top conversations for each of the flow
//		this.forEach( function(flow) {
//			var topConversations = Nav.ConversationsController.create();
//			topConversations.set('content', flow.get('conversations'));
//			
//			flow.set('topConversationsController', topConversations);
//		});
//	}
});

/******************************************************************************
 * This controller is included into every flow provided by flowController.
 * The selection indicates currently shown conversation.
 * The setup is done in Nav.states.flows.didBecomeFirstResponder
 * */
Nav.ConversationsController = SC.ArrayController.extend({
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
			var q = SC.Query.local(Nav.model.Conversation, '{id} AS_GUID_IN flows', {id: flow.get('guid')});
			conversations = Nav.store.find(q);
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
		Nav.conversationController.set('content', ao.objectAt(first));
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
Nav.conversationsBrowserController = Nav.ConversationsController.create();
