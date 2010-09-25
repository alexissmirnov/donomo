App.signupPage = SC.Page.design({
	// The main signup pane.  used to show info
	mainPane: SC.MainPane.design({
		childViews: 'form'.w(),
		form: SC.ScrollView.design({
		  delaysContentTouches: NO,
		  contentView: SC.FormView.design({
			labelWidth: 100,
			flowPadding: { left: 20, top: 10, bottom: 40, right: 20 },
		    theme: 'iphone-form',
		    classNames: ['signup_form'],

		    childViews: 'header name email password description submit cancel'.w(),
		  
		    header: SC.LabelView.design({
		      layout: { width: 400, height: 44 },
		      classNames: 'header'.w(),
		      value: '_Enter your email address and password'.loc()
		    }),
		  
		    name: SC.FormView.row(SC.TextFieldView.design({
			      layout: { left: 0, width: 300, height: 44, centerY: 0},
			      hint: 'John Zenseed'.loc(),
			      isSpacer: YES
			    }), { classNames: ['first'] }),

			email: SC.FormView.row(SC.TextFieldView.design({
			      layout: { left: 0, width: 300, height: 44, centerY: 0},
			      hint: '_email@example.com'.loc()
			    })),

		    password: SC.FormView.row(SC.TextFieldView.design({
			      layout: { left: 0, width: 300, height: 44, centerY: 0},
			      value: '',
			      isPassword: YES
			    })),
		    
		    description: SC.FormView.row(SC.TextFieldView.design({
			      layout: { left: 0, width: 300, height: 44, centerY: 0},
			      value: '',
			      hint: '_My work account'.loc(),
			      isSpacer: YES
			    }), { classNames: ['last'] }),
			    
		    submit: SC.ButtonView.design({
		        controlSize: SC.AUTO_CONTROL_SIZE,
		        layout: { height: 44, width: 100, centerY: 0 },
		        title: 'submit',
		        isDefault: YES,
		        action: function() { App.state.transitionTo('SENDER_CLASSIFICATION'); }
		      }),

		    cancel: SC.ButtonView.design({
		        controlSize: SC.AUTO_CONTROL_SIZE,
		        layout: { height: 44, width: 100, centerY: 0 },
		        title: 'cancel',
		        location: 'main',
		        action: function() { App.state.transitionTo('START'); }
		      })
		  })
		})
		})
});

//childViews: 'prompt okButton cancelButton emailLabel email passwordLabel password'.w(),
//
//prompt: SC.LabelView.design({
//    layout: { top: 12, left: 20, height: 18, right: 20 },
//    value: '_Enter your email address and password'.loc()
//    }),
//    
//// EMAIL
//emailLabel: SC.LabelView.design({
//	layout: { top: 68, left: 20, width: 70, height: 18 },
//	textAlign: SC.ALIGN_RIGHT,
//	value: '_Email:'.loc()
//	}),
//    
//email: SC.TextFieldView.design({
//	layout: { top: 68, left: 100, height: 20, width: 270 },
//	hint: '_email@example.com'.loc(),
//	valueBinding: 'App.signupController.email'
//	}),
//
//// PASSWORD
//passwordLabel: SC.LabelView.design({
//	layout: { top: 98, left: 20, width: 70, height: 18 },
//	textAlign: SC.ALIGN_RIGHT,
//	value: '_Password:'.loc()
//	}),
//    
//password: SC.TextFieldView.design({
//	layout: { top: 98, left: 100, height: 20, width: 270 },
//	valueBinding: 'App.signupController.password'
//	}),
//	
//// BUTTONS
//okButton: SC.ButtonView.design({
//	layout: { bottom: 20, right: 20, width: 90, height: 24 },
//	title: '_OK'.loc(),
//    isDefault: YES,
//    location: 'senderClassification',
//    action: 'go',
//    target: App.states.main
//}),
//
//cancelButton: SC.ButtonView.design({
//	layout: { bottom: 20, right: 120, width: 90, height: 24 },
//	title: '_Cancel'.loc(),
//	isCancel: YES,
//    location: 'main',
//    action: 'go',
//    target: App.states.main
//})




