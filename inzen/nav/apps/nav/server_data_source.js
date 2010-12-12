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
	downloadNewMessages: function() {
		var requestUrl = '/api/1.0/sync/events/';
		
		// Add modified_since if we already have it
		// If not, request all messages.
		// Messages come in order of modified date and are limited in number
		if( App.syncTrackerController.content ) {
			requestUrl = '%@?modified_since=%@'.fmt(
					requestUrl, 
					App.syncTrackerController.timestamp());
		}
		SC.Request.getUrl(requestUrl)
			.header({'Accept': 'application/json'})
			.json()
			.notify(this, '_didGetNewMessages', App.store, App.store.dataSource )
			.send();
	},
	
	_didGetNewMessages: function(response, store, db) {
		// Only run this if the User object still exists
		// state got cleared while we were getting messages? stop calling downloadNewMessages
		if( !App.userController.user() )
			return;
		
		if( response.status >= 500 ) {
			// retry on server error
			this.invokeLater('downloadNewMessages', 10000);
		} else if( response.status === 200 ) {
			// process successful response
			var messageDate = this._processGetMessagesResponse(response, store, db);
		
			this.invokeLater('downloadNewMessages', 5000);
		} else if( response.status === 403 ) {
			var username = App.userController.user();
			// try logging in if forbidden
			// 403 response should come with the login URL in Locaiton header
			SC.Request.postUrl(response.header('Location'))
				.header({'Accept': 'application/json', 'Content-Type' :'application/x-www-form-urlencoded'})
				.notify(this, 'handleLoginResponse')
				.send('username=%@&password=%@'.fmt(username, username));	
		}
	},
	
	handleLoginResponse: function(response, store, db) {
		if( response.status === 403 ) {
			// Can't login with the credentials we already have?
			// delete user and account and start from scratch
			// TODO: handle this case more gracefully
			App.store.destroyRecord(App.model.User, App.model.User.prototype.ID);
			App.accountController.get('content').forEach(function(a) {
				App.store.destroyRecord(App.model.Account, a.get('guid'));});
			App.state.transitionTo(App.state.START);
		} else if ( response.status === 200 ) {
			this.downloadNewMessages();
		}
	},
		
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
		//TODO: define status constants
		response.get('body').aggregates.forEach(function(conversation){
			if( conversation.status === '-1' &&
					App.model.Conversation.storeKeysById()[conversation.guid]) {
				/**
				 * destroyRecord if it exists and it's status is -1 (deleted)
				 * 
				 * Using storeKeysById() here to prevent calling destroyRecord
				 * in case the record for this id doesn't exist
				 */
				store.destroyRecord(App.model.Conversation, conversation.guid);
			} else if( conversation.status === '1' ) {
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
			}
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
//			App.model.SyncTracker.objects().getOrCreate(
//					{guid: App.model.SyncTracker.prototype.ID}, 
//					{date: lastModifiedTimestamp},
//					function(record, created) {
//						if( !created )
//							record.set('date', lastModifiedTimestamp);
//					});
			
			if( App.syncTrackerController.content && App.syncTrackerController.content.objectAt(0)) {
				App.syncTrackerController.content.objectAt(0).set('date', lastModifiedTimestamp);
			} else {
				store.createRecord(App.model.SyncTracker, 
									{'date' : lastModifiedTimestamp}, 
									App.model.SyncTracker.prototype.ID);
			}
		}
	},
	
	/**
	 * Look for an actual Query object to see what is being requested
	 * and map it to the API call
	 */
	fetch: function (store, query, params) {
		return NO;
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
	createRecord: function(store, storeKey, params) {
		if (SC.kindOf(store.recordTypeFor(storeKey), App.model.Account)) {
			this.createAccountRecord(store, storeKey, params);
		}
	},
	createAccountRecord: function(store, storeKey, params) {
		var id = store.idFor(storeKey);
		var url = '/api/1.0/accounts/'+id+'/';
//				if( store.dataHashes[store.storeKeyFor(App.model.User, '1')] ) {
		if(  App.userController.user() ) {
			url = url + '?username=' + App.userController.user().get('username');
		}
		SC.Request.putUrl(url)
			.header({
	            'Accept': 'application/json'
	        })
	        .json()
			.notify(this, '_didCreateRecordAccount', store, storeKey, params )
			.send(store.readDataHash(storeKey));
		return YES;
		
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
					
//			App.User.objects().getOrCreate({guid: App.model.User.prototype.ID}, response.get('body'), 
//					function(record, created){
//						console.log('getOrCreate returned %@ Created? %@'.fmt(record, created));
//					});
			// create a User object if it doesn't yet exist
			if( !store.dataHashes[store.storeKeyFor(App.model.User, '1')] ) {
				store.createRecord(App.model.User, response.get('body'), App.model.User.prototype.ID);
			} else {
				console.log('NOT creating user object');
			}
		} else {
			console.log(response.rawRequest.responseText);
			store.dataSourceDidError(storeKey, response);
		}
	}
});
