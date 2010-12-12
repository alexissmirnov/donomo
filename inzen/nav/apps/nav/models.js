
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


App.ObjectsController = SC.ArrayController.extend({
	/**
	 * Pseudo-synchronous API to handle all objects of a given type.
	 * 
	 * This API in intended to hide the asynchronous nature of retrieving
	 * records by providing a callback to be called when the data in available.
	 * 
	 * Example usage:
	 * App.MyModel.objects().all(function(obj) {console.log(obj);));
	 */
	all: function(onSuccess, onError) {
		var records = this.get('content'),
			_statusDidChange = function() {
				if( this.status & SC.Record.READY_CLEAN && onSuccess) {
					// Now that the records are in READ_CLEAN state, call
					// the callback
					onSuccess(this);
					
					// Now that we've handled the event, we no longer need
					// to be listening for the status
					records.removeObserver('status', statusDidChange);
				}
			};
		
		// No records yet, launch the find() request for all objects of the
		// parentType
		if( !records ) {
			var parentType = this.get('parent');
			var store = this.get('store');
			
			records = store.find(SC.Query.local(parentType));
			this.set('content', records);
		}
		
		// If the records aren't ready yet, defer calling onSuccess
		if( onSuccess ) {
			if( records.status & SC.Record.READY_CLEAN )
				onSuccess(records);
			else
				records.addObserver('status', _statusDidChange);
		}
		return this;
	},
	
	/**
	 * Delete all objects contained objects
	 */
	del: function() {
		var records = this.get('content'),
			_del = function(records) {
				records.forEach(function(record) {
					record.store.destroyRecord(undefined, 
											undefined, 
											record.storeKey);
				});
				// In principle, this would be a good time to
				// destroy the records array because we just deleted its contents
				// However, the array could also be also supplying data to some other controller
				// in which case destroying the array will cause those controllers to stop
				// refreshing its listeners (eg. the views)
				// records.destroy();
			};
		
		if( records.status & SC.Record.READY_CLEAN ) {
			_del(records);
		} else {
			var _statusDidChange = function() {
				if( records.status & SC.Record.READY_CLEAN ) {
					console.log('deleting %@'.fmt(this));
					_del(this);
					this.removeObserver('status', statusDidChange);
				}
			};
			records.addObserver('status', _statusDidChange);
		}
	},
	
	runGet: function(queryConditions, onSuccess, onError) {
		var parentType = this.get('parent'),
		store = this.get('store'),
		queryString = '',
		andString = '',
		query = null,
		records = null,
		_statusDidChange = function() {
			console.log('status change: %@'.fmt(records.status));
			
			if( records.status & SC.Record.READY_CLEAN ) {
				if( records.length() === 1 && onSuccess ) { 
					onSuccess(records.objectAt(0));
				}
				if( records.length() != 1 && onError ){
					onError();
				}
				
				// Now that the READY state is handled, the observer is
				// no longer needed. So remove it.
				records.removeObserver('status', _statusDidChange);
				records.destroy();
			}
		};

		for( condition in queryConditions ) {
			if (queryConditions.hasOwnProperty(condition)) {
				queryString = '%@ %@ %@="%@"'.fmt(queryString, andString, condition, queryConditions[condition]);
				andString = "and";
			}
		}

		query = SC.Query.local(parentType, queryString);
		records = store.find(query);

		if( records.status & SC.Record.READY_CLEAN ) {
			_statusDidChange();
		} else {
			records.addObserver('status', _statusDidChange);
		}
	},
	/**
	 * Usage example:
	 * 
	 * MyApp.MyModel.objects().getOrCreate(
	 * 				'guid = 1', 
	 * 				{quid: 1, foo, 'bar'}, 
	 * 				function(result, created) {
	 * 					console.log('got %@ created? %@'.fmt(result, created);
	 * 				});
	 */
	getOrCreate: function(queryConditions, defaults, onSuccess, onError) {
		var parentType = this.get('parent'),
			store = this.get('store'),
			queryString = '',
			andString = '',
			query = null,
			records = null,
			_createRecord = function() {
				// If the conditions or defaults include the primary key,
				// it will be extracted from the defaults and be used as the ID
				// for the record.
				var record = store.createRecord(parentType, defaults);
				onSuccess(record, YES);
			},
			_statusDidChange = function() {
				if( records.status & SC.Record.READY_CLEAN ) {
					console.log('callback received records ready');
					if( records.length() > 1) {
						var handler = onError || console.log;
						handler('getOrCreate returned %@ records'.fmt(records.length()));
					}
					if( records.length() === 0) {
						_createRecord();
					}
					if( records.length() === 1 && onSuccess ) { 
						onSuccess(records.objectAt(0), NO);
					}
					// Now that the READY state is handled, the observer is
					// no longer needed. So remove it.
					records.removeObserver('status', _statusDidChange);
					records.destroy();
				}
			};

		for( condition in queryConditions ) {
			if (queryConditions.hasOwnProperty(condition)) {
				queryString = '%@ %@ %@="%@"'.fmt(queryString, andString, condition, queryConditions[condition]);
				andString = "and";
				defaults['%@'.fmt(condition)] = queryConditions[condition];
			}
		}			
		query = SC.Query.local(parentType, queryString);
		records = store.find(query);
		
		if( records.status & SC.Record.READY_CLEAN ) {
			_statusDidChange();
		} else {
			records.addObserver('status', _statusDidChange);
		}
	}
});
/*---------------------------------------------------------------------------*/

