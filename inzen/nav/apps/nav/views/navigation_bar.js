/**
 * Vertiral left-side navigation bar. Holds buttons that change what's
 * shown on the main surface
 */
App.NavigationButton = SC.ButtonView.extend({
	classNames: 'navbutton'.w()
});

App.NavigationBar = SC.View.extend({
	classNames: 'navbar'.w(),
	
	childViews: 'all profile codeVersion cacheVersion currentState'.w(),
	
	all: SC.ButtonView.design({
        classNames: 'all'.w(),
        layout: { left: 0, top: 100, width: 45, height: 45 },
        title: null,
        titleMinWidth: 0,
        controlSize: SC.JUMBO_CONTROL_SIZE,
        icon: '/media/img/all_button.png'
    }),
	profile: SC.ButtonView.design({
        classNames: 'profile'.w(),
        layout: { left: 0, bottom: 10, width: 45, height: 45 },
        title: null,
        titleMinWidth: 0,
        controlSize: SC.JUMBO_CONTROL_SIZE,
        icon: '/media/img/profile_button.png',
        
        action: 'showProfilePage'
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
    }),
    
    showProfilePage: function() {
		App.state.transitionTo(App.state.PROFILE_PAGE);
    }
});
