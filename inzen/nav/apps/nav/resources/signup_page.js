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





