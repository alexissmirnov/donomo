/*globals Nav */

/** @namespace

  Application singletones (like the 'store') go here
  
  @extends SC.Object
*/
Nav = SC.Application.create(
  /** @scope Nav.prototype */ {

	NAMESPACE: 'Nav',
	VERSION: '0.1.0'
	// turn on logging for action notifications
//	trace : YES,
});

App = Nav;

//SC.LOG_OBSERVERS = YES;
//SC.LOG_BINDINGS = YES;