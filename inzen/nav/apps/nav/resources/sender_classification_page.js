// ==========================================================================
// Project:   Nav
// Copyright: ©2010 My Company, Inc.
// ==========================================================================
/*globals Nav */

// Sender classification as part of signup flow
Nav.senderClassificationPage = SC.Page.design({
	newFlowPage: SC.PanelPane.design({
		layout: { centerX: 0, centerY: 0, width: 400, height: 400 },
		childViews: 'form'.w(),
		form: SC.ScrollView.design({
		  delaysContentTouches: NO,
		  contentView: SC.FormView.design({
			labelWidth: 100,
			flowPadding: { left: 20, top: 10, bottom: 40, right: 20 },
		    theme: 'iphone-form',
		    classNames: ['signup_form'],

		    childViews: 'header name submit cancel'.w(),
		    contentBinding: 'Nav.senderClassificationController.flow',
		    
		    header: SC.LabelView.design({
		      layout: { width: 400, height: 44 },
		      classNames: 'header'.w(),
		      value: '_Enter the name of the flow'.loc()
		    }),
		    
		    name: SC.FormView.row(SC.TextFieldView.design({
			      layout: { left: 0, width: 300, height: 44, centerY: 0},
			      hint: 'Sport'.loc(),
			      isSpacer: YES
			    }), { classNames: ['first last'] }),
		    
		    submit: SC.ButtonView.design({
		        controlSize: SC.AUTO_CONTROL_SIZE,
		        layout: { height: 44, width: 100, centerY: 0 },
		        title: 'done',
		        isDefault: YES,
		        location: 'senderClassification',
		        action: 'go',
		        target: Nav.states.main
		      }),

		    cancel: SC.ButtonView.design({
		        controlSize: SC.AUTO_CONTROL_SIZE,
		        layout: { height: 44, width: 100, centerY: 0 },
		        title: 'cancel',
		        location: 'main',
		        action: 'go',
		        target: Nav.states.main
		      })
		  })
		})
	}),
	mainPane: SC.MainPane.design({
		childViews: 'homeButton promptLabel nextButton currentContactView'.w(),
	    
		promptLabel: SC.LabelView.design({
			layout: { centerX: 0, top: 10, width: 200, height: 44 },
			textAlign: SC.ALIGN_CENTER,
			tagName: 'h1', 
			value: 'Sender classificaiton.'
		}),
		
		homeButton: SC.ButtonView.extend({
			layout: { height: 44, left: 12, top: 10, width: 120 },
			title: 'Flows',
	        location: 'flows',
	        action: 'go',
	        target: Nav.states.main
		}),
		nextButton: SC.ButtonView.extend({
			layout: { centerY: 0, right: 12, width: 120, height: 44 },
            controlSize: SC.HUGE_CONTROL_SIZE,
            theme: 'point-right',
			title: 'Next Sender',
			action: 'nextSender',
			target: Nav.states.senderClassification
		}),		
		currentContactView:  SC.PanelPane.design({
			layout: { width: 600, height: 500, centerX: 0, centerY: 0 },
		    isModal: NO,
			contentView: SC.View.extend({
				childViews: 'sender flows'.w(),
		    	sender: SC.LabelView.design({
					layout: { left: 0, top: 0, width: 300, bottom: 0 },
					valueBinding: 'Nav.senderClassificationController.selection'
				}),
				flows: SC.ScrollView.design({
				      hasHorizontalScroller: NO,
				      layout: { top: 0, bottom: 0, left: 300, right: 0 },
				      backgroundColor: 'white',
				      contentView: SC.ListView.design({
				    	  contentBinding: 'Nav.senderClassificationFlowsController.arrangedObjects',
				    	  contentValueKey: 'name',
				    	  contentCheckboxKey: 'included'
				      })
				})
			})
		})
	})
});
