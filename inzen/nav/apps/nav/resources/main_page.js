require('views/conversation_view');
require('views/profile_view');
sc_require('views/navigation_bar');
sc_require('views/main_surface');




// This page describes the main user interface for your application.  
App.mainPage = SC.Page.design({
	// Add childViews to this pane for views to display immediately on page 
	// load.
	mainPane: SC.MainPane.design({
        classNames: 'main-pane'.w(),
		childViews: 'mainSurface'.w(),

		mainSurface: App.MainSurface.design({
			layout: {top: 0, left: 0, bottom: 0, right: 0}
		})
	})
});

