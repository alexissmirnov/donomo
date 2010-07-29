// ==========================================================================
// Project:   Nav
// ==========================================================================
/*globals Nav */

SC.Query.registerQueryExtension("AS_GUID_IN", {
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
                            if ( prop == values.objectAt(i).get("guid") ) found = true;
                            i++;
                          }
                          return found;
                        }
    });

SC.Query.registerQueryExtension("OF_LENGTH", {
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


/** @class

  Represents a contact (email address and possibly a name). Contacts
  may be classified to belong to a flow.

  @extends SC.Record
  @version 0.1
*/


Nav.model = {};

Nav.model.Contact = SC.Record.extend(
/** @scope Nav.Contact.prototype */ {
	email:		SC.Record.attr(String),
	name:		SC.Record.attr(String),
	flows: 		SC.Record.toMany('Nav.model.Flow', {inverse: 'contacts', isMater: YES}),
	sentMessages:		SC.Record.toMany('Nav.model.Message', {inverse: 'from'}),
	receivedMessages:	SC.Record.toMany('Nav.model.Message', {inverse: 'to'}),
	copiedMessages:		SC.Record.toMany('Nav.model.Message', {inverse: 'cc'}),
	
	// computed property
	isClassified: function () { 
		return this.flows.get('length') ? YES : NO; 
	}.property('flows').cacheable()
});


/** @class

Describes the user created during signup.
For now the user owns the one email account.

@extends SC.Record
@version 0.1
*/
Nav.model.User = SC.Record.extend(
/** @scope Nav.User.prototype */ {
	name:	   SC.Record.attr(String),
	email:     SC.Record.attr(String),
	password:  SC.Record.attr(String),
	description: SC.Record.attr(String)
});

/** @class

Describes the flow - a high-level classification of the message stream
and contacts

@extends SC.Record
@version 0.1
*/
Nav.model.Flow = SC.Record.extend(
/** @scope Nav.Flow.prototype */ {
	name:			SC.Record.attr(String),
	contacts:		SC.Record.toMany('Nav.model.Contact', {inverse: 'flows'}),
	conversations:	SC.Record.toMany('Nav.model.Conversation', {inverse: 'flows'}),
	documents:		SC.Record.toMany('Nav.model.Document', {inverse: 'flow'})
});

/** @class

Defines an email message with its attributes. A message belongs to one conversation

@extends SC.Record
@version 0.1
*/
Nav.model.Message = SC.Record.extend(
/** @scope Nav.Flow.prototype */ {
	conversation:	SC.Record.toOne('Nav.model.Conversation', {inverse: 'messages', isMaster: NO}),
	date:			SC.Record.attr(String), // sent or received
	subject:		SC.Record.attr(String),
	body:			SC.Record.attr(String),
	from:			SC.Record.toOne('Nav.model.Contact', {inverse: 'sentMessages'}),
	to:				SC.Record.toMany('Nav.model.Contact', {inverse: 'receivedMessages'}),
	cc:				SC.Record.toMany('Nav.model.Contact', {inverse: 'copiedMessages'}),
	attachments:	SC.Record.toMany('Nav.model.Document', {inverse: 'message'})
});

/** @class

Defines a conversation. A named group of messages that may belong to one flow.

@extends SC.Record
@version 0.1
*/
Nav.model.Conversation = SC.Record.extend(
/** @scope Nav.Flow.prototype */ {
	messages:		SC.Record.toMany('Nav.model.Message', {inverse: 'conversation', isMaster: YES}),
	name:			SC.Record.attr(String)
});



/** @class

Defines a conversation. A named group of messages that may belong to one flow.

@extends SC.Record
@version 0.1
*/
Nav.model.Document = SC.Record.extend(
/** @scope Nav.Flow.prototype */ {
	message:		SC.Record.toOne('Nav.model.Message', {inverse: 'attachments'}),
	flow:			SC.Record.toOne('Nav.model.Flow', {inverse: 'documents'}),
	name:			SC.Record.attr(String)
});


Nav.model.Contact.FIXTURES = [
	{
    "guid": "contact-1",
    "name": "Alexis",
    "email": "alexis@smirnov.ca",
    'sentMessages': ['msgID-1', 'msgID-2'],
    'receivedMessages': ['msgID-3', 'msgID-4'],
    'copiedMessages': ['msgID-5']
	},
	{
    "guid": "contact-2",
    "name": "Roger",
    "email": "roger@inzen.me",
    'sentMessages': ['msgID-3', 'msgID-6', 'msgID-7'],
    'receivedMessages': ['msgID-1', 'msgID-2'],
    'flows': ['flowID-dining']
	},
	{
    "guid": "contact-3",
    "name": "Adam",
    "email": "adam@inzen.me",
    'sentMessages': ['msgID-4']
	},
	{
    "guid": "contact-4",
    "name": "Nick",
    "email": "nick@kushmeric.com",
    'sentMessages': ['msgID-5']
	},
	{
    "guid": "contact-5",
    "name": "Support at Tripit",
    "email": "support@tripit.com",
    'sentMessages': ['msgID-8']
	},
	{
    "guid": "contact-6",
    "name": "Kimpton Hotels and Restaurants",
    "email": "reservations@kimptongroup.ip08.com",
    'sentMessages': ['msgID-9']
	}
];

Nav.model.Message.FIXTURES = [
	{
    "guid": "msgID-1",
    "subject": "Hello from Alexis",
    "body": "Hey there, Roger!",
    "to": ['contact-2'],
    'from': ['contact-1']
	},
	{
    "guid": "msgID-2",
    "subject": "Hello again from Alexis",
    "body": "Roger, up for lunch?",
    "to": ['contact-2'],
    'from': ['contact-1']
	},
	{
    "guid": "msgID-3",
    "subject": "Lunch?",
    "body": "Alexis, I'm hungry",
    "to": ['contact-1'],
    'from': ['contact-2']
	},
	{
    "guid": "msgID-4",
    "subject": "From Adam to Alexis",
    "body": "Nice weather on Malta!",
    "to": ['contact-1'],
    'from': ['contact-3']
	},
	{
    "guid": "msgID-5",
    "subject": "More ideas for Roger",
    "body": "Roger, I'm CCing Alexis on this",
    "to": ['contact-2'],
    'cc': ['contact-1'],
    'from': ['contact-4']
	},
	{
    "guid": "msgID-6",
    "subject": "Lunch?",
    "body": "Hi Alexis, You let us know when you're available, and we'll do our best to fit to your schedule.  AFAIK, I'm not super constrained this weekend (Abby will let me know, haha) and Alexis is available.  From your description is sound like your evenings are taken, but maybe you have a Sunday morning free, for example. Cheers, Roger",
    "to": ['contact-1'],
    'cc': ['contact-1'],
    'from': ['contact-2']
	},
	{
    "guid": "msgID-7",
    "subject": "Good Lunch",
    "body": "I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon.",
    "to": ['contact-1'],
    'from': ['contact-2']
	},
	{
    "guid": "msgID-8",
    "subject": "TripIt Network Updates - Jul 21 to Jul 28",
    "body": "Your TripIt network activity: 1 person has travel plans.Add yours.	Top destinations Atlanta, GA",
    "to": ['contact-1'],
    'from': ['contact-5']
	},	
	{
    "guid": "msgID-9",
    "subject": "Kimpton InTouch Exclusive: Summer Weekends from $109",
    "body": "To view this message in your web browser, please follow this link.You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch.",
    "to": ['contact-1'],
    'from': ['contact-6']
	},	
];

Nav.model.Flow.FIXTURES = [
	{
    "guid": "flowID-work",
    "name": "Work",
    'contacts': ['contact-4']
	},
	{
    "guid": "flowID-dining",
    "name": "Dining",
    'contacts': ['contact-2']
	},
	{
    "guid": "flowID-travel",
    "name": "Travel",
    'contacts': ['contact-5', 'contact-6']
	}
];
                           

