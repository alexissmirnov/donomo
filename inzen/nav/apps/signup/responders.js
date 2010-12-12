/* globals Signup */

App = Signup;


/*---------------------------------------------------------------------------*/
Signup.START = SC.Responder.create( {
	didBecomeFirstResponder : function() {
		var store = SC.Store.create( {
			commitRecordsAutomatically : YES
		}).from(LawnchairSC.DataSource.create({
				nestedDataSource: 'Signup.ServerDataSource'
			}));
		Signup.set('store', store);

		Signup.accountsController.set('content', App.Account.objects().all().get('content'));
		Signup.userController.set('content', App.User.objects().all().get('content'));
		Signup.messagesController.set('content', App.Message.objects().all().get('content'));
	}
});
/*---------------------------------------------------------------------------*/

/**
 * @namespace
 * 
 * The default responder state. This is the normal state while we wait for the
 * user to click on the signup button.
 * 
 * @extends SC.Responder
 */
Signup.READY = SC.Responder.create( {

	/** called when the user clicks on the signup button */
	addAccount : function() {
		Signup.makeFirstResponder(Signup.ADDING_ACCOUNT); // show account dialog
	},

	/** called when the user clicks on the logout button. */
	removeAllAccounts : function() {
		App.User.objects().all().del();
		App.Account.objects().all().del();
		App.Message.objects().all().del();
	},

	hasAccounts : function() {
		return !SC.none(this.get('content'));
	}

});

/*---------------------------------------------------------------------------*/
/**
 * 
 * The active state when the signup dialog is showing.
 * 
 * @extends SC.Responder
 */
Signup.ADDING_ACCOUNT = SC.Responder.create( {
	// when we become first responder, always show the signup panel
	didBecomeFirstResponder : function() {
		// the view will use this controller for editing
		Signup.ADDING_ACCOUNT.controller.set('content', {
			email : null,
			password : null,
			accountClass: 'email/gmail' //TODO: find a way to create an uncommited Account model
		});

		// then show the dialog
		var pane = Signup.getPath('newAccountPage.mainPane');
		pane.append(); // show on screen
		pane.makeFirstResponder(pane.contentView.email); // focus first
		// field
	},

	// when we lose first responder, always hide the signup panel.
	willLoseFirstResponder : function() {
		 // cleanup controller
		Signup.ADDING_ACCOUNT.controller.set('content', null);
		Signup.getPath('newAccountPage.mainPane').remove();
	},

	// called when the OK button is pressed.
	submit : function() {
		account = Signup.ADDING_ACCOUNT.controller.get('content');
		var accountRecord = Signup.store.createRecord(Signup.Account, account);

		Signup.makeFirstResponder(Signup.READY);
	},

	// called when the Cancel button is pressed
	cancel : function() {
		Signup.makeFirstResponder(Signup.READY);
	}
});
Signup.ADDING_ACCOUNT.controller = SC.ObjectController.create();