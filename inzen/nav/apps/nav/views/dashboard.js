require('responders/main');
require('responders/flows');

// all flow dashboard views are here

/******************************************************************************
 *  @class

  @extends SC.View
*/
Nav.MessageSummaryView = SC.View.extend({
    classNames:'MessageSummaryView'.w(),
	content: null,
	displayProperties: 'content'.w(),
	render: function(context,firstTime) {
		var content = this.get('content');
		if(!content) return;
		
		context = context.begin('div').
				addClass('MessageSummaryView-sender').
				push(content.get('from').get('attributes').name).
			end();
		context = context.begin('div').
				addClass('MessageSummaryView-subject').
				push(content.get('subject')).
			end();
		context = context.begin('div').
				addClass('MessageSummaryView-body').
				push(content.get('body')).
			end();
		
		sc_super();
	},
    click: function(evt) {
		this.touchEnd();
	},
	touchStart: function(evt) {
		return YES;
	},
	touchEnd: function(evt) {
		var controller, index;
		var content = this.get('content');
		Nav.states.main.go('main');
	}
});


/******************************************************************************
 *  @class

  @extends SC.LabelView
*/
Nav.FlowBumperView = SC.View.extend({
	childViews: "label".w(),
	label: SC.LabelView.design({
		textAlign: SC.ALIGN_CENTER,
		value: 'CLICK HERE FOR MORE FROM THIS SECTION'
	}),
	
    click: function(evt) {
		this.touchEnd();
	},
	touchStart: function(evt) {
		return YES;
	},
	touchEnd: function(evt) {
		var content = this.get('content');
		Nav.states.flows.toFlowState(content);
	}
});
/******************************************************************************
 *  @class

  @extends SC.View
*/
Nav.FlowContentView = SC.View.extend({
    classNames:'FlowContentView'.w(),
	itemPadding: 10,
    rowHeight: 161,
    columnWidth: 317,
    // observes('*content.[]') makes this handler fire twice, 
    // so skipping the second time.
	_alreadyRendered: false, 
	
	contentObserver: function(target, value) {
		if( this._contentRendered )
			return;
		this._contentRendered = true;

	    var content = this.get('content').get('topFlowMessageController');
	    var height = this.get('rowHeight');
	    var width = this.get('columnWidth');
	 	var itemPadding = this.get('itemPadding');
		var len = content.length();
		
		console.log('FlowContentView: content='+content+' len='+len);
	
	    for (var i=0; i < len + 1; i++) {
	    	
	    	// add a bumper view at the end
	    	var view, itemContent, viewProto;
	    	if( i < len ) {
	    		viewProto = Nav.MessageSummaryView;
	    		itemContent = content.objectAt(i);
	    	}
			else {
				viewProto = Nav.FlowBumperView;
				itemContent = this.get('content');
	    	}
			
			view = viewProto.create({
				content:itemContent,
				layout: {
					height: height, 
					width: width, 
					top: 0, 
					left: width * i + ((((i === 0 )? 0 : i )) * itemPadding)
				}
			});

			this.appendChild(view);

			// grow the size of the content view to include the newly 
			// appended child
			this.set('layout', {
				top: 0, 
				left: 0, 
				height: height, 
				width: (width + itemPadding)*(len+1) // +1 for the bumber
			});
	    };
	}.observes('*content.[]')
});

/******************************************************************************
 *  @class

  @extends SC.ScrollView
*/
Nav.FlowScrollView = SC.ScrollView.extend({
    classNames:'FlowScrollView'.w(),
	alwaysBounceVertical: NO,
	
	contentObserver: function(target, value) {
	    var content = this.get('content');
		var contentView = this.contentView;
		if( contentView.get && !contentView.get('content') && content ) {
			contentView.set('content', content);
		}
	}.observes('*'), //observing  *content.[] doesn't trigger the call. 
	// TODO: find out why

	contentView: Nav.FlowContentView.design({
	})
});

/******************************************************************************
 *  @class

  @extends SC.View
*/
Nav.FlowLabelView = SC.LabelView.extend({
	textAlign: SC.ALIGN_LEFT,
    click: function(evt) {
		this.touchEnd();
	},
	touchStart: function(evt) {
		return YES;
	},
	touchEnd: function(evt) {
		var content = this.get('content');
		Nav.states.flows.toFlowState(content);
	}
	
});

/******************************************************************************
 *  @class

  @extends SC.View
*/
Nav.DashboardContentView = SC.View.extend({
    classNames:'DashboardContentView'.w(),
	layout: { top: 0, left: 0, right: 0, bottom: 0},
    contentObserver: function(target, key){
		console.log('DashboardContentView:'+target+'='+key );
		console.log('flows='+this.get('content'));
		var i = 0;
		var thisView = this;
		
		//TODO it would be cleaner to detach the observer
		// than to ignore subsequent calls to it
		if( thisView.childViews.length > 0)
			return;
		
		this.get('content').forEach(function(item) {
			console.log('flow='+item);
			var view = Nav.FlowLabelView.create({
					layout: { left: 0, top: (30 + 170) * i, right: 0, height: 30 },
					value: item.get('name'),
					content: item
				});
			thisView.appendChild(view);
			var view = Nav.FlowScrollView.create({
				layout: {top: 30 + (30 + 170) * i, left: 0, right: 0, height: 170}
			});
			i = i + 1;
			thisView.appendChild(view);
			view.set('content', item);
		});
		// grow the size of the content view to 
		// include the newly appended child
		this.set('layout', {
			top: 0, 
			height: (30 + 170) * this.get('content').get('length'), 
			left: 0, 
			right: 0
		});
	}.observes('*content.[]')
});

/******************************************************************************
 *  @class

  @extends SC.ScrollView
*/
Nav.DashboardScrollView = SC.ScrollView.extend({
	// make sure the view doesn't react to side-ways swipes
	alwaysBounceHorizontal: NO,
	delaysContentTouches: NO,
	classNames: 'DashboardScrollView'.w(),
	
	contentView: Nav.DashboardContentView.design({
		contentBinding: 'Nav.flowsController.arrangedObjects'
	})
});
