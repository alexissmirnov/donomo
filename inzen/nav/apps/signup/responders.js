/* globals Signup */

/*---------------------------------------------------------------------------*/
Signup.START = SC.Responder.create( {
	didBecomeFirstResponder : function() {
		var store = SC.Store.create( {
			commitRecordsAutomatically : YES
		}).from(LawnchairSC.DataSource.create({
				nestedDataSource: 'Signup.ServerDataSource'
			}));
		Signup.set('store', store);

		this.invokeLater(function() {
				Signup.accountsController.set('content', Signup.store.find(SC.Query.local(Signup.Account)));
			}, 2000);
		this.invokeLater(function() {
				Signup.userController.set('content', Signup.store.find(SC.Query.local(Signup.User)));
			}, 4000);
		this.invokeLater(function() {
				Signup.messagesController.set('content', Signup.store.find(SC.Query.local(Signup.Message)));
			}, 6000);
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
		ids = [];
		Signup.accountsController.arrangedObjects().forEach(function(o) {
			ids.pushObject(o.get('id'));
		});
		Signup.store.destroyRecords(Signup.Account, ids);
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