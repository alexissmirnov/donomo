/** @class

  This controller represents the profile object that is actually handled by this view.

  @extends SC.ObjectController
*/
Nav.profileController = SC.ObjectController.create();

/**
 * Profile view
 */

Nav.ProfileView = SC.View.extend(SC.Animatable, {
	classNames: 'profile-view'.w(),
	// initially positioned off screen
	transitions: {
		left: { duration: .2, timing: SC.Animatable.TRANSITION_EASE_OUT } // with timing curve
	},
	layout: {top: 0, bottom: 0, width: 568, left: -608}, // off screen to the left, including 40px for the shadow
	finalLayout: {left: 200},
	
	childViews: 'prompt credentials gmail yahoo hotmail imap twitter linkedin'.w(),
	
	prompt: SC.LabelView.design(SC.Animatable, {
		classNames: 'profile-view-prompt'.w(),
		transitions: {
			top: { duration: .25, timing: SC.Animatable.TRANSITION_EASE_IN_OUT }
		},
		layout: {top: 200, left: 30},
		finalLayout: {top: 10},
		value: 'Select an account to add'
	}),
	
	credentials: SC.View.design(SC.Animatable, {
		classNames: 'profile-view-credentials'.w(),
		transitions: {
			height: { duration: .25, timing: SC.Animatable.TRANSITION_EASE_IN_OUT }
		},
		layout: {top: 180, height: 0},
		finalLayout: {height: 210},
		childViews: 'form loading'.w(),
		form: SC.FormView.design({
			layout: {left: 10, top: 5, right: 10},
			labelWidth: 100,
			//
			//flowPadding: { left: 10, top: 5, right: 10 },
			theme: 'iphone-form',
			classNames: 'profile-view-credentials-form'.w(),
		
			childViews: 'email password submit'.w(),
		  
			email: SC.FormView.row(SC.TextFieldView.design({
				layout: { left: 0, width: 300, height: 44, centerY: 0},
				hint: 'steve@gmail.com',
				valueBinding: 'App.state.MANAGING_PROFILE.controller.name'
			}), { classNames: ['first'] }),
			
			password: SC.FormView.row(SC.TextFieldView.design({
				layout: { left: 0, width: 300, height: 44, centerY: 0},
				valueBinding: 'App.state.MANAGING_PROFILE.controller.password',
				isPassword: YES
			}), { classNames: ['last'] }),
			
			submit: SC.ButtonView.design({
				controlSize: SC.HUGE_CONTROL_SIZE,
				layout: { width: 100, height: 44, bottom: 5, left: 5 },
				title: 'Done',
				isDefault: YES,
				action: 'onSubmit'
			})
		}),
		loading: SC.LabelView.design(SC.Animatable, {
			classNames: 'profile-view-credentials-loading'.w(),
			transitions: {
				opacity: { duration: .3, timing: SC.Animatable.TRANSITION_EASE_IN }
			},
			layout: {bottom: 65, height: 44, width: 200, right: 0},
			textAlign: SC.ALIGN_CENTER,
			icon: 'profile-view-credentials-loading-icon',
			value: 'Loading...',
			style: {opacity: 0.0 }, // fully transparent initially
			finalStyle: {opacity: 1.0}
		})

	}),

	gmail: SC.View.design(SC.Animatable, {
		classNames: 'profile-view-account profile-view-gmail'.w(),
		transitions: {
			top: { duration: .25, timing: SC.Animatable.TRANSITION_EASE_IN_OUT }
		},
		layout: {top: 400, left: 30, width: 140, height: 140},
		finalLayout: {top: 30},
	    click: function(evt) {
			this.touchEnd();
		},
		touchStart: function(evt) {
			return YES;
		},
		touchEnd: function(evt) {
			this.adjust('top', this.finalLayout.top);
			this.parentView.prompt.adjust('top', this.parentView.prompt.finalLayout.top);
			this.parentView.credentials.adjust('height', this.parentView.credentials.finalLayout.height);
		}		
	}),
	yahoo: SC.View.design({
		classNames: 'profile-view-account profile-view-yahoo'.w(),
		layout: {top: 400, left: 200, width: 140, height: 140} // 200 = 140 + 30 + 30
	}),
	hotmail: SC.View.design({
		classNames: 'profile-view-account profile-view-hotmail'.w(),
		layout: {top: 400, left: 370, width: 140, height: 140} // 370 = 2*140 + 3*30
	}),
	imap: SC.View.design({
		classNames: 'profile-view-account profile-view-imap'.w(),
		layout: {top: 570, left: 30, width: 140, height: 140}, // 470 = 300 + 140 + 30
		childViews: [SC.LabelView.design({
			layout: {top: 70},
			textAlign: SC.ALIGN_CENTER,
			fontWeight: SC.BOLD_WEIGHT,
			value: 'IMAP'
		})]
	}),	
	twitter: SC.View.design({
		classNames: 'profile-view-account profile-view-twitter'.w(),
		layout: {top: 570, left: 200, width: 140, height: 140}
	}),	
	linkedin: SC.View.design({
		classNames: 'profile-view-account profile-view-linkedin'.w(),
		layout: {top: 570, left: 370, width: 140, height: 140}
	}),	
	
	
	showView: function() {
		this.adjust('left', this.finalLayout.left);
	},
	onSubmit: function() {
		this.credentials.loading.adjust('opacity', 1.0);
		App.state.MANAGING_PROFILE.submit();
	},

	hideView: function() {
		this.adjust('left', this.layout.left);
		this.removeFromParent();
	}
});