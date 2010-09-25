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
App.ConversationSummaryView = App.ConversationListItemView.extend({
	classNames: 'conversation-summary',
    click: function(evt) {
		this.touchEnd();
	},
	touchStart: function(evt) {
		return YES;
	},
	/*
	 */
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
/******************************************************************************
 *  @class

  @extends SC.View
*/
App.FlowContentView = SC.View.extend({
    classNames:'FlowContentView'.w(),
	itemPadding: 10,
    rowHeight: 161,
    columnWidth: 317,
    // observes('*content.[]') makes this handler fire twice, 
    // so skipping the second time.
	_contentRendered: false, 

	
	contentLengthDidChange: function() {
		sc_super();
		var content = this.get('content');
		console.log('FlowContentView.contentLengthDidChange len=' + content ? content.get('length') : 0);
	},


	contentObserver: function(target, value) {
		if( this._contentRendered )
			return;
		this._contentRendered = true;

	    var conversations = this.get('content').get('conversations');//topConversationsController');
	    var height = this.get('rowHeight');
	    var width = this.get('columnWidth');
	 	var itemPadding = this.get('itemPadding');
		var len = conversations.length();
		
		/*
		 * cap the number of conversations we're showing
		 * for performance
		 */
		if( len > 5 ) {
			len = 5;
			//TODO: invoke the rest later
		}
		
		console.log('FlowContentView: conversations='+conversations+' len='+len);
	
		var runningWidth = 0;
	    for (var i=0; i < len+1; i++) {
	    	
	    	// add a bumper view at the end
	    	var view, item, viewProto;
	    	
	    	/*
	    	 * Start the flow band with the summary tile
	    	 */
	    	if(i == 0) {
	    		item = this.get('content'); // get a flow
	    		
	    		// Hiding the 'Unsorted' panel
	    		if( item.get('name') === 'Unsorted' ) {
	    			continue;
	    		} else {	    			
		    		viewProto = App.FlowSummaryView;
		    		width = 100;
	    		}
	    	} else { //if( i < len+1 ) {
	    		/*
	    		 * Continue with adding conversation tiles
	    		 */
	    		viewProto = App.ConversationSummaryView,
	    		item = conversations.objectAt(i-1); // get a conversation
	    		width = this.get('columnWidth');
	    	}
//			else {
//				/*
//				 * End with the bumper tile
//				 */
//				viewProto = App.FlowBumperView;
//				item = this.get('content'); // get a flow
//				width = 100;
//	    	}
	    	
			if( item.name != 'Unso')
	    	// item can be ether a conversation or a flow
			view = viewProto.create({
				content:item,
				layout: {
					height: height, 
					width: width, 
					top: 0, 
					left: runningWidth + ((((i < 2 )? 0 : i )) * itemPadding)
				}
			});

	    	runningWidth += width;

	    	this.appendChild(view);

			// grow the size of the content view to include the newly 
			// appended child
			this.set('layout', {
				top: 0, 
				left: 0, 
				height: height, 
				width: (width + itemPadding)*(len+1) // +1 for the bumper
			});
	    }
	}.observes('*content.[]')
});

/******************************************************************************
 *  @class

  @extends SC.ScrollView
*/
App.FlowScrollView = SC.ScrollView.extend({
    classNames:'flow-band'.w(),
	alwaysBounceVertical: NO,
	
	contentObserver: function(target, value) {
	    var flow = this.get('content'); // a flow
		var contentView = this.contentView;
		if( contentView.get && !contentView.get('content') && flow ) {
			contentView.set('content', flow);
		}
	}.observes('*content.[]'),

	contentView: App.FlowContentView.design({
	})
});

/******************************************************************************
 *  @class

  @extends SC.View
*/
App.FlowLabelView = SC.LabelView.extend({
	classNames: 'flow-label'.w(),
	textAlign: SC.ALIGN_LEFT,
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

/******************************************************************************
 *  @class

  @extends SC.View
*/
App.DashboardContentView = SC.View.extend({
    classNames:'dashboard-content'.w(),
    itemHeight: 170,
    labelHeight: 30,
	layout: { top: 0, left: 0, right: 0, bottom: 0},
    contentObserver: function(target, key){
		var i = 0;
		var that = this;
		
		//TODO it would be cleaner to detach the observer
		// than to ignore subsequent calls to it
		if( this.childViews.length > 0)
			return;
		
		// content is an array of flows
		var flows = this.get('content');
		flows.forEach(function(flow) {
			var viewTop = that.labelHeight + (that.labelHeight + that.itemHeight) * i;
			var view = App.FlowScrollView.create({
				layout: {
					top: viewTop, 
					left: 0, 
					right: 0, 
					height: that.itemHeight
				}
			});
			i = i + 1;
			that.appendChild(view);
			view.set('content', flow);
			

//			view = App.FlowLabelView.create({
//				layout: { 
//					left: 0, 
//					top: viewTop,
//					right: 0, 
//					height: that.labelHeight 
//				},
//				value: flow.get('name'),
//				content: flow
//			});
//			that.appendChild(view);

		});
		// grow the size of the content view to 
		// include the newly appended child
		this.set('layout', {
			top: 0, 
			height: (this.labelHeight + this.itemHeight) * flows.length(), 
			left: 0, 
			right: 0
		});
	}.observes('*content.[]')
});

/******************************************************************************
 *  @class

  @extends SC.ScrollView
*/
App.DashboardScrollView = SC.ScrollView.extend({
	// make sure the view doesn't react to side-ways swipes
	alwaysBounceHorizontal: NO,
	delaysContentTouches: NO,
	classNames: 'dashboard'.w(),
	
	contentView: App.DashboardContentView.design({
		contentBinding: 'App.flowsController.arrangedObjects'
	})
});
