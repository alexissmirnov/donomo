
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
	primaryKey:			'email',
	email:				SC.Record.attr(String),
	contact:			SC.Record.toOne('App.model.Contact', {inverse: 'addresses'})
});

App.model.Contact = SC.Record.extend({
	addresses:			SC.Record.toMany('App.model.Address', {inverse: 'contact'}),
	name:				SC.Record.attr(String),
	flows: 				SC.Record.toMany('App.model.Flow', {inverse: 'contacts', isMater: YES}),
	sentMessages:		SC.Record.toMany('App.model.Message', {inverse: 'from'}),
	receivedMessages:	SC.Record.toMany('App.model.Message', {inverse: 'to'}),
	copiedMessages:		SC.Record.toMany('App.model.Message', {inverse: 'cc'}),
	
	// computed property
	isClassified: function () { 
		return this.flows.get('length') ? YES : NO; 
	}.property('flows').cacheable()
});


/** @class

Describes the flow - a high-level classification of the message stream
and contacts

@extends SC.Record
@version 0.1
*/
App.model.Flow = SC.Record.extend(
/** @scope App.Flow.prototype */ {
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
App.model.Message = SC.Record.extend(
/** @scope App.Flow.prototype */ {
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
App.model.Conversation = SC.Record.extend(
/** @scope App.Flow.prototype */ {
	messages:			SC.Record.toMany('App.model.Message', {inverse: 'conversation', isMaster: YES}),
	subject:			SC.Record.attr(String),
	flows:				SC.Record.toMany('App.model.Flow', {inverse: 'conversations', isMaster: NO}),
	key_participant:	SC.Record.toOne('App.model.Address'),
	summary:			SC.Record.attr(String),
	date:				SC.Record.attr(String)
});



/** @class

Defines an attachment/document

@extends SC.Record
@version 0.1
*/
App.model.Document = SC.Record.extend(
/** @scope App.Flow.prototype */ {
	message:		SC.Record.toOne('App.model.Message', {inverse: 'attachments'}),
	flow:			SC.Record.toOne('App.model.Flow', {inverse: 'documents'}),
	name:			SC.Record.attr(String)
});

App.model.Contact.FIXTURES = [
	{
    'guid': 'contact-1',
    'name': 'Alexis',
    'email': 'alexis@smirnov.ca',
    'sentMessages': ['msgID-1', 'msgID-2'],
    'receivedMessages': ['msgID-3', 'msgID-4'],
    'copiedMessages': ['msgID-5']
	},
	{
    'guid': 'contact-2',
    'name': 'Roger',
    'email': 'roger@inzen.me',
    'sentMessages': ['msgID-3', 'msgID-6', 'msgID-7'],
    'receivedMessages': ['msgID-1', 'msgID-2'],
    'flows': ['flowID-dining']
	},
	{
    'guid': 'contact-3',
    'name': 'Adam',
    'email': 'adam@inzen.me',
    'sentMessages': ['msgID-4']
	},
	{
    'guid': 'contact-4',
    'name': 'Nick',
    'email': 'nick@kushmeric.com',
    'sentMessages': ['msgID-5']
	},
	{
    'guid': 'contact-5',
    'name': 'Support at Tripit',
    'email': 'support@tripit.com',
    'sentMessages': ['msgID-8']
	},
	{
    'guid': 'contact-6',
    'name': 'Kimpton Hotels and Restaurants',
    'email': 'reservations@kimptongroup.ip08.com',
    'sentMessages': ['msgID-9']
	},
	{
    'guid': 'contact-7',
    'name': 'The Posterous Newsletter',
    'email': 'no-reply@posterous.com',
    'sentMessages': ['msgID-11']
	},
	{
    'guid': 'contact-8',
    'name': 'Noam Wasserman',
    'email': 'info@compstudy.com',
    'sentMessages': ['fixtures/messages/ca6d02c22c16148ed611bfd31632e4a0@na04.mypinpointe.com.html']
	}
	
	
];

App.model.Message.FIXTURES = [
	{
    'guid': 'msgID-1', 
    'subject': 'Hello from Alexis',
    'body': 'Hey there, Roger!',
    'to': ['contact-2'],
    'from': ['contact-1'],
    'date': 'Last night'
	},
	{
    'guid': 'msgID-2',
    'subject': 'Hello again from Alexis',
    'body': 'Roger, up for lunch?',
    'to': ['contact-2'],
    'from': ['contact-1'],
    'date': 'Monday'
	},
	{
    'guid': 'msgID-3',
    'subject': 'Lunch?',
    'body': 'Alexis, I\'m hungry',
    'to': ['contact-1'],
    'from': ['contact-2'],
    'date': 'Tuesday'
	},
	{
    'guid': 'msgID-4',
    'subject': 'From Adam to Alexis',
    'body': 'Nice weather on Malta!',
    'to': ['contact-1'],
    'from': ['contact-3'],
    'date': '2 months ago'
	},
	{
    'guid': 'msgID-5',
    'subject': 'More ideas for Roger',
    'body': 'Roger, I\'m CCing Alexis on this',
    'to': ['contact-2'],
    'cc': ['contact-1'],
    'from': ['contact-4']
	},
	{
    'guid': 'msgID-6',
    'subject': 'Lunch?',
    'body': "Hi Alexis, You let us know when you're available, and we'll do our best to fit to your schedule.  AFAIK, I'm not super constrained this weekend (Abby will let me know, haha) and Alexis is available.  From your description is sound like your evenings are taken, but maybe you have a Sunday morning free, for example. Cheers, Roger", //$NON-NLS-1$
    'to': ['contact-1'],
    'cc': ['contact-1'],
    'from': ['contact-2'],
    'date': 'Last night'
	},
	{
    'guid': 'msgID-7',
    'subject': 'Good Lunch',
    'body': 'I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon.I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 3 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 4 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 5 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon.I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 3 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 4 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 5 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon.I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 3 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 4 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 5 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon.I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 3 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 4 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 5 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon.I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 3 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 4 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon 5 I really enjoyed our lunch; it was great chatting with you. I am sure we will bump into each other again soon',
    'to': ['contact-1'],
    'from': ['contact-2'],
    'date': 'Monday'
	},
	{
    'guid': 'msgID-7.1',
    'subject': 'RE: Good Lunch',
    'body': "A cohesive guide or book is definitely something that would be beneficial for newcomers. In case it's useful, my own path to learning SproutCore (still ongoing) has gone something like this: - Heard about it somewhere, checked out the demos at http://demo.sproutcore.com and was blown away - Went through the Todos tutorial (http://wiki.sproutcore.com/Todos%C2%A0Intro) - Wrote a trivial application using the wiki (http://wiki.sproutcore.com) and API docs (http://docs.sproutcore.com) as a reference, A cohesive guide or book is definitely something that would be beneficial for newcomers. In case it's useful, my own path to learning SproutCore (still ongoing) has gone something like this: - Heard about it somewhere, checked out the demos at http://demo.sproutcore.com and was blown away - Went through the Todos tutorial (http://wiki.sproutcore.com/Todos%C2%A0Intro) - Wrote a trivial application using the wiki (http://wiki.sproutcore.com) and API docs (http://docs.sproutcore.com) as a referenceA cohesive guide or book is definitely something that would be beneficial for newcomers. In case it's useful, my own path to learning SproutCore (still ongoing) has gone something like this: - Heard about it somewhere, checked out the demos at http://demo.sproutcore.com and was blown away - Went through the Todos tutorial (http://wiki.sproutcore.com/Todos%C2%A0Intro) - Wrote a trivial application using the wiki (http://wiki.sproutcore.com) and API docs (http://docs.sproutcore.com) as a referenceA cohesive guide or book is definitely something that would be beneficial for newcomers. In case it's useful, my own path to learning SproutCore (still ongoing) has gone something like this: - Heard about it somewhere, checked out the demos at http://demo.sproutcore.com and was blown away - Went through the Todos tutorial (http://wiki.sproutcore.com/Todos%C2%A0Intro) - Wrote a trivial application using the wiki (http://wiki.sproutcore.com) and API docs (http://docs.sproutcore.com) as a referenceA cohesive guide or book is definitely something that would be beneficial for newcomers. In case it's useful, my own path to learning SproutCore (still ongoing) has gone something like this: - Heard about it somewhere, checked out the demos at http://demo.sproutcore.com and was blown away - Went through the Todos tutorial (http://wiki.sproutcore.com/Todos%C2%A0Intro) - Wrote a trivial application using the wiki (http://wiki.sproutcore.com) and API docs (http://docs.sproutcore.com) as a referenceA cohesive guide or book is definitely something that would be beneficial for newcomers. In case it's useful, my own path to learning SproutCore (still ongoing) has gone something like this: - Heard about it somewhere, checked out the demos at http://demo.sproutcore.com and was blown away - Went through the Todos tutorial (http://wiki.sproutcore.com/Todos%C2%A0Intro) - Wrote a trivial application using the wiki (http://wiki.sproutcore.com) and API docs (http://docs.sproutcore.com) as a reference", //$NON-NLS-1$
    'to': ['contact-2'],
    'from': ['contact-1'],
    'date': 'Last night'
	},
	{
    'guid': 'msgID-8',
    'subject': 'TripIt Network Updates - Jul 21 to Jul 28',
    'body': 'Your TripIt network activity: 1 person has travel plans.Add yours.	Top destinations Atlanta, GA',
    'to': ['contact-1'],
    'from': ['contact-5'],
    'date': 'This morning'
	},	
	{
    'guid': 'msgID-9',
    'subject': 'Kimpton InTouch Exclusive: Summer Weekends from $109',
    'body': 'To view this message in your web browser, please follow this link.You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch.',
    'to': ['contact-1'],
    'from': ['contact-6'],
    'date': 'Moments ago'             
	},	
	{
    'guid': 'msgID-10',
    'subject': 'Kimpton InTouch Exclusive: Summer Weekends from $109',
    'body': 'Kimpton InTouch Exclusive: Summer Weekends from $109 You have received Kimpton InTouch Exclusive: Summer Weekends from $109 You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch. You have received this message as you are a valued member of Kimpton InTouch.',
    'to': ['contact-1'],
    'from': ['contact-6'],
    'date': 'Today'
	},	
	{
    'guid': 'msgID-11',
    'subject': 'The Path Ahead After a Tough Week',
    'body': "Hi <b>Alexis</b>. As you're no doubt aware, Posterous has had a rocky six days. On Wednesday and Friday, our servers were hit by massive Denial of Service (DoS) attacks. We responded quickly and got back online within an hour, but it didn’t matter; the site went down and our users couldn’t post.", //$NON-NLS-1$
    'to': ['contact-1'],
    'from': ['contact-7'],
    'date': 'Today'
	},
	{
	'guid': 'ca6d02c22c16148ed611bfd31632e4a0@na04.mypinpointe.com.html',
	'subject': 'Increase transparency in private company compensation',
	'body' : "<bo><div style='color: #000000; font-family: Verdana, Arial, Helvetica,sans-serif; font-size: 10px; background-image: initial;background-attachment: initial; background-origin: initial;background-clip: initial; background-color: #ffffff; margin: 8px;'><p><span style='font-family: Arial;'><font size='2'>Greetings!<br /><br/>I recently published an op-ed piece at Xconomy on the impetus behind mysupport of the CompStudy entitled <ahref='http://na04.mypinpointe.com/link.php?M=234709&N=469&L=214&F=H'>'HelpIncrease Transparency in Private Company ExecutiveCompensation.'</a></font></span></p><p><span style='font-family: Arial;'><font size='2'>If you haven`t already, I`d like to invite you to take our 2010 privatecompany&nbsp;</font><font size='2'><strong>CompStudy</strong></font><fontsize='2'>&nbsp;survey, the results of which become our industry-leadingCompensation and Entrepreneurship Report. To accommodate lateinvitees,&nbsp;</font><strong><font size='2'>we have extended theparticipation deadline to August 27th</font></strong><font size='2'>.<br/><br />For a guided video tour of the reporting platform, please visitthis page:&nbsp;</font><a target='_blank'href='http://na04.mypinpointe.com/link.php?M=234709&N=469&L=103&F=H'><fontsize='2'>https://compstudy.com/content/overview<br /></font></a><fontsize='2'><br />To take the survey, please visit </font><ahref='http://na04.mypinpointe.com/link.php?M=234709&N=469&L=114&F=H'><fontsize='2'>https://compstudy.com</font></a></span></p><p><span style='font-family: Arial;'><font size='2'>This comprehensive andinnovative survey of equity and salary compensation for private companiesis produced as a collaborative effort between Harvard Business School andprofessionals at J. Robert Scott and Ernst &amp; Young,llp.</font></span></p><p><span style='font-family: Arial;'><font size='2'>Thank you in advancefor your time and participation!<br />&nbsp;</font></span></p><p><span style='font-family: Arial;'><font size='2'>Professor NoamWasserman<br />Harvard Business School<br /><imgsrc='http://na04.mypinpointe.com/admin/temp/newsletters/152/compstudy-logo.jpg'width='100' height='22' alt='compstudy-logo.jpg' title='compstudy-logo.jpg'/>&nbsp;</font></span></p><p><font size='2'><br /></font></p><p><span style='font-family: Arial;'><span style='font-style:italic;'><font size='2'>For more information on how the data provided isused, please visit us online at&nbsp;</font><ahref='http://na04.mypinpointe.com/link.php?M=234709&N=469&L=104&F=H'><fontsize='2'>http://www.compstudy.com</font></a><font size='2'>, where you canview previous editions of our report and more work from HBS AssociateProfessor Noam Wasserman.</font></span><font size='2'><br/></font></span></p><p><font size='2'><br /></font></p><p align='center'><span style='font-family: Arial;'><ahref='http://na04.mypinpointe.com/unsubscribe.php?M=234709&C=e457c453cd15fe58631de9767af54192&L=175&N=469'><fontsize='2'>Unsubscribe me from this list</font></a><fontsize='2'>&nbsp;|&nbsp;</font><font size='2'>www.compstudy.com</font><fontsize='2'>&nbsp;| 260 Franklin St. Ste 620 | Boston, MA02110</font></span></p></div></bo><imgsrc='http://na04.mypinpointe.com/open.php?M=234709&L=175&N=469&F=H&image=.jpg'height='1' width='10'>", //$NON-NLS-1$
	'to': ['contact-1'],
	'from' : ['contact-8'],
	'date': 'Thu, 12 Aug 2010 08:20:14 -0700'
	}
];


App.model.Flow.FIXTURES = [
	{
    'guid': 'flowID-work',
    'name': 'Work',
    'contacts': ['contact-4'],
    'type': 'conversation',
    'conversations': ['conv-5', 'conv-7']
	},
	{
    'guid': 'flowID-dining',
    'name': 'Dining',
    'contacts': ['contact-2'],
    'type': 'conversation',
    'conversations': ['conv-1', 'conv-2', 'conv-3', 'conv-4']
	},
	{
    'guid': 'flowID-travel',
    'name': 'Travel',
    'contacts': ['contact-5', 'contact-6'],
    'type': 'newsletter',
    'conversations': ['conv-6']
	}
];

App.model.Conversation.FIXTURES = [
    {
    	'guid': 'conv-1',
    	'subject': 'Good Lunch',
    	'messages': ['msgID-7', 'msgID-7.1'],
    	'flows' : ['flowID-dining']
	},
    {
    	'guid': 'conv-2',
    	'subject': 'Lunch Plans',
    	'messages': ['msgID-2', 'msgID-3'],
    	'flows' : ['flowID-dining']
	},
    {
    	'guid': 'conv-3',
    	'subject': 'Good Lunch',
    	'messages': ['msgID-1'],
    	'flows' : ['flowID-dining']
	},
    {
    	'guid': 'conv-4',
    	'subject': 'Good Lunch',
    	'messages': ['msgID-1'],
    	'flows' : ['flowID-dining']
	},
    {
    	'guid': 'conv-5',
    	'subject': 'The Path Ahead After a Tough Week',
    	'messages': ['msgID-11'],
    	'flows' : ['flowID-work']
	},
    {
    	'guid': 'conv-6',
    	'subject': 'Kimpton InTouch Exclusive: Summer Weekends from $109',
    	'messages': ['msgID-9', 'msgID-10'],
    	'flows' : ['flowID-travel']
	},
    {
    	'guid': 'conv-7',
    	'subject': 'compstudy',
    	'messages': ['ca6d02c22c16148ed611bfd31632e4a0@na04.mypinpointe.com.html'],
    	'flows' : ['flowID-work']
	}
    ];
                           

