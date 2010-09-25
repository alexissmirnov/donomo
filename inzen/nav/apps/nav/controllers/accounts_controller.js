require('responders/state');

App.userController = SC.ObjectController.create({
	user: function() {
		return this.get('content').objectAt(0);
	},
	
	contentDidChange: function() {
		console.log('userController.contentDidChange. content=%@'.fmt(this.get('content')));
		if( this.get('content') && this.get('content').length() > 0 && this.content.objectAt(0).get('username')) {
			state = App.state.FLOWS;
			App.state.transitionTo(state);
		}
	}.observes('content')
	
});


App.accountsController = SC.ArrayController.create( {
	
	/**
	 * Invoked several times:
	 *  - length 0 when the App.accountsController instance is created. At this
	 * point App.firstResponder isn't set yet.
	 * 
	 *  - length 0 in START state when START state sets the 'content' property of this controller
	 *  
	 *  - length 1 when the DB query returns the data, for content 
	 *  
	 *  - length 1 AGAIN (bug?) TODO
	 * 
	 */
    enumerableContentDidChange: function(start, length) {
        arguments.callee.base.apply(this,arguments);
        
        console.log('accountsController.enumerableContentDidChange: len=%@, responder=%@'.fmt(length, App.firstResponder ? App.firstResponder.get('name') : 'none'));
		
		if( length == 0 && App.state ) {
			state = App.state.MANAGING_PROFILE;
			App.state.transitionTo(state);	
		}
		
		
    }
});