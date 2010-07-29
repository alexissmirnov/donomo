// ==========================================================================
// Project:   Nav
// ==========================================================================
/*globals Nav */

// This page describes the main user interface for your application.  
Nav.flowsPage = SC.Page.design({
	mainPane: SC.MainPane.design({
		childViews: 'topbar flows'.w(),
    
	    topbar: SC.View.design({
	        layout: { height: 45, left:0, top:0, right:0 },
	        childViews: 'logo settings'.w(),
	        
	        logo: SC.View.design({
	          layout: {top:10,left:15,height:24,width:72}
	        }),
	        
	        settings: SC.ButtonView.design({
	            layout: {top:7,right:20,height:31,width:47},
	            title: 'settings',
	            action: 'go',
	            target: Nav.states.main,
	            location: 'settings'
	          })
	    }),
	    
	    flows: Nav.DashboardScrollView.design({
	    	layout: {top:45,right:0,bottom:0,left:0}
	    })
	})
});
