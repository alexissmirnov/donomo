// ==========================================================================
// Project:   Signup - mainPage
// Copyright: ©2009 Apple Inc.
// ==========================================================================
/*globals Signup */

// This page describes the main user interface for your application.  
Signup.mainPage = SC.Page
		.design( {

			// The main pane is made visible on screen as soon as your app is
			// loaded.
			// Add childViews to this pane for views to display immediately on
			// page
			// load.
			mainPane : SC.MainPane
					.design( {
						childViews : 'descLabel working'.w(),

						// setting default responder to the app namespace causes
						// general actions
						// to fire on the current first responder for signup
						defaultResponder : 'Signup',

						working : SC.View
								.design( {
									classNames : "working",
									layout : {
										left : 280,
										top : 50,
										bottom : 50,
										right : 50
									},

									childViews : "addAccountButton container removeAllAccountsButton"
											.w(),

									// the main container. swaps between a
									// signup prompt and the current
									// signup info.
									container : SC.ContainerView
											.design( {
												lengthDidChange : function() {
													if (Signup.accountsController
															.length() > 0)
														this.set('nowShowing',
																'accounts');
													else
														this.set('nowShowing',
																'prompt');
												}
														.observes('Signup.accountsController.length'),

												layout : {
													left : 20,
													top : 20,
													bottom : 60,
													right : 20
												}
											}),

									// the signup button used to trigger the
									// dialog. note that the action
									// goes down the responder chain and ends up
									// firing on the
									// application firstResponder
									addAccountButton : SC.ButtonView.design( {
										layout : {
											bottom : 20,
											centerX : 55,
											width : 100,
											height : 24
										},
										title : 'Add Accoount',
										isDefault : YES,
										action : "addAccount"
									}),

									// the logout button removes the current
									// user account. It is only
									// enabled if we have an account.
									removeAllAccountsButton : SC.ButtonView
											.design( {
												layout : {
													bottom : 20,
													centerX : -55,
													width : 100,
													height : 24
												},
												title : 'Remove all accounts',
												action : 'removeAllAccounts',

												isEnabledBinding : "Signup.accountsController.length"
											})

								}),

						descLabel : SC.LabelView
								.design( {
									layout : {
										top : 50,
										left : 40,
										width : 220,
										bottom : 50
									},
									escapeHTML : NO,
									classNames : 'desc',
									value : '<h1>Creating a user profile and managing accounts.</h1><p><ul><li>Click "Add Account"</li><li>Complete the form and press "Done"</li><li>Repeat.</li></u></p>'
								})
					}),

			prompt : SC.LabelView.design( {
				tagName : "h2",
				classNames : "prompt",
				textAlign : SC.ALIGN_CENTER,
				controlSize : SC.HUGE_CONTROL_SIZE,
				layout : {
					left : 0,
					right : 0,
					height : 24,
					centerY : 0
				},
				value : 'No Accounts created. Add one'
			}),

			accounts : SC.ScrollView
					.design( {
						hasHorizontalScroller : NO,
						layout : {
							top : 0,
							bottom : 0,
							left : 0,
							right : 0
						},
						backgroundColor : 'white',
						contentView : SC.ListView
								.design( {
									contentBinding : 'Signup.accountsController.arrangedObjects',
									contentValueKey : 'name'
								})
					})
		});
