require('responders/state');

/**
 * 
 * The active state when the profile panel is showing
 * 
 * @extends SC.Responder
 */
App.state.PROFILE_PAGE = SC.Responder.create( {
	name: 'PROFILE_PAGE',
	
	// when we become first responder, always show the signup panel
	didBecomeFirstResponder : function() {
		App.getPath('profilePage.mainPane').append();
	},
	// when we lose first responder, always hide the signup panel.
	willLoseFirstResponder : function() {
		App.getPath('profilePage.mainPane').remove();
	}
});