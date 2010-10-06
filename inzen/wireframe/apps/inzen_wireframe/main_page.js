// ==========================================================================
// Project:   InzenWireframe - mainPage
// Copyright: ©2010 My Company, Inc.
// ==========================================================================
/*globals InzenWireframe */

InzenWireframe.Button = SC.View.extend({
    classNames: 'wf-button'.w(),
    click: function(e) {this.touchEnd();},
    touchStart: function(e) { return YES; },
    touchEnd: function(e) {
        InzenWireframe.mainPage.mainPane.container.set('nowShowing', this.show);
    }
});

// This page describes the main user interface for your application.
InzenWireframe.mainPage = SC.Page.design({
    // The main pane is made visible on screen as soon as your app is loaded.
    // Add childViews to this pane for views to display immediately on page
    // load.
    mainPane: SC.MainPane.design({
        classNames: 'main-pane'.w(),
        childViews: 'container'.w(),

        container: SC.ContainerView.design({
            nowShowing: 'start'
        })
    }),
    
    start: SC.View.design({
        classNames: 'wf-start'.w(),
        childViews: [ InzenWireframe.Button.design({
            layout: {top: 54, left: 0, height: 48, width: 168},
            show: 'newAccount'
        })]
    }),
    
    newAccount: SC.View.design({
        classNames: 'wf-new-account'.w(),
        
        childViews: [InzenWireframe.Button.design({
            layout: {top: 318, left: 318, height: 120, width: 144 },
            show: 'newAccountGmail'
        }),
        InzenWireframe.Button.design({
            layout: {bottom: 0, left: 0, height: 25, width: 25 },
            show: 'start'
        })]
    }),
    
    newAccountGmail: SC.View.design({
        classNames: 'wf-new-account-gmail'.w(),
        childViews: [InzenWireframe.Button.design({
            layout: {top: 350, left: 265, height: 30, width: 70 },
            show: 'flows'
        }),
        InzenWireframe.Button.design({
            layout: {bottom: 0, left: 0, height: 25, width: 25 },
            show: 'start'
        })]
    }),
    
    flows: SC.View.design({
        classNames: 'wf-flows'.w(),
        childViews: [ 
            InzenWireframe.Button.design({
                layout: { top: 608, left: 393, height: 69, width: 286 },
                show: 'vmware'
            }),
            InzenWireframe.Button.design({
                layout: {top: 466, left: 393, height: 136, width: 286 },
                show: 'conversation'
            }),
            InzenWireframe.Button.design({
                layout: {top: 36, left: 393, height: 136, width: 286 },
                show: 'classification'
            }),
            InzenWireframe.Button.design({
                layout: {top: 54, left: 0, height: 49, width: 207 },
                show: 'addAccount'
            }),
            InzenWireframe.Button.design({
                layout: {bottom: 0, left: 0, height: 25, width: 25 },
                show: 'start'
            })
        ]
    }),
    
    expandedFlows: SC.View.design({
        classNames: 'wf-expanded-flows'.w(),
        childViews: [ 
            InzenWireframe.Button.design({
                layout: { top: 598, left: 240, height: 69, width: 286 },
                show: 'vmware'
            }),
            InzenWireframe.Button.design({
                layout: {top: 466, left: 243, height: 126, width: 280 },
                show: 'conversation'
            }),
            InzenWireframe.Button.design({
                layout: {top: 27, left: 243, height: 126, width: 283 },
                show: 'classification'
            }),
            InzenWireframe.Button.design({
                layout: {top: 53, left: 0, height: 45, width: 45 },
                show: 'addAccount'
            }),
            InzenWireframe.Button.design({
                layout: {bottom: 0, left: 0, height: 25, width: 25 },
                show: 'start'
            })
        ]
    }),
    
    economist: SC.View.design({
        classNames: 'wf-economist'.w(),
        childViews: [InzenWireframe.Button.design({
            layout: {top: 0, right: 0, height: 30, width: 30},
            show: 'expandedFlows'
        }),
        InzenWireframe.Button.design({
            layout: {top: 45, left: 188, height: 132, width: 173 },
            show: 'classification'
        }),
        InzenWireframe.Button.design({
            layout: {bottom: 0, left: 0, height: 25, width: 25 },
            show: 'start'
        })]
    }),
    
    conversation: SC.View.design({
        classNames: 'wf-conversation'.w(),
        childViews: [InzenWireframe.Button.design({
            layout: {top: 25, left: 992, height: 25, width: 25},
            show: 'expandedFlows'
        }),
        InzenWireframe.Button.design({
            layout: {top: 45, left: 188, height: 132, width: 173 },
            show: 'classification'
        }),
        InzenWireframe.Button.design({
            layout: {top: 619, left: 191, height: 72, width: 174 },
            show: 'vmware'
        }),
        InzenWireframe.Button.design({
            layout: {bottom: 0, left: 0, height: 25, width: 25 },
            show: 'start'
        })]
    }),
    
    classification: SC.View.design({
        classNames: 'wf-classification'.w(),
        childViews: [InzenWireframe.Button.design({
            layout: {top: 25, left: 992, height: 25, width: 25},
            show: 'expandedFlows'
        }),
        InzenWireframe.Button.design({
            layout: {top: 619, left: 191, height: 72, width: 174 },
            show: 'vmware'
        }),
        InzenWireframe.Button.design({
            layout: {bottom: 0, left: 0, height: 25, width: 25 },
            show: 'start'
        })]
    }),
    
    addAccount: SC.View.design({
        classNames: 'wf-add-account'.w(),
        childViews: [
            InzenWireframe.Button.design({
                layout: {top: 0, left: 757, height: 768, right: 0},
                show: 'expandedFlows'
            }),
            InzenWireframe.Button.design({
                layout: { top: 111, left: 0, height: 46, width: 181 },
                show: 'expandedFlows'
            }),
            InzenWireframe.Button.design({
                layout: {bottom: 0, left: 0, height: 25, width: 25 },
                show: 'start'
            })
        ]
    }),
    vmware: SC.View.design({
        classNames: 'wf-vmware'.w(),
        childViews: [InzenWireframe.Button.design({
            layout: {top: 10, left: 992, height: 25, width: 25},
            show: 'expandedFlows'
        }),
        InzenWireframe.Button.design({
            layout: {top: 269, left: 120, height: 153, width: 139 },
            show: 'zagg'
        }),
        InzenWireframe.Button.design({
            layout: {bottom: 0, left: 0, height: 30, width: 30 },
            show: 'start'
        })]
    }),
    zagg: SC.View.design({
        classNames: 'wf-zagg'.w(),
        childViews: [InzenWireframe.Button.design({
            layout: {top: 10, left: 992, height: 25, width: 25},
            show: 'expandedFlows'
        }),
        InzenWireframe.Button.design({
            layout: {bottom: 0, left: 0, height: 25, width: 25 },
            show: 'start'
        })]
    })
    

});
