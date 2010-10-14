App.CONVERSATION_VIEW_ITEM_CONTACT_COLUMN_WIDTH = 140;
App.CONVERSATION_PANEL_WIDTH = 724;
App.NEWSLETTER_HEADER_HEIGHT = 40;
App.NEWSLETTER_FOOTER_HEIGHT = 30;

App.SenderContactLabel = SC.View.extend({
	childViews: [
	    SC.LabelView.design({
	    	layout: {top: 20, left: 5, right: 0, height: 20},
	        textAlign: SC.ALIGN_LEFT,
	    	valueBinding: '.parentView.parentView.content.sender_address.contact.name'
	    }),
	    SC.ButtonView.design({
	    	layout: {top: 50, left: 5, right: 0, height: 25},
	    	title: 'Newsletter',
	    	action: 'setCurrentSenderAsNewsletter',
	    	contentBinding: '.parentView.parentView.content.sender_address.contact',
	    	setCurrentSenderAsNewsletter: function() {
	    		App.state.FLOWS.setCurrentSenderAsNewsletter(this.get('content'));
	    	}
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
	exampleView: App.ConversationItemView
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


App.NewsletterHeaderView = SC.View.extend({
	classNames: 'app-newsletter-header'.w(),
	
    layout: {
		top: 0, 
		right: 0, 
		left: 0, 
		height: App.NEWSLETTER_HEADER_HEIGHT
	},
    childViews: 'subject sender'.w(),
    subject: SC.LabelView.design({
    	classNames: 'app-newsletter-header-sender'.w(),
    	layout: {top: 0, left: 5, height: 20},
    	valueBinding: 'App.conversationController.subject'
    }),
    sender: SC.LabelView.design({
    	classNames: 'app-newsletter-header-sender'.w(),
    	layout: {top: 0, right: 5, height: 20},
    	valueBinding: 'App.conversationController.key_participant'
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
		layout: {top: App.NEWSLETTER_HEADER_HEIGHT}
	}),
    header: App.NewsletterHeaderView.design({
    }),
	footer: App.NewsletterFooterView.design({
    }),
	close: SC.ButtonView.design({
        layout: {top:0,right:0,height:20,width:20},
        title: 'X',
        action: 'showFlowsFullScreen',
        target: App.state.FLOWS
      }),
	
	adjustToNewsletterLayout: function() {
		var itemViews = App.getPath('flowsPage.mainPane.conversation.scroll.contentView._sc_itemViews');
		this.scroll.adjust('bottom', App.NEWSLETTER_FOOTER_HEIGHT);
		this.footer.adjust('bottom', 0);
		
		itemViews.forEach(function(item) { 
			item.adjust('width', App.CONVERSATION_VIEW_ITEM_CONTACT_COLUMN_WIDTH
					+App.CONVERSATION_PANEL_WIDTH);
			item.adjust('left', -App.CONVERSATION_VIEW_ITEM_CONTACT_COLUMN_WIDTH); 
		});
	},
	
	adjustToShow: function() {
		this.adjust('width', App.CONVERSATION_PANEL_WIDTH);
	}
});

