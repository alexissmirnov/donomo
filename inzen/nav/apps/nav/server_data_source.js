/**
 * Data Soruce connected to inzen API
 */
sc_require('models');


App.query = {};
App.query.GET_CONVERSATIONS = SC.Query.local(App.model.Conversation);
/**
 * A note about sort order.
 * Sorting by tag_class so that INBOX ("Unsorted") always comes up on top
 * no mappter what the raking it.
 * Then sorting by date -- initial (and temorary) sorting order
 */
App.query.GET_FLOWS = SC.Query.local(App.model.Flow, {orderBy: 'tag_class DESC, date DESC'});
App.query.GET_CONTACTS = SC.Query.local(App.model.Contact);
App.query.GET_TOP_UNCLASSIFIED_CONTACTS = App.query.GET_CONTACTS; // TODO: add qualifier


App.ServerDataSource = SC.DataSource.extend({
	/**
	 * Called by didBecomeFirstResponder of FLOWS state
	 * @returns
	 */
	startDownloadMessages: function() {
		// Launch the query and pull the date of the last message from the DB (if it is there)
		//TODO: DEBUG RESET 
		//App.store.find(App.model.SyncTracker, '1');
		//App.store.createRecord(App.model.SyncTracker, {date: String(new Date())}, '1');
		
		// Give it 2 seconds to pull it from DB
		// this.invokeLater('downloadEarlyMessages', 10);
		
		// start in 5 sec
		//this.invokeLater('downloadNewMessages', 5000);
		this.downloadNewMessages();
	},
	
	downloadNewMessages: function() {
		// find the most recent message in the db
		//var messages = App.store.find(App.model.Message);

		var requestUrl = '/api/1.0/sync/events/';
		
		// Add modified_since if we already have it
		// If not, request all messages.
		// Messages come in order of modified date and are limited in number
		if( App.syncTrackerController.content && App.syncTrackerController.content.length() ) {
			requestUrl = '%@?modified_since=%@'.fmt(
					requestUrl, 
					App.syncTrackerController.content.objectAt(0).get('date'));
		}
		SC.Request.getUrl(requestUrl)
			.header({'Accept': 'application/json'})
			.json()
			.notify(this, '_didGetNewMessages', App.store, App.store.dataSource )
			.send();
//		
//		
//		// minimal date Dec 31 1969 - i wasn't born yet, so there surely cannot be any email earlier that this
//		var latestMessageDate = new Date(0);
//		messages.forEach(function(message) {
//			var currentMessageDate = getDateFromFormat(message.get('modified_date'), "y-M-d H:mm:ss");
//			if(  currentMessageDate > latestMessageDate )
//				latestMessageDate = currentMessageDate;
//		});
	},
	
	_didGetNewMessages: function(response, store, db) {
		// state got cleared while we were getting messages? stop it.
		if( !App.store.dataHashes[App.store.storeKeyFor(App.model.User, '1')] )
			return;
			
		if( SC.ok(response) ) {
			var messageDate = this._processGetMessagesResponse(response, store, db);
		
			this.invokeLater('downloadNewMessages', 5000);
		}
	},
	
//	downloadEarlyMessages: function() {
//		// pull the date cursor from in-memory store -- if we have it in DB it should
//		// now be in memory because of the find() call in startDownloadMessages has pulled it in
//		var earliestMessageDate = App.store.dataHashes[App.store.storeKeyFor(App.model.SyncTracker, '1')];
//		
//		if( !earliestMessageDate ) {
//			// no earliestMessageDate means we're dealing with the cold start
//			// and the DB is empty
//			// add a record with the current time -- meaning we'll be
//			// loading messages from the current time going back
//			// and call this function again in 2s
//
//			App.store.createRecord(App.model.SyncTracker, {date: String(new Date().format("y-M-d H:mm:ss"))}, '1');
//			App.store.dataSource.getNestedDataSource().invokeLater('downloadEarlyMessages', 2000);
//			return;
//		}
//		
//		// we got the time cursor. load X number of messages starting from the cursor
//		// going back in time
//		var r = SC.Request.getUrl('/api/1.0/messages/?limit=%@&modified_before=%@'.fmt(10, earliestMessageDate.date))
//			.header({'Accept': 'application/json'})
//			.json()
//			.notify(this, '_didGetEarlyMessages', App.store, App.store.dataSource )
//			.send();
//	},
	
	_processGetMessagesResponse: function(response, store, db) {
		var lastModifiedTimestamp = null;
		var tags = [];
		response.get('body').tags.forEach(function(tagHash){
			var tag = App.store.dataHashes[App.model.Flow.storeKeyFor(tagHash.guid)];
			if( !tag ) {
				tag = tagHash;
			}
				
			tags.set(tag.guid, tag);
			tags.pushObject(tag);
		});
		
		//TODO: rename conversation to aggregate
		response.get('body').conversations = response.get('body').aggregates;
		response.get('body').conversations.forEach(function(conversation){
			conversation.tags.forEach(function(tagGuid){
				if( tags[tagGuid] ) {
					if (!tags[tagGuid].conversations)
						tags[tagGuid].conversations = [];
					
					if( !tags[tagGuid].conversations.contains(conversation.guid) )
						tags[tagGuid].conversations.pushObject(conversation.guid);
				}
				else {
					console.log( 'Malformed /messages/ response? got %@ tags, but no tag %@ in the list'.fmt(tags.length(), tagGuid));
				}
			});
			conversation.key_participant = conversation.latest_sender;
			var storeKey = store.loadRecord(App.model.Conversation, conversation);
			db.didRetrieveRecordFromNestedStore(store, storeKey);
		});
		
		tags.forEach(function(tag){
			var storeKey = store.loadRecord(App.model.Flow, tag);
			db.didRetrieveRecordFromNestedStore(store, storeKey);
		});
		
		response.get('body').contacts.forEach(function(contact){
			var addressGuids = [];
			contact.addresses.forEach(function(address){
				addressGuids.pushObject(address.email);
				address.contact = contact.guid;
				var storeKey = store.loadRecord(App.model.Address, address);
				db.didRetrieveRecordFromNestedStore(store, storeKey);
			});
			
			contact.addresses = addressGuids;
			var storeKey = store.loadRecord(App.model.Contact, contact);
			db.didRetrieveRecordFromNestedStore(store, storeKey);
		});
		
		response.get('body').messages.forEach(function(message) {
			// get HTML or, if not available,
			// text message body
			if( message.body_type === 'text/html' ) {
				message.body = message.body;
			}
			else {
				message.body = message.body.replace(/\r\n/g, '<br>');
			}
			
			var storeKey = store.loadRecord(App.model.Message, message);
			db.didRetrieveRecordFromNestedStore(store, storeKey);
			
			// the messages are in reverse chronological order.
			// this means the last message we process will carry the timestamp
			// we need to start the next request from
			// remember it here and use it after the forEach loop
			lastModifiedTimestamp = message.modified_date;
		});
		
		// Create or update SyncTracker record
		if( lastModifiedTimestamp ) {
			if( App.syncTrackerController.content.objectAt(0) ) {
				App.syncTrackerController.content.objectAt(0).set('date', lastModifiedTimestamp);
			} else {
				var storeKey = store.loadRecord(App.model.SyncTracker, {'date' : lastModifiedTimestamp});
				db.didRetrieveRecordFromNestedStore(store, storeKey);			
			}
		}
	},
	
//	_didGetEarlyMessages: function(response, store, db) {
//		
//		// state got cleared while we were getting messages? stop it.
//		if( !App.store.dataHashes[App.store.storeKeyFor(App.model.User, '1')] )
//			return;
//			
//		if( SC.ok(response) ) {
//			var messageDate = this._processGetMessagesResponse(response, store, db);
//			
//			// stop trying to download early messages after we get 100 of them
//			// TODO: when using the DB, continue the download, but offload earlier
//			// messages from memory
//			if( App.store.find(App.model.Message) > 50 )
//				return;
//			
//			if( messageDate ) {
//				// non-empty messageDate means we got some messages i.e. we're
//				// not at the end of the mail archive.
//				// let's continue loading then
//				var earliestMessageDate = App.store.find(App.model.SyncTracker, '1');
//				earliestMessageDate.set('date', messageDate);
//				this.invokeLater('downloadEarlyMessages', 1000); 
//			} else if( App.store.find(App.model.Message).length() === 0) {
//				// We did not get any messages AND app's store is empty.
//				//
//				// During the initial boot this API call may come
//				// before the server has the available data.
//				// Assume that if the app has 0 messages, this means we're in that state
//				// This means the app should continue trying to downloadMessages
//				this.invokeLater('downloadEarlyMessages', 1000*5); 
//			} else {
//				// We did not get anything from the server, but we have something in the local store
//				//
//				// run a routine check for past messages then, every 1 min
//				this.invokeLater('downloadEarlyMessages', 1000*10); 
//			} 
//		}
//	},
	
	_loadTags: function(hashes, convIDs, store, db){
		hashes.forEach(function(h) {
			if(h.name === 'INBOX') {
				h.name = 'Unlabaled';
			}
			// Load the contact
			var convIDs = [];
			h.conversations.forEach(function(c) {
				convIDs.pushObject(c.guid);
				
				// We're assuming that the contact and email 
				// were already loaded,
				
				// substitute the payload data
				// with the ID to the address (which is email)
				c.key_participant = c.key_participant.email;
			});
			
			
			// 1. create conversation objects
			store.loadRecords(App.model.Conversation, h.conversations);
			
			// 2. no that conversation records are created
			// we no longer need the data so we overwrite it with its IDs.
			h.conversations = convIDs;
		});
		
		// 4. create Flows with references to conversations (loaded at step 1) 
		var records = store.loadRecords(App.model.Flow, hashes);
		
		// notify the db so that it can load it
		if( db ) {
			records.forEach(function(record) {
				db.didRetrieveRecordFromNestedStore(store, record.storeKey);
			});
			//TODO unload record from memory?
		}
	},	
	/**
	 * Look for an actual Query object to see what is being requested
	 * and map it to the API call
	 */
	fetch: function (store, query, params) {
		return NO;
	},	
//		if( query === App.query.GET_CONVERSATIONS ) {
//			SC.Request.getUrl('/api/1.0/conversations/')
//				.header({'Accept': 'application/json'})
//				.json()
//				.notify(this, '_didGetConversations', App.model.Conversation, store, query, params )
//				.send();
//			return YES;
//		} else if ( query === App.query.GET_FLOWS ) {
//			// skip gmail's own folders
//			SC.Request.getUrl('/api/1.0/tags/?notstartswith=[Gmail]&conversations=1')
//				.header({'Accept': 'application/json'})
//				.json()
//				.notify(this, '_didGetFlows', store, query, params )
//				.send();
//			
//			
//			return YES;
//		} else if ( query === App.query.GET_CONTACTS ) {
//			SC.Request.getUrl('/api/1.0/contacts/')
//				.header({'Accept': 'application/json'})
//				.json()
//				.notify(this, '_didGetContacts', store, query, params )
//				.send();
//		} else if ( query.recordType === App.model.Conversation 
//					&& query.conditions 
//					&& query.conditions.search('{conversationGuid}') != -1) {
//			
//			SC.Request.getUrl('/api/1.0/conversations/' 
//											+ query.conversationGuid 
//											+ '/?message_body=1')
//				.header({'Accept': 'application/json'})
//				.json()
//				.notify(this, '_didGetConversationFromQuery', store, query, params )
//				.send();
//			return YES;			
//		}
//	},
	
//	_didGetConversations: function (response, model, store, query, params) {
//		if (SC.ok(response)) {
//			store.loadRecords(model, response.get('body').content);
//			store.dataSourceDidFetchQuery(query);
//			if( params && params.outerDataSource ) 
//				params.outerDataSource.didRetrieveQueryFromNestedStore(store, query);
//		}
//		else {
//			store.dataSourceDidErrorQuery(query, response);
//		}
//	},
//	
	
	/**
	 * The conversation JSON includes the message body. We'll use it
	 * to load the Message records.
	 * 
	 * For brevity, this handler is called by both fetch() and retrieveRecord(). In case of fetch()
	 * the query is specified by a 'query' object. In case of retrieveRecord() it is a storeKey.
	 */
//	_didGetConversationFromQuery: function (response, store, query, params) {
//		if (SC.ok(response)) {
//			// for some reason response.get('body') doesn't
//			// have KVO features, so wrapping it into SC.Object
//			var hashes = SC.Object.create(response.get('body'));
//		
//			var messageIDs = [];
//			hashes.messages.forEach(function(m) {
//				messageIDs.pushObject(m.guid);
//				
//				// get HTML or, if not available,
//				// text message body
//				if( m.body_type === 'text/html' ) {
//					m.body = m.body;
//				}
//				else {
//					m.body = m.body.replace(/\r\n/g, '<br>');
//				}
//			});
//			var storeKeys = store.loadRecords(App.model.Message, hashes.messages);
//			if( params && params.outerDataSource )
//				storeKeys.forEach(function(storeKey) {
//					params.outerDataSource.didRetrieveRecordFromNestedStore(store, storeKey);
//				});
//			
//			hashes.messages = messageIDs;
//
//			// now that the messages are loaded and 'messages'
//			// array is patched to include the IDs we can load
//			// the conversation into the store
//			store.loadRecord(App.model.Conversation, hashes);
//			
//			store.dataSourceDidFetchQuery(query);
//			
//			if( params && params.outerDataSource ) 
//				params.outerDataSource.didRetrieveQueryFromNestedStore(store, query);
//		}
//		else {
//			store.dataSourceDidErrorQuery(queryOrKey, response);
//		}
//	},
	/**
	 * The conversation JSON includes the message body. We'll use it
	 * to load the Message records.
	 * 
	 * For brevity, this handler is called by both fetch() and retrieveRecord(). In case of fetch()
	 * the query is specified by a 'query' object. In case of retrieveRecord() it is a storeKey.
	 */
//	_didGetConversation: function (response, store, storeKey, id, params) {
//		if (SC.ok(response)) {
//			// for some reason response.get('body') doesn't
//			// have KVO features, so wrapping it into SC.Object
//			var hashes = SC.Object.create(response.get('body'));
//		
//			var messageIDs = [];
//			hashes.messages.forEach(function(m) {
//				messageIDs.pushObject(m.guid);
//				
//				// get HTML or, if not available,
//				// text message body
//				if( m.body_type === 'text/html' ) {
//					m.body = m.body;
//				}
//				else {
//					m.body = m.body.replace(/\r\n/g, '<br>');
//				}
//			});
//			store.loadRecords(App.model.Message, hashes.messages);
//			hashes.messages = messageIDs;
//
//			// now that the messages are loaded and 'messages'
//			// array is patched to include the IDs we can load
//			// the conversation into the store
//			store.loadRecord(App.model.Conversation, hashes);
//			
//			if( params && params.outerDataSource ) 
//				params.outerDataSource.didRetrieveRecordFromNestedStore(store, storeKey, id);
//		}
//		else {
//			store.dataSourceDidErrorQuery(queryOrKey, response);
//		}
//	},
	/**
	 * The flow JSON includes flows (tags) and conversations as nested objects
	 * loadRecords() isn't smart enough to figure out how to create store records
	 * for nested objects.
	 * This function does the following:
	 * First, it scans all nested conversations and loads them in the store as records
	 * Second, it replaces the nested conversations objects with their IDs
	 * Third, now that all "conversations" property no longer includes the
	 * conversation data (just the guids to conversations), we create the Flow objects.
	 */
	_didGetFlows: function (response, store, query, params) {
		if (SC.ok(response)) {
			var hashes = response.get('body').content;
			hashes.forEach(function(h) {
				if(h.name === 'INBOX') {
					h.name = 'Unlabaled';
				}
				// Load the contact
				var convIDs = [];
				h.conversations.forEach(function(c) {
					convIDs.pushObject(c.guid);
					
					// We're assuming that the contact and email 
					// were already loaded,
					
					// substitute the payload data
					// with the ID to the address (which is email)
					c.key_participant = c.key_participant.email;
				});
				
				
				// 1. create conversation objects
				store.loadRecords(App.model.Conversation, h.conversations);
				
				// 2. no that conversation records are created
				// we no longer need the data so we overwrite it with its IDs.
				h.conversations = convIDs;
			});
			
			// 4. create Flows with references to conversations (loaded at step 1) 
			var records = store.loadRecords(App.model.Flow, hashes);
			
			
			store.dataSourceDidFetchQuery(query);
			if( params && params.outerDataSource ) 
				params.outerDataSource.didRetrieveQueryFromNestedStore(store, query);
		}
		else {
			store.dataSourceDidErrorQuery(query, response);
		}
	},

	/**
	 * Same logic as above but for contacts and addresses
	 */
	_didGetContacts: function (response, store, query, params ) {
		if (SC.ok(response)) {
			var contacts = response.get('body').content;
			contacts.forEach(function(contact){
				var addressIDs = [];
				contact.addresses.forEach(function(address) {
					address.contact = contact.guid;
					addressIDs.pushObject(address.email);
				});
				store.loadRecords(App.model.Address, contact.addresses);
				
				contact.addresses = addressIDs;
			});
			store.loadRecords(App.model.Contact, contacts);
			if( params && params.outerDataSource ) 
				params.outerDataSource.didRetrieveQueryFromNestedStore(store, query);
		}
		else {
			store.dataSourceDidErrorQuery(query, response);
		}
	},
	
	retrieveRecord: function(store, storeKey, id, params) {
		if( SC.kindOf(SC.Store.recordTypeFor(storeKey), App.model.Conversation) ) {
			SC.Request.getUrl('/api/1.0/conversations/%@/?message_body=1'.fmt(id))
				.header({'Accept': 'application/json'})
				.json()
				.notify(this, '_didGetConversation', store, storeKey, id, params )
				.send();
			return YES;
		}
		return NO;
	},

	/**
	 * Only handles the creation of the account record. The account JSON is sent
	 * to the server via a PUT because the account ID is generated by the app.
	 * If username parameter isn't provided the server will create the User
	 * object and return it back.
	 * 
	 * This function initiates the API call. The response handling takes place
	 * in _didCreateRecordAccount
	 * 
	 * @param store
	 * @param storeKey
	 * @param params
	 * @returns YES in case we were asked to create an Account, NO in any other
	 *          case
	 */
	createRecord : function(store, storeKey, params) {
		if (SC.kindOf(store.recordTypeFor(storeKey), App.model.Account)) {
			// check to see if we already have a user object.
			// This is a synchronous call to the store that will not attempt
			// to call the DataSource in case the object isn't found.
			// The id of '1' is well-known because the User record is a
			// singleton.
			//TODO: refactor to user User.ID
			user = store.dataHashes[store.storeKeyFor(App.model.User, '1')];
			var id = store.idFor(storeKey);
			var url = '/api/1.0/accounts/'+id+'/';
			if( user ) {
				url = url + '?username=' + user.get('username');
			}
			
			// send a PUT request with the JSON of the storeKey and call
			// _didCreateRecordAccount to process the response
			SC.Request.putUrl(url)
				.header({
	                'Accept': 'application/json'
	            })
	            .json()
				.notify(this, '_didCreateRecordAccount', store, storeKey, params )
				.send(store.readDataHash(storeKey));
				
			return YES;
		}
		
		// Don't handle the creation of any other type of record.
		return NO;
	},
	
	updateRecord: function(store, storeKey, params) {
		console.log('Will update store key %@ params=%@'.fmt(storeKey, params));
		if( App.store.recordTypeFor(storeKey).toString().split('.')[1] === 'Contact' ) {
			var url = '/api/1.0/contacts/%@/'.fmt(App.store.idFor(storeKey));
			SC.Request.putUrl(url)
				.header({'Accept': 'application/json'})
				.json()
				.notify(this, '_didUpdateContactRecord', store, storeKey, params)
				.send(store.readDataHash(storeKey));
			
			return YES;
		}
		return NO;
	},
	_didUpdateContactRecord: function(response, store, storeKey, params) {
		if (SC.ok(response)) {
			console.log('responce to PUT /contacts/: %@'.fmt(response.get('body')));
		} else {
			console.log(response.rawRequest.responseText);
		}
	},
	/**
	 * When an account record is created on the server, the server sends back
	 * the JSON representing the User record. We persist this record in
	 * in-memory store and subsequently in the DB.
	 * 
	 * @param response HTTP response object
	 * @param store
	 * @param storeKey key of the record that caused this response (an Account record)
	 * @param params passed though from the caller of createRecord
	 * @returns
	 */
	_didCreateRecordAccount: function(response, store, storeKey, params) {
		if (SC.ok(response)) {
			console.log('responce to PUT /account/: %@'.fmt(response.get('body')));
					
			// create a User object if it doesn't yet exist
			if( !store.dataHashes[store.storeKeyFor(App.model.User, '1')] ) {
				store.createRecord(App.model.User, response.get('body'), '1');
			} else {
				console.log('NOT creating user object');
			}
		} else {
			console.log(response.rawRequest.responseText);
			store.dataSourceDidError(storeKey, response);
		}
	}
});
//App.ServerDataSource.EARLIEST_MESSAGE_DATE_RECORD_ID = 'earliestMessageDate';
//App.ServerDataSource.earliestMessageDate = SC.ObjectController.create({
//	contentPropertyDidChange: function(target, key) {
//		sc_super();
//		App.store.dataSource.getNestedDataSource().downloadMessages();
//	}
//});

