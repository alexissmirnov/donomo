require('views/conversation_view');
require('views/profile_view');




// This page describes the main user interface for your application.  
Nav.mainPage = SC.Page.design({

  // Add childViews to this pane for views to display immediately on page 
  // load.
	mainPane: SC.MainPane.design({
	        classNames: 'main-pane'.w(),
			//defaultResponder: Nav.states.main,
			childViews: 'welcomeLabel statusLabel'.w(),
    
			welcomeLabel: SC.StaticContentView.design({
				layout: { centerX: 0, centerY: 0, width: 200, height: 44 },
				content: 'Touch the profile button to get started.'
			}),
			statusLabel: SC.StaticContentView.design({
				layout: {bottom: 0, left: 0, width: 200, top: 400},
				contentBinding: 'App.userController.username'
			})
			
		})
});

