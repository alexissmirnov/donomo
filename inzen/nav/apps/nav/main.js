// ==========================================================================
// Project:   Nav
// ==========================================================================
/*globals Nav */

// This is the function that will start your app running.  
require('responders/main');


Nav.main = function main() {
	// make the root state the initial controller
	Nav.makeFirstResponder(Nav.states.main);
	
	// register Nav.states.root.route() as the route handler
	SC.routes.add(':stateLocation', Nav.states.main, 'route');
};

function main() 
{
	Nav.main(); 
}
