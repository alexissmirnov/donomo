// ==========================================================================
// Project: Signup.User
// Copyright: ©2009 Apple Inc.
// ==========================================================================
/*globals Signup */

/*---------------------------------------------------------------------------*/
Signup.Account = SC.Record.extend( {
	accountClass : SC.Record.attr(String, {defaultValue: 'email/gmail'}),
	password : SC.Record.attr(String),
	name : SC.Record.attr(String)
});

Signup.User = SC.Record.extend( {
	username : SC.Record.attr(String)
});

Signup.Message = SC.Record.extend( {
	body : SC.Record.attr(String)
});

