sc_require('responders/state');
sc_require('views/conversation_view');
sc_require('views/navigation_bar');


App.NAVBAR_WIDTH = 45;

// This page describes the main user interface for your application.  
App.flowsPage = SC.Page.design({
	mainPane: SC.MainPane.design({
		NAVIGATION_BAR_WIDTH: 45,
		
		classesName: 'flow-pane'.w(),
		childViews: 'navigationBar flows conversation'.w(),

		navigationBar: App.NavigationBar.design({
			layout: {top: 0, left: 0, bottom: 0, width: App.NAVBAR_WIDTH}
		}),

	    flows: App.DashboardScrollView.design({
	    	layout: {top:0,right:0,bottom:0,left: App.NAVBAR_WIDTH}
	    }),
	    
	    conversation: App.ConversationPanel.design(SC.Animatable, {
	    	classNames: 'conversation-panel'.w(),
	    	layout: {top: 0, bottom: 0, right: 0, width: 0 }, // initially hidden (width: 0)
	    	transitions: {
	    		 width: { duration: .25, timing: SC.Animatable.TRANSITION_EASE_IN_OUT } // with timing curve
	    	},
	    	contentBinding: 'App.conversationController.content'
	    })
	})
});