App.Record = SC.Record.extend({});
App.Record.mixin({
	_objects: null,
	objects: function() {
		if( !this._objects ) {
			this._objects = App.ObjectsController.create({parent: this, store: App.store});
		}
		return this._objects;
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
App.model.SyncTracker = App.Record.extend({
	ID: 'SyncTracker.1',
	
	date: SC.Record.attr(String),
	
	getOrCreate: function(guid, defaults, onSuccess, onFailure) {
		// check if the object is already in in-memory store
		var storeKey = this.storeKeysById()[guid],
			onFound = function(store, storeKey, id, record) {
				onSuccess(record);
			},
			onNotFound = function(store, storeKey, id) {
				
			};
		if( !storeKey ) {
			// launch the get query
			storeKey = recordType.storeKeyFor(guid);
			this.store._getDataSource().retrieveRecordWithCallbacks(this.store, storeKey, id, onFound, onNotFound);
		}
	}
});

App.model.Account = App.Record.extend( {
	accountClass : SC.Record.attr(String, {defaultValue: 'email/gmail'}),
	password : SC.Record.attr(String),
	name : SC.Record.attr(String)
});

App.model.User = App.Record.extend( {
	ID: 'User.1',
	username : SC.Record.attr(String)
});

App.model.Address = App.Record.extend({
	email:				SC.Record.attr(String),
	contact:			SC.Record.toOne('App.model.Contact', {inverse: 'addresses'})
});

App.model.Contact = App.Record.extend({
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
App.model.Contact.BUSINESS = '1';
App.model.Contact.PERSON = '2';


/** @class

Describes the flow - a high-level classification of the message stream
and contacts

@extends SC.Record
@version 0.1
*/
App.model.Flow = App.Record.extend({
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
App.model.Message = App.Record.extend({
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
App.model.Conversation = App.Record.extend({
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
App.model.Document = App.Record.extend({
	message:		SC.Record.toOne('App.model.Message', {inverse: 'attachments'}),
	flow:			SC.Record.toOne('App.model.Flow', {inverse: 'documents'}),
	name:			SC.Record.attr(String)
});

App.model.SchemaVersion = App.Record.extend({
	ID: 'SchemaVersion.1',
	version:		SC.Record.attr(String)
});


