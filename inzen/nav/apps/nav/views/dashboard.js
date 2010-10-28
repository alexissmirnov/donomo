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

















//
//
//
//
//
//
//
//
//
//
///******************************************************************************
// *  @class
//
//  @extends SC.View
//*/
//App.FlowContentView2 = SC.View.extend({
//    classNames:'flow-content'.w(),
//	itemPadding: 10,
//    rowHeight: 161,
//    columnWidth: 317,
//    // observes('*content.[]') makes this handler fire twice, 
//    // so skipping the second time.
//	_contentRendered: false, 
//
//	
//	contentLengthDidChange: function() {
//		sc_super();
//		var content = this.get('content');
//		console.log('FlowContentView.contentLengthDidChange len=' + content ? content.get('length') : 0);
//	},
//
//
//	contentObserver: function(target, value) {
//		if( this._contentRendered )
//			return;
//		this._contentRendered = true;
//
//		/*
//		 * Here I'm using a query instead of tag.conversations in order to 
//		 * sort the resulting conversations by date.
//		 */
//	    var conversations = App.store.find(
//	    		SC.Query.local(App.model.Conversation, {
//	    			conditions: "{tg} AS_GUID_IN tags", 
//	    			parameters: { tg: this.get('content').get('guid')}, 
//	    			orderBy: 'date DESC'}));
//	    var height = this.get('rowHeight');
//	    var width = this.get('columnWidth');
//	 	var itemPadding = this.get('itemPadding');
//		var len = conversations.length();
//		
//		/*
//		 * cap the number of conversations we're showing
//		 * for performance
//		 */
//		if( len > 20 ) {
//			len = 20;
//			//TODO: invoke the rest later
//		}
//	
//		var runningWidth = 0;
//	    for (var i=0; i < len+1; i++) {
//	    	
//	    	// add a bumper view at the end
//	    	var view, item, viewProto;
//	    	
//	    	/*
//	    	 * Start the flow band with the summary tile
//	    	 */
//	    	if(i == 0) {
//	    		item = this.get('content'); // get a flow
//	    		
//	    		// Hiding the 'Unsorted' panel
//	    		if( item.get('name') === 'Unsorted' ) {
//	    			continue;
//	    		} else {	    			
//		    		viewProto = App.FlowSummaryView;
//		    		width = 100;
//	    		}
//	    	} else { //if( i < len+1 ) {
//	    		/*
//	    		 * Continue with adding conversation tiles
//	    		 */
//	    		viewProto = App.ConversationSummaryView,
//	    		item = conversations.objectAt(i-1); // get a conversation
//	    		width = this.get('columnWidth');
//	    	}
////			else {
////				/*
////				 * End with the bumper tile
////				 */
////				viewProto = App.FlowBumperView;
////				item = this.get('content'); // get a flow
////				width = 100;
////	    	}
//	    	
//			if( item.name != 'Unso')
//	    	// item can be ether a conversation or a flow
//			view = viewProto.create({
//				content:item,
//				layout: {
//					height: height, 
//					width: width, 
//					top: 0, 
//					left: runningWidth + ((((i < 2 )? 0 : i )) * itemPadding)
//				}
//			});
//
//	    	runningWidth += width;
//
//	    	this.appendChild(view);
//
//			// grow the size of the content view to include the newly 
//			// appended child
//			this.set('layout', {
//				top: 0, 
//				left: 0, 
//				height: height, 
//				width: (width + itemPadding)*(len+1) // +1 for the bumper
//			});
//	    }
//	}.observes('*content.[]')
//});