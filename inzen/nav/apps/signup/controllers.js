// ==========================================================================
// Project:   Signup.signupController
// Copyright: ©2009 Apple Inc.
// ==========================================================================
/*globals Signup */
App = Signup;

Signup.userController = SC.ObjectController.create({
	  allowsMultipleContent: NO,
	  username: function() {
		  if( this.content && this.content.objectAt(0) )
			  return this.content.objectAt(0).get('username');
	  }.property()
});

Signup.messagesController = SC.ArrayController.create();

Signup.accountsController = SC.ArrayController.create( {
	/**
	 * The contents of this controller determine the state.
	 * If we have the content, we're in READY state. If we don't
	 * we need to prompt the user to create the account.
	 */
	contentDidChange : function(start, amt, delta) {
		var state = null;
		
		console.log('contentDidChange: ' + start + ' ' + amt + ' ' + delta);
		
		if (this.get('content') && this.get('content').length
				&& this.get('content').length() > 0) {
			state = Signup.READY;
			console.log('contentDidChange: ' + state);
		} else {
			state = Signup.ADDING_ACCOUNT;
			console.log('contentDidChange: ' + state);
		}
		Signup.makeFirstResponder(state);
	}.observes('content')
	
//	lengthDidChange: function() {
//		var user = Signup.userController.get('content');
//		var isCreatingUser = Signup.userController.get('isCreatingUser');
//		
//		if( this.length() > 0 && user.get('id') === undefined && isCreatingUser === NO) {
//			Signup.userController.set('isCreatingUser', YES);
//			console.log('create user');
//		}
//	}.observes('length')
});

