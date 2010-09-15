// ==========================================================================
// Project:   Nav
// ==========================================================================
/*globals Nav */

// This is the function that will start your app running.  
require('responders/main');
require('core');



function main() 
{
	Nav.makeFirstResponder(Nav.states.main);
	
	// register Nav.states.root.route() as the route handler
	SC.routes.add(':stateLocation', Nav.states.main, 'route');
}

