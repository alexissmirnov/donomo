// This is the function that will start your app running.  
sc_require('responders/start');
require('core');


function main() 
{
	App.state.transitionTo(App.state.START);
}

