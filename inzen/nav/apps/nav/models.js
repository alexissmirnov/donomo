
SC.Query.registerQueryExtension('AS_GUID_IN', {
	reservedWord:     true,
	leftType:         'PRIMITIVE',
      rightType:        'PRIMITIVE',
      evalType:         'BOOLEAN',

      evaluate:         function (r,w) {
                          	var prop   = this.leftSide.evaluate(r,w);
                          	var values = this.rightSide.evaluate(r,w);
                          	var found  = false;
                          	var i      = 0;
                          	while ( found===false && i<values.get('length') ) {
                            if ( prop == values.objectAt(i).get('guid') ) found = true;
                            i++;
                          }
                          return found;
                        }
    });

SC.Query.registerQueryExtension('OF_LENGTH', {
    reservedWord:     true,
    leftType:         'PRIMITIVE',
    rightType:        'PRIMITIVE',
    evalType:         'BOOLEAN',

    evaluate:         function (r,w) {
                    	var arr   = this.leftSide.evaluate(r,w);
                    	var len = this.rightSide.evaluate(r,w);
                    	return arr.get('length') == len;
                      }
  });



/**
 * App.model represents a syntaxic sugar to tell model objects apart from views
 * etc. We still have only one namespace App
 * TODO: http://markmail.org/message/sdyvzighmr47z355
 */
App.model = App;

/** @class

  Represents a contact (email address and possibly a name). Contacts
  may be classified to belong to a flow.

  @extends SC.Record
  @version 0.1
*/


App.model.SyncTracker = SC.Record.extend({
	date: SC.Record.attr(String)
});

App.model.Account = SC.Record.extend( {
	accountClass : SC.Record.attr(String, {defaultValue: 'email/gmail'}),
	password : SC.Record.attr(String),
	name : SC.Record.attr(String)
});

App.model.User = SC.Record.extend( {
	username : SC.Record.attr(String)
});

App.model.Address = SC.Record.extend({
	email:				SC.Record.attr(String),
	contact:			SC.Record.toOne('App.model.Contact', {inverse: 'addresses'})
});

App.model.Contact = SC.Record.extend({
	addresses:			SC.Record.toMany('App.model.Address', {inverse: 'contact'}),
	name:				SC.Record.attr(String),
	type:				SC.Record.attr(String),
	flows: 				SC.Record.toMany('App.model.Flow', {inverse: 'contacts', isMater: YES}),
	sentMessages:		SC.Record.toMany('App.model.Message', {inverse: 'from'}),
	receivedMessages:	SC.Record.toMany('App.model.Message', {inverse: 'to'}),
	copiedMessages:		SC.Record.toMany('App.model.Message', {inverse: 'cc'}),
	
	// computed property
	isClassified: function () { 
		return this.flows.get('length') ? YES : NO; 
	}.property('flows').cacheable()
});
App.model.Contact.PERSON = '2';
App.model.Contact.BUSINESS = '1';


/** @class

Describes the flow - a high-level classification of the message stream
and contacts

@extends SC.Record
@version 0.1
*/
App.model.Flow = SC.Record.extend({
	date:			SC.Record.attr(String),
	name:			SC.Record.attr(String),
	tag_class:		SC.Record.attr(String),
	contacts:		SC.Record.toMany('App.model.Contact', {inverse: 'flows'}),
	conversations:	SC.Record.toMany('App.model.Conversation', {inverse: 'flows', isMaster: YES}),
	documents:		SC.Record.toMany('App.model.Document', {inverse: 'flow'})
});

/** @class

Defines an email message with its attributes. A message belongs to one conversation

@extends SC.Record
@version 0.1
*/
App.model.Message = SC.Record.extend({
	conversation:	SC.Record.toOne('App.model.Conversation', {inverse: 'messages', isMaster: NO}),
	date:			SC.Record.attr(String), // sent or received
	subject:		SC.Record.attr(String),
	body:			SC.Record.attr(String),
	sender_address:	SC.Record.toOne('App.model.Address', {inverse: 'sentMessages'}),
	to:				SC.Record.toMany('App.model.Contact', {inverse: 'receivedMessages'}),
	cc:				SC.Record.toMany('App.model.Contact', {inverse: 'copiedMessages'}),
	attachments:	SC.Record.toMany('App.model.Document', {inverse: 'message'})
});

/** @class

Defines a conversation. A named group of messages that may belong to one flow.

@extends SC.Record
@version 0.1
*/
App.model.Conversation = SC.Record.extend({
	messages:			SC.Record.toMany('App.model.Message', {inverse: 'conversation', isMaster: YES}),
	subject:			SC.Record.attr(String),
	tags:				SC.Record.toMany('App.model.Flow', {inverse: 'conversations', isMaster: NO}),
	key_participant:	SC.Record.toOne('App.model.Address'),
	summary:			SC.Record.attr(String),
	date:				SC.Record.attr(SC.DateTime, {format: '%a %b %d %H:%M:%S %Y'}),
	humanized_age:		SC.Record.attr(String)
});



/** @class

Defines an attachment/document

@extends SC.Record
@version 0.1
*/
App.model.Document = SC.Record.extend({
	message:		SC.Record.toOne('App.model.Message', {inverse: 'attachments'}),
	flow:			SC.Record.toOne('App.model.Flow', {inverse: 'documents'}),
	name:			SC.Record.attr(String)
});

App.model.SchemaVersion = SC.Record.extend({
	version:		SC.Record.attr(String)
});


