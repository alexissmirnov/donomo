require('responders/state');

/**
 * 
 * The active state when the signup dialog is showing.
 * 
 * @extends SC.Responder
 */
App.state.MANAGING_PROFILE = SC.Responder.create( {
	name: 'MANAGING_PROFILE',
	
	/**
	 * Holds the view that is used to manage profile. We keep it here in oder to
	 * know which view to remove/hide when we transition out of this state
	 */
	_provileView: null,
	
	// when we become first responder, always show the signup panel
	didBecomeFirstResponder : function() {
		// initialize the internal controller with a temporary object
		// the view will use this controller for editing
		// TODO: find a way to create an uncommited Account model
		// nested store?
		App.state.MANAGING_PROFILE.controller.set('content', {
			email : null,
			password : null,
			accountClass: 'email/gmail' //TODO
		});

		// then show profile pane
		this._provileView = App.ProfileView.create();
		var pane = App.getPath('mainPage.mainPane');
		pane.appendChild(this._provileView); // append
		this._provileView.invokeLast('showView'); // reveal the view (runs any kind of animaiton the view needs to show up)
	},

	// when we lose first responder, always hide the signup panel.
	willLoseFirstResponder : function() {
		 // cleanup controller
		App.state.MANAGING_PROFILE.controller.set('content', null);
		this._provileView.hideView();
	},

	// called when the OK button is pressed.
	submit : function() {
		account = App.state.MANAGING_PROFILE.controller.get('content');
		App.store.createRecord(App.model.Account, account);

		/*
		 * Don't transition to FLOWS here because it will be done by userController
		 * The creation of the account will lead to pushing of this account to the server,
		 * which may create a User object and return it back.
		 * userController is watching for this event and will transition to FLOWS
		 */
		//TODO: transition to "LOADING_FLOWS" state
	}
});
App.state.MANAGING_PROFILE.controller = SC.ObjectController.create();