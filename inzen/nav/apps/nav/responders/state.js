/**
 * Program state management
 * 
 * 
 */
App.state = {
	/**
	 * Wraps makeFirstResponder. Transitions to a given state. Apart from making
	 * the state the first responder, this function is also setting the state
	 * name as a URL location This function is called by the routeHandler when
	 * the URL changes as well as any space where a state change is made.
	 * 
	 * @param stateName
	 * @returns
	 */
	transitionTo: function(state) {			
		if( SC.typeOf(state) === SC.T_HASH ) {
			state = state.location;
		}
		
		if( SC.typeOf(state) === SC.T_STRING ) {
			// Is there such a state?
		    if (!App.state.hasOwnProperty(state)) {
		    	console.log("App.state.transitionTo can't find state %@. Will transition to state START"
								.fmt(state));
		    	state = App.state.START;
		    }
		    else {
		    	// get the object by name
		    	state = App.state[state];
		    }
		}

		// Already in this state? Do nothing then.
		if( App.firstResponder && App.firstResponder === state)
			return state;
		
	    SC.routes.set('location', state.get('name'));
	    document.title = state.get('name');

	    App.makeFirstResponder(state);
		return state;
	},

	/**
	 * Single route handles that gets all route changes. The route name (URL's
	 * fragment) is assumed to be the state name. This routing handler as was
	 * set in main.js and is called by the SC routing when location changes
	 */
	routeHandler: function (route) {
		this.transitionTo(route);
	}
};
