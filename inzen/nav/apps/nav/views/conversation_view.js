App.CONVERSATION_VIEW_ITEM_CONTACT_COLUMN_WIDTH = 140;
App.CONVERSATION_PANEL_WIDTH = 724;
App.CONVERSATION_HEADER_HEIGHT = 40;
App.NEWSLETTER_FOOTER_HEIGHT = 30;
App.CONVERSATION_HEADER_SPACING = 5;
App.CONVERSATION_BUTTON_WIDTH = 105;
App.CONVERSATION_BUTTON_LEFT = App.CONVERSATION_HEADER_SPACING;
App.CONVERSATION_SUBJECT_WIDTH = 414;
App.CONVERSATION_SUBJECT_LEFT = App.CONVERSATION_BUTTON_LEFT+App.CONVERSATION_BUTTON_WIDTH+App.CONVERSATION_HEADER_SPACING;
App.CONVERSATION_CLOSE_BUTTON_WIDTH = 20;
App.CONVERSATION_SENDER_WIDTH = 165;
App.CONVERSATION_SENDER_RIGHT = App.CONVERSATION_CLOSE_BUTTON_WIDTH + App.CONVERSATION_HEADER_SPACING;


App.SenderContactLabel = SC.View.extend({
	childViews: [
	    SC.LabelView.design({
	    	layout: {top: 20, left: 5, right: 0, height: 20},
	        textAlign: SC.ALIGN_LEFT,
	    	valueBinding: '.parentView.parentView.content.sender_address.contact.name'
	    })
	]
});
/******************************************************************************
 *  @class
 * @extends View
*/
App.ConversationItemView = SC.View.extend(SC.Animatable, SC.StaticLayout, {
    classNames: 'conversation-item'.w(),
    useStaticLayout: YES,
    
	transitions: {
		 left: { duration: .25, timing: SC.Animatable.TRANSITION_EASE_IN_OUT } // with timing curve
	},

    childViews: [
    App.SenderContactLabel.design({
        classNames: 'conversation-item--contact'.w(),
        layout: {
            left: 0,
            width: 100
        }
    }),
    SC.StaticContentView.design({
        classNames: 'conversation-item--body'.w(),
        layout: {
            left: App.CONVERSATION_VIEW_ITEM_CONTACT_COLUMN_WIDTH,
            right: 0
        },
        contentBinding: '.parentView.content.body'
    })
    ]
});


/******************************************************************************
 *  @class

  @extends SC.View
*/
App.ConversationContentView = SC.StackedView.extend({
	contentBinding: 'App.conversationController.messages', // content is one an array of messages
	exampleView: App.ConversationItemView,
	itemViewForContentIndex: function(idx, rebuild) {
		var item = sc_super();
		
		if( this.parentView.parentView.parentView.contact.get('type') === App.model.Contact.PERSON ) {
			item.adjust('width', App.CONVERSATION_PANEL_WIDTH);
			item.adjust('left', 0); 
		}
		else {
			item.adjust('width', App.CONVERSATION_VIEW_ITEM_CONTACT_COLUMN_WIDTH
					+App.CONVERSATION_PANEL_WIDTH);
			item.adjust('left', -App.CONVERSATION_VIEW_ITEM_CONTACT_COLUMN_WIDTH); 
		}
		
		return item;
	}
});

/******************************************************************************
 *  @class ConversationScrollView
 *  Assumes content will be set to a conversation object
 *  @extends SC.ScrollView
*/
App.ConversationScrollPanel = SC.ScrollView.extend({
	classNames: 'conversation-content'.w(),
	// make sure the view doesn't react to side-ways swipes
	alwaysBounceHorizontal: NO,
	contentView: App.ConversationContentView.design({})
});


