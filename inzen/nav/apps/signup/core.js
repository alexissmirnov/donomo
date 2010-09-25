/*globals Signup */

/**
 * @namespace
 * 
 * This example application demonstrates the use of a using a modal dialog with
 * several controls to construct a new Account and User object for submission to
 * a server.
 * 
 * Note also the use of Responders to manage the overall application context.
 * 
 * @extends SC.Object
 */
Signup = SC.Application.create( {

	NAMESPACE : 'Signup',
	VERSION : '1.0.0',

	// turn on logging for action notifications
	trace : YES
});
