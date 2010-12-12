
App = Signup;

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

App.Account = App.Record.extend( {
	accountClass : SC.Record.attr(String, {defaultValue: 'email/gmail'}),
	password : SC.Record.attr(String),
	name : SC.Record.attr(String)
});

App.User = App.Record.extend( {
	ID: 'user.1',
	username : SC.Record.attr(String)
});

App.Message = App.Record.extend({
	body : SC.Record.attr(String)
});

