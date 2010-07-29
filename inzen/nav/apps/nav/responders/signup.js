// ==========================================================================
// Project:   Nav
// Copyright: ©2009 Apple Inc.
// ==========================================================================
/*globals Nav */

require('responders/main');

/** @namespace

  The active state when the signup panel is showing.
  
  @extends SC.Responder
*/
Nav.states.signup = SC.Responder.create({
	didBecomeFirstResponder: function () {
		// Create a new user and set it as the root of the signup controller
		// so that we can edit it.
		var store, user, pane;
		
		this._store = Nav.store.chain(); // buffer changes
		store = this._store;
		user = store.createRecord(Nav.model.User, {}); // create a new user record
		Nav.signupController.set('content', user); // for editing

		// show signup page
		Nav.getPath('signupPage.mainPane').append();
	},
	
	willLoseFirstResponder: function () {
		// if we still have a store, then cancel first.
		if (this._store) {
			this._store.discardChanges();
			this._store = null;
		}
	
	    Nav.signupController.set('content', null); // cleanup controller	
		// remove signup page
		Nav.getPath('signupPage.mainPane').remove();
	},

	// called when the OK button is pressed.
	submit: function () {
		this._store.commitChanges();
		this._store = null;
    
		Nav.state.main.go('senderClassification');
	},
  
	// called when the Cancel button is pressed
	cancel: function () {
		this._store.discardChanges();
		this._store = null;
	
		// go back to root state
		Nav.state.main.go('main');
	}
});