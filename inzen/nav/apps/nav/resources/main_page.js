// ==========================================================================
// Project:   Nav - mainPage
// Copyright: ©2010 My Company, Inc.
// ==========================================================================
/*globals Nav */

// This page describes the main user interface for your application.  
Nav.mainPage = SC.Page.design({

  // The main pane is made visible on screen as soon as your app is loaded.
  // Add childViews to this pane for views to display immediately on page 
  // load.
	mainPane: SC.MainPane.design({
			// setting default responder to the app namespace causes general actions
			// to fire on the current first responder for signup
			defaultResponder: Nav,    

			childViews: 'welcomeLabel signupButton'.w(),
    
			welcomeLabel: SC.LabelView.design({
				layout: { centerX: 0, top: 50, width: 200, height: 18 },
				textAlign: SC.ALIGN_CENTER,
				tagName: "h1", 
				value: "This is a mock-up of inzen's navigation elements."
			}),

			signupButton: SC.ButtonView.design({
				layout: { centerX: 0, centerY: 0, width: 200, height: 44 },
				textAlign: SC.AUTO_CONTROL_SIZE,
				title: "go to signup",
				isDefault: YES,
				action: 'go',
				target: Nav.states.main,
				location: 'signup'				
			})
		})
	});
