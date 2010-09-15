// ==========================================================================
// Project:   Nav
// ==========================================================================
require ('views/conversation_view');

/*globals Nav */

// This page describes the main user interface for your application.  
Nav.flowsPage = SC.Page.design({
	mainPane: SC.MainPane.design({
		classesName: 'flow-pane'.w(),
		childViews: 'topbar flows conversation'.w(),
    
	    topbar: SC.View.design({
	        classNames: 'topbar'.w(),
	        layout: { height: 45, left:0, top:0, right:0 },
	        childViews: 'logo settings'.w(),
	        
	        
	        settings: SC.ButtonView.design({
	            layout: {top:7,right:20,height:31,width:47},
	            title: 'settings',
	            action: 'go',
	            target: Nav.states.main,
	            location: 'settings'
	        }),
	        
	        logo: SC.ImageView.design({
	            canLoadInBackground: YES,
		          layout: {top:2, left:2, width:40, height:40},
		          value: '/media/img/inzen-logo-40.png'
		    })
	    }),
	    
	    flows: Nav.DashboardScrollView.design({
	    	layout: {top:45,right:0,bottom:0,left:0}
	    }),
	    
	    conversation: Nav.ConversationPanel.design(SC.Animatable, {
	    	classNames: 'conversation-panel'.w(),
	    	layout: {top: 55, bottom: 10, right: 0, width: 0 }, // initially hidden (width: 0)
	    	transitions: {
	    		 width: { duration: .25, timing: SC.Animatable.TRANSITION_EASE_IN_OUT } // with timing curve
	    	},
	    	contentBinding: 'Nav.conversationController.content.messages'
	    })
	})
});
