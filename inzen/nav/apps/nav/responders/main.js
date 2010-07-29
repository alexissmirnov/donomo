Nav.states = {};

Nav.states.main = SC.Responder.create({
	go: function(fragment) {
		var fragmentParts, stateLocation; 
	    
		// fragment could be a string when this function is called directly
		// by the url 'route'
		// or an object when it is called by a button.
		if (SC.typeOf(fragment) !== SC.T_STRING) {
			fragmentParts = fragment.get('location').split('/');
		}
		else {
			fragmentParts = fragment.split('/');
		}
		stateLocation = fragmentParts[0];
		
	    if (!Nav.states.hasOwnProperty(stateLocation)) {
	      stateLocation = 'main';
	    }
		
	    SC.routes.set('location', fragment);
	    document.title = "inzen - %@".fmt(stateLocation.titleize());
	    // TODO explain what's going on here
	    // passing a 'URL' to the state
	    Nav.states[stateLocation].set('resource', fragmentParts[1]);
    	Nav.makeFirstResponder(Nav.states[stateLocation]);
    	return Nav.states[stateLocation];
	},
	
	// rousing handler as was set in main.js
	// caleld by the SC routing when location changes
	route: function (route) {
		this.go(route.stateLocation);
	},
	
	willLoseFirstResponder: function () {
		Nav.getPath('mainPage.mainPane').remove();
	},
	
	didBecomeFirstResponder: function () {
		Nav.getPath('mainPage.mainPane').append();
	},
	
	// bound to 'signup' button on the main page
	onSignup: function () {
		Nav.makeFirstResponder(Nav.states.signup);
	}
});
