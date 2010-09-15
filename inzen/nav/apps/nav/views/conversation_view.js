
/******************************************************************************
 *  @class
 * @extends View
*/
Nav.ConversationItemView = SC.View.extend(SC.StaticLayout, {
    classNames: 'conversation-item'.w(),
    useStaticLayout: YES,

    childViews: [
    SC.LabelView.design({
        classNames: 'conversation-item--contact'.w(),
        layout: {
            left: 0,
            width: 100
        },
        textAlign: SC.ALIGN_RIGHT,
        valueBinding: '.parentView.content.sender_address.contact.name'
    }),
    SC.StaticContentView.design({
        classNames: 'conversation-item--body'.w(),
        layout: {
            left: 140,
            width: 550
        },
        contentBinding: '.parentView.content.body'
    })
    ]
});


/******************************************************************************
 *  @class

  @extends SC.View
*/
Nav.ConversationContentView = SC.StackedView.extend({
	contentBinding: 'Nav.conversationController.messages', // content is one an array of messages
	exampleView: Nav.ConversationItemView
});

/******************************************************************************
 *  @class ConversationScrollView
 *  Assumes content will be set to a conversation object
 *  @extends SC.ScrollView
*/
Nav.ConversationScrollPanel = SC.ScrollView.extend({
	classNames: 'conversation-content'.w(),
	// make sure the view doesn't react to side-ways swipes
	alwaysBounceHorizontal: NO,
	contentView: Nav.ConversationContentView.design({})
});

Nav.ConversationPanel = SC.View.extend({
	childViews: 'scroll close'.w(),
	close: SC.ButtonView.design({
        layout: {top:0,right:0,height:20,width:20},
        title: 'X',
        action: 'showFlowsFullScreen',
        target: Nav.states.flows
      }),
	scroll: Nav.ConversationScrollPanel.design({
		layout: {top:10},
		contentBinding: '.parentView.content'
	})
});

