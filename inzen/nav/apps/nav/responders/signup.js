// ==========================================================================
// Project:   Nav
// Copyright: ©2009 Apple Inc.
// ==========================================================================
/*globals Nav */

require('responders/state');
require('views/profile_view');
/** @namespace

  The active state when the signup panel is showing.
  
  @extends SC.Responder
*/
App.state.SIGNUP = SC.Responder.create({
	didBecomeFirstResponder: function () {
		// Create a new user and set it as the root of the signup controller
		// so that we can edit it.
		var store, user, pane;
		
		this._store = App.store.chain(); // buffer changes
		store = this._store;
		user = store.createRecord(App.model.User, {}); // create a new user record
		App.signupController.set('content', user); // for editing

		// show signup page
		//App.getPath('signupPage.mainPane').append();
		App.profileView.showView();
	},
	
	willLoseFirstResponder: function () {
		// if we still have a store, then cancel first.
		if (this._store) {
			this._store.discardChanges();
			this._store = null;
		}
	
	    App.signupController.set('content', null); // cleanup controller	
		// remove signup page
		App.getPath('signupPage.mainPane').remove();
	},

	// called when the OK button is pressed.
	submit: function () {
		this._store.commitChanges();
		this._store = null;
    
		App.state.transitionTo('SENDER_CLASSIFICATION');
	},
  
	// called when the Cancel button is pressed
	cancel: function () {
		this._store.discardChanges();
		this._store = null;
	
		// go back to root state
		App.state.transitionTo('START');
	}
});