// ==========================================================================
// Project:   Nav - mainPage
// Copyright: ©2010 My Company, Inc.
// ==========================================================================
/*globals Nav */

// This page describes the main user interface for your application.  
Nav.flowPage = SC.Page.design({

  // The main pane is made visible on screen as soon as your app is loaded.
  // Add childViews to this pane for views to display immediately on page 
  // load.
	mainPane: SC.MainPane.design({
			// setting default responder to the app namespace causes general actions
			// to fire on the current first responder for signup
			defaultResponder: Nav,    

			childViews: 'welcomeLabel home'.w(),
    
			welcomeLabel: SC.LabelView.design({
				layout: { centerX: 0, top: 50, width: 200, height: 18 },
				textAlign: SC.ALIGN_CENTER,
				tagName: "h1", 
				value: "This is a lif of messages that belong to a flow"
			}),

			home: SC.ButtonView.design({
				layout: { centerX: 0, centerY: 0, width: 200, height: 44 },
				textAlign: SC.AUTO_CONTROL_SIZE,
				title: "go to main page",
				isDefault: YES,
				action: 'go',
				target: Nav.states.main,
				location: 'main'				
			})
		})
	});
