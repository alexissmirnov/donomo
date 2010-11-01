sc_require('responders/state');
sc_require('views/navigation_bar');


App.NAVBAR_WIDTH = 45;

// This page describes the main user interface for your application.  
App.profilePage = SC.Page.design({
	mainPane: SC.MainPane.design({
		classesName: 'profile-pane'.w(),
		childViews: 'navigationBar profilePanel'.w(),

		navigationBar: App.NavigationBar.design({
			layout: {top: 0, left: 0, bottom: 0, width: App.NAVBAR_WIDTH}
		}),

		profilePanel: SC.LabelView.design(SC.Animatable, {
	    	classNames: 'profile-panel'.w(),
	    	layout: {top: 0, bottom: 0, left: 200, width: 568 },
	    	value: 'this is profile panel'
	    })
	})
});
