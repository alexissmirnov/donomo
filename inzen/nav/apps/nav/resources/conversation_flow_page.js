// ==========================================================================
// Project:   Nav - mainPage
// Copyright: ©2010 My Company, Inc.
// ==========================================================================
/*globals Nav */
require('responders/state');
require('responders/flow');
require('controllers/controllers');
require('views/conversation_view');

/*jslint undef: true */


// This page describes the main user interface for your application.  
App.conversationFlowPage = SC.Page.design({

  // The main pane is made visible on screen as soon as your app is loaded.
  // Add childViews to this pane for views to display immediately on page 
  // load.
	mainPane: SC.MainPane.design({
			// setting default responder to the app namespace causes general actions
			// to fire on the current first responder for signup
			defaultResponder: App.state.FLOW,

			childViews: [
				SC.MasterDetailView.design({
					autoHideMaster: YES,
					layout: { left: 0, top: 0, right: 0, bottom: 0 },
					
					masterView: SC.WorkspaceView.design({
				        topToolbar: SC.ToolbarView.design(SC.Animatable, {
				            masterIsHidden: NO,
				            
				            layout: { top: 0, right: 0, left: 0, height: 44 },
				            
				            style: {
				              display: 'block',
				              opacity: 0.9
				            },
				            transitions: {
				              display: 0.2,
				              opacity: 0.1
				            },
				            
				            isShowing: YES,
				            
				            autoResize: NO,
				            childViews: [
					            SC.LabelView.design({
						              useAbsoluteLayout: YES,
						              layout: { left: 100, right: 0, centerY: 0, height: 20 },
						              textAlign: SC.ALIGN_LEFT,
						              valueBinding: 'App.conversationsBrowserController.flowName'
					            }),
					            SC.ButtonView.design({
					                layout: { left: 10, top: 0, width: 80, height: 44 },
					                controlSize: SC.REGULAR_CONTROL_SIZE,
					                title: 'Flows',
					                theme: 'point-left',
						            action: function() { App.state.transitionTo('FLOWS'); }
					            })
				            ]
				        }),
						contentView: SC.ScrollView.design({
							contentView: SC.SourceListView.design({
								contentBinding: 'App.conversationsBrowserController.arrangedObjects',
								selectionBinding: 'App.conversationsBrowserController.selection',
								exampleView: App.ConversationListItemView,
								rowHeight: 100,
								rowSpacing: 5
							})
						})
					}),
					detailView: SC.View.design({
						classNames: 'conversation'.w(),
						childViews: 'contentView topToolbar'.w(),
	
						masterIsHidden: NO,
				        masterIsHiddenDidChange: function() { 
				          this.topToolbar.set('masterIsHidden', this.get('masterIsHidden'));
				        }.observes('masterIsHidden'),
						
				        contentView: App.ConversationPanel.design({
				        	layout: { top: 44, right: 0, left: 0, bottom: 0 },
				        	contentBinding: 'App.conversationsBrowserController.selectionMessages'
				        }),
				        
				        topToolbar: SC.ToolbarView.design(SC.Animatable, {
				            masterIsHidden: NO,
				            
				            layout: { top: 0, right: 0, left: 0, height: 44 },
				            
				            style: {
				              display: 'block',
				              opacity: 0.9
				            },
				            transitions: {
				              display: 0.2,
				              opacity: 0.1
				            },
				            
				            isShowing: YES,
				            
				            autoResize: NO,
				            childViews: [
					            SC.LabelView.design({
									useAbsoluteLayout: YES,
									layout: { left: 0, right: 0, centerY: 0, height: 20 },
									textAlign: SC.ALIGN_CENTER,
									valueBinding: 'App.conversationController.subject'
						        }),
						        SC.ButtonView.design({
					                layout: { left: 10, top: 0, width: 44, height: 44 },
					                theme: 'icon',
					                icon: 'previous',
					                isEnabled: NO,
					                isEnabledBinding: 'App.conversationsBrowserController.hasPreviousConversation',
					                action: 'previousConversation'
					            }),
					            SC.ButtonView.design({
					                layout: { right: 10, top: 0, width: 44, height: 44 },
					                theme: 'icon',
					                icon: 'next',
					                action: 'nextConversation',
					                isEnabled: NO,
					                isEnabledBinding: 'App.conversationsBrowserController.hasNextConversation'
					            }),
					            SC.ButtonView.design({
									layout: { left: 64, width: 100, height: 44 },
									titleBinding: 'App.conversationsBrowserController.flowName',
									theme: 'chromeless',
									isVisible: NO,
									action: 'toggleMasterPicker',
									isVisibleBinding: '.parentView.masterIsHidden'
					            })
					        ]
				        })
					})
				})
			]
		})
	});