App.ConversationHeaderView = SC.View.extend({
	classNames: 'app-newsletter-header'.w(),
	
    layout: {
		top: 0, 
		right: 0, 
		left: 0, 
		height: App.CONVERSATION_HEADER_HEIGHT
	},
    childViews: 'viewSwitchButton subject sender'.w(),
    viewSwitchButton: SC.ButtonView.design({
    	layout: {top: 0, left: App.CONVERSATION_BUTTON_LEFT, width: App.CONVERSATION_BUTTON_WIDTH},
    	title: 'Newsletter',
    	action: 'actionHandler',
    	actionHandler: function() {
    		var panel = this.parentView.parentView;
    		 
    		if( panel.contact.get('type') === App.model.Contact.BUSINESS) {
    			panel.contact.set('type', App.model.Contact.PERSON);
    			panel.adjustToConversationLayout();
    		} else {
    			panel.contact.set('type', App.model.Contact.BUSINESS);
    			panel.adjustToNewsletterLayout();
    		}
    		App.state.FLOWS.didChangeContactType(panel.contact);
    	}
    }),
    subject: SC.LabelView.design({
    	classNames: 'app-newsletter-header-subject'.w(),
    	layout: {
    		left: App.CONVERSATION_SUBJECT_LEFT, 
    		height: App.CONVERSATION_HEADER_HEIGHT, 
    		width: App.CONVERSATION_SUBJECT_WIDTH
    	},
    	valueBinding: 'App.conversationController.subject',
    	controlSize: SC.LARGE_CONTROL_SIZE,
    	textAlign: SC.ALIGN_CENTER
    }),
    sender: SC.LabelView.design(SC.Animatable, {
    	classNames: 'app-newsletter-header-sender'.w(),
    	textAlign: SC.ALIGN_RIGHT,
    	controlSize: SC.LARGE_CONTROL_SIZE,
    	layout: {
    		right: -App.CONVERSATION_SENDER_RIGHT-App.CONVERSATION_SENDER_WIDTH, // off screen
    		height: App.CONVERSATION_HEADER_HEIGHT, 
    		width: App.CONVERSATION_SENDER_WIDTH
    	},
    	transitions: {
   			right: { duration: .25, timing: SC.Animatable.TRANSITION_EASE_IN_OUT } // with timing curve
    	},
    	valueBinding: '.parentView.parentView.senderName'
    })
});

App.NewsletterFooterView = SC.View.extend({
	classNames: 'app-newsletter-footer'.w(),
	
    layout: {bottom: -App.NEWSLETTER_FOOTER_HEIGHT-10, right: 0, left: 0, height: App.NEWSLETTER_FOOTER_HEIGHT},
    childViews: [
        SC.LabelView.design({
        	layout: {centerY: 0, centerX: 0},
        	value: 'message scrubber goes here'
        })
    ]
});


App.ConversationPanel = SC.View.extend({
	childViews: 'header scroll close footer'.w(),
	scroll: App.ConversationScrollPanel.design({
		layout: {top: App.CONVERSATION_HEADER_HEIGHT}
	}),
    header: App.ConversationHeaderView.design(),
	footer: App.NewsletterFooterView.design(),
	close: SC.ButtonView.design({
        layout: {
			top: 0,
			right: 0,
			height: App.CONVERSATION_CLOSE_BUTTON_WIDTH,
			width: App.CONVERSATION_CLOSE_BUTTON_WIDTH
		},
        title: 'X',
        action: 'showFlowsFullScreen',
        target: App.state.FLOWS
      }),
      
    
    senderName: null,
    contact: null,
    
	adjustToConversationLayout: function() {
		this.scroll.adjust('bottom', 0);
		this.footer.adjust('bottom', -App.NEWSLETTER_FOOTER_HEIGHT-10);
		this.header.sender.adjust('right', -200);
		this.header.viewSwitchButton.set('title', 'Newsletter');
		
		var itemViews = App.getPath('flowsPage.mainPane.conversation.scroll.contentView._sc_itemViews');
		if( itemViews ) 
			itemViews.forEach(function(item) { 
				item.adjust('width', App.CONVERSATION_PANEL_WIDTH);
				item.adjust('left', 0); 
			});
	},
	adjustToNewsletterLayout: function() {
		this.scroll.adjust('bottom', App.NEWSLETTER_FOOTER_HEIGHT);
		this.footer.adjust('bottom', 0);
		this.header.sender.adjust('right', App.CONVERSATION_SENDER_RIGHT);
		this.header.viewSwitchButton.set('title', 'Conversation');
		
		var itemViews = App.getPath('flowsPage.mainPane.conversation.scroll.contentView._sc_itemViews');
		if( itemViews ) 
			itemViews.forEach(function(item) { 
				item.adjust('width', App.CONVERSATION_VIEW_ITEM_CONTACT_COLUMN_WIDTH
						+App.CONVERSATION_PANEL_WIDTH);
				item.adjust('left', -App.CONVERSATION_VIEW_ITEM_CONTACT_COLUMN_WIDTH); 
			});
	},
	
	adjustToShow: function() {
		this.adjust('width', App.CONVERSATION_PANEL_WIDTH);
	},
	
	contentDidChange: function() {
		var contact = App.getPath('conversationController.key_participant.contact');
		console.log('content.key_participant.contact=%@'.fmt(contact));
		if( contact ) {
			this.set('senderName', contact.get('name'));
			this.set('contact', contact);
			
			if( contact.get('type') === App.model.Contact.PERSON ) {
				this.adjustToConversationLayout();
			} else {
				this.adjustToNewsletterLayout();
			}
		}
	}.observes('content')
});

