/**
 * 
 * Dashboard related views.
 * 
 * 
 */


require('responders/state');
require('responders/flows');
require('resources/conversation_flow_page');
// all flow dashboard views are here

/******************************************************************************
 *  @class

  @extends SC.View
*/
App.MessageAggregateView = SC.View.extend({
	classNames: 'conversation-list-view-item conversation-summary'.w(),

	messages: function() {
		return this.get('content').get('messages');
	}.property('content').cacheable(),
	
	messageCount: function() {
		return this.get('content').get('messages').length();
	}.property('content').cacheable(),
	
	messageConuntString: function() {
		return '' + this.get('messageCount');
	}.property('messageCount').cacheable(),
	
	latestMessage: function() {
		var messages = this.get('messages');
		var messageCount = this.get('messageCount');
		return messages.objectAt(messageCount-1);
	}.property('content').cacheable(),
	
	aggregateDate: function() {
		var d = this.get('content').get('date');
		if (d) {
			return d.toFormattedString('%a, %d %b');
		} else {
			return d;
		}
	}.property('content').cacheable(),
	
	
	childViews: [
	    SC.LabelView.design({
	    	classNames: 'conversation-list-view-item--key-participant'.w(),
	    	fontWeight: SC.BOLD_WEIGHT,
	    	isEditable: NO,
	    	textAlign: SC.ALIGN_LEFT,
	    	layout: { left: 5, right: 0, top: 0, height: 25 },
	    	valueBinding: '.parentView.content.key_participant.contact.name'
	    }),
	    SC.LabelView.design({
	    	classNames: 'conversation-list-view-item--date'.w(),
	    	textAlign: SC.ALIGN_RIGHT,
	    	layout: { left: 5, right: 5, top: 0, height: 25 },
	    	valueBinding: '.parentView.aggregateDate'
	    }),
	    SC.LabelView.design({
	    	classNames: 'conversation-list-view-item--subject'.w(),
	    	textAlign: SC.ALIGN_LEFT,
	    	layout: { left: 5, right: 20, top: 20, height: 20 },
	    	valueBinding: '.parentView.content.subject'
	    }),
	    SC.LabelView.design({
	    	classNames: 'conversation-list-view-item--message-count'.w(),
	    	textAlign: SC.ALIGN_CENTER,
	    	layout: { width: 30, right: 10, top: 20, height: 20 },
	    	valueBinding: '.parentView.messageConuntString'
	    }),
	    SC.LabelView.design({
	    	classNames: 'conversation-list-view-item--summary'.w(),
	    	textAlign: SC.ALIGN_LEFT,
	    	layout: { left: 5, right: 5, top: 40, height: 60 },
	    	valueBinding: '.parentView.content.summary'
	    })
	],

	click: function(evt) {
		this.touchEnd();
	},
	touchStart: function(evt) {
		return YES;
	},
	touchEnd: function(evt) {
		App.state.FLOWS.selectConversation(this.get('content'));
	}
});


/******************************************************************************
 *  @class

  @extends SC.LabelView
*/
App.FlowSummaryView = SC.View.extend({
	classNames: 'flow-summary'.w(),
	childViews: 'label'.w(),
	label: SC.LabelView.design({
		textAlign: SC.ALIGN_LEFT,
		controlSize: SC.LARGE_CONTROL_SIZE,
		valueBinding: '.parentView.content.name'
	})
});

/******************************************************************************
 *  @class

  @extends SC.LabelView
*/
App.FlowBumperView = SC.View.extend({
	childViews: 'label'.w(),
	label: SC.LabelView.design({
		textAlign: SC.ALIGN_CENTER,
		value: 'CLICK HERE FOR MORE FROM THIS SECTION/FLOW/LABEL/LIST'
	}),
	   
    click: function(evt) {
		this.touchEnd();
	},
	touchStart: function(evt) {
		return YES;
	},
	touchEnd: function(evt) {
		var flow = this.get('content');
		App.states.flows.toFlowState(flow);
	}
});

App.FlowContentView = SC.CollectionView.extend({
    classNames:'flow-content'.w(),
    exampleView: App.MessageAggregateView,
	layoutForContentIndex: function(contentIndex) {
	    return {
			top:    0,
			bottom: 0,
			left:   200*contentIndex,
			width:  190
	    };
	},
	computeLayout: function() {
		return {
			top:    0,
			bottom: 0,
			left:   0,
			width:  200*this.get('content').length()
		};
	},
	contentBinding: '.parentView.parentView.parentView.sortedConversations'
});


App.FlowScrollView = SC.ScrollView.extend({
	classNames:'flow-scroll'.w(),
	alwaysBounceVertical: NO,
	contentView: App.FlowContentView.design()
});

App.DashboardBar = SC.View.extend({
	childViews: 'shading label scroll'.w(),
	shading: SC.View.design({
		classNames: 'flow-shading'.w(),
		layout: {
			top: 0, 
			left: 0, 
			right: 0, 
			bottom: 5
		}
	}),
	label: SC.LabelView.design({
		classNames: 'flow-label'.w(),
		textAlign: SC.ALIGN_LEFT,
		fontWeight: SC.BOLD_WEIGHT,
		controlSize: SC.LARGE_CONTROL_SIZE,
		layout: {
			top: 3, 
			left: 30, 
			right: 0, 
			height: 25
		},
		valueBinding: '.parentView.content.name'
	}),
	scroll: App.FlowScrollView.design({
		layout: {
			top: 30, 
			left: 0, 
			right: 0, 
			height: 135
		}
	}),
	sortedConversations: function() {
		var flow = this.get('content');
		return App.store.find(
	    		SC.Query.local(App.model.Conversation, {
	    			conditions: "{tag} AS_GUID_IN tags", 
	    			parameters: { tag: flow.get('guid')}, 
	    			orderBy: 'date DESC'}));	
	}.property('content').cacheable()
});

App.DashboardContentView = SC.ListView.extend({
	exampleView: App.DashboardBar,
    classNames:'dashboard-content'.w(),
    rowHeight: 170
});

App.DashboardScrollView = SC.ScrollView.extend({
	// make sure the view doesn't react to side-ways swipes
	alwaysBounceHorizontal: NO,
	delaysContentTouches: NO,
	classNames: 'dashboard-scroll'.w(),
	
	contentView: App.DashboardContentView.design({
		contentBinding: 'App.flowsController.arrangedObjects'
	})
});
