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
		childViews: 'mainSurface codeVersion cacheVersion currentState'.w(),

		mainSurface: App.MainSurface.design({
			layout: {top: 0, left: 0, bottom: 0, right: 0}
		}),
	    codeVersion: SC.LabelView.design({
	    	controlSize: SC.SMALL_CONTROL_SIZE,
	    	valueBinding: 'App.VERSION',
	    	layout: { left: 0, top: 0, width: 45, height: 10 }
	    }),
	    cacheVersion: SC.LabelView.design({
	    	controlSize: SC.SMALL_CONTROL_SIZE,
	    	valueBinding: 'App.schemaVersionController.version',
	    	layout: { left: 0, top: 15, width: 45, height: 10 }
	    }),
	    currentState: SC.LabelView.design({
	    	controlSize: SC.SMALL_CONTROL_SIZE,
	    	valueBinding: 'App.firstResponder.name',
	    	layout: { left: 0, top: 30, width: 45, height: 10 }
	    })
		
	})
});

