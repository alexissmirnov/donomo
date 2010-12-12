LawnchairSC = Nav;


/*
 * http://markmail.org/message/cu5yc55ynrn525dv
 * This will provide you with the defaultValue function on the primaryKey, that
 * will be run each time any record will be created without providing explicit
 * guiid.
 * 
 * This mixin allows calling SC.Store.createRecord without providing the id
 */
SC.mixin( SC.Record.prototype,{
	guid : SC.Record.attr(String, { defaultValue : function() {
			var i, rnum, chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz", strLen = 8, ret = '';
			for (i = 0; i < strLen; i++) {
				rnum = Math.floor(Math.random() * chars.length);
				ret += chars.substring(rnum, rnum + 1);
			}
			return ret;
		}
	})
});

LawnchairSC.DataSource = SC.DataSource.extend({
	
	/**
	 * The database may not be up-to-date with the latest data, not it always contains
	 * full dataset of the application.
	 * 
	 * If innerDataSource is set, it will get called in the following cases:
	 * - if a record ID is not found in this datasource. When innerDataSource retrieves the record, this datasource will be updated.
	 * - if a record is deleted.
	 * - if a record is updated. innerDataSource will receive the record so that it can updated its datasource.
	 * 
	 */
	nestedDataSource: null,
	
	// lazily convert data source to real object
	getNestedDataSource : function() {
		var ret = this.get('nestedDataSource');
		if (typeof ret === SC.T_STRING) {
			ret = SC.objectForPropertyPath(ret);
			if (ret)
				ret = ret.create();
			if (ret)
				this.set('nestedDataSource', ret);
		}
		return ret;
	},	
	/*
	 * A list of cached datastores keyed by record type.
	 */
	_tables : {},
	
	_getStoreTableNamesFromStoreKey : function(storeKey) {
		return this._getStoreTableNamesFromRecordType(
						SC.Store.recordTypeFor(storeKey));
	},
	/**
	 * Uses a convention to generate database name and a table name from a
	 * record type. A record type is assumed to take the form
	 * MyApp.someModule.Model (eg. MyApp.models.Calendar) The application's name
	 * is used as the database name. The table name is a concatenation of the
	 * rest of the absolute path to the module. In example above the DB
	 * would be called MyApp and the table with calendar records would be called
	 * "models_Calendar"
	 * 
	 * @param recordType
	 * @returns an object with two properties: store and table.
	 */
	_getStoreTableNamesFromRecordType: function(recordType) {
		var nameParts = recordType.toString().split('.');
		var tableName = [];
		for(var i = 1; i < nameParts.length; i++) tableName.push(nameParts[i]);
		return {
			store : nameParts[0],
			table : tableName.join('_')
		};
	},
	
	_getTable: function(storeName, tableName) {
		var table = this._tables[tableName];
		
		if (!table) {
			table = new Lawnchair( {
				display : storeName,
				name : storeName,
				table : tableName,
				adaptor : 'dom',
				onError : function(tx, e, msg) {
					SC.Logger.error("Lawnchair error: %@ (%@)".fmt(msg, e.message));
				}
			});
			this._tables[tableName] = table;
		}
		
		return table;
	},
	
	getTable: function(recordType) {
		var name = this._getStoreTableNamesFromRecordType(recordType);
		return this._getTable(name.store, name.table);
	},
	
	_dropAllTables: function() {
		for (var table in this._tables) {
			if ( this._tables.hasOwnProperty(table)) {
				this._tables[table].nuke();
			}
		}
	},

  // ..........................................................
  // SC.STORE ENTRY POINTS
  // 
  

  /**
    Invoked by the store whenever it needs to retrieve data matching a 
    specific query, triggered by find(). 
    
    @param {SC.Store} store the requesting store
    @param {SC.Query} query query describing the request
    @returns {Boolean} YES if you can handle fetching the query, NO otherwise
  */
  fetch : function(store, query) {
		var name = this._getStoreTableNamesFromRecordType(query.recordType);

		table = this._getTable(name.store, name.table);

		if (!table) {
			return NO;
		}

		that = this;
		// Don't attempt to query the DB if the app is asking to perform a
		// remote query
		if( query.isRemote() ) {
			var nestedDataSource = that.getNestedDataSource();
			if( nestedDataSource ) {
				nestedDataSource.fetch(
						store, 
						query,
						{outerDataSource: that});
			}
			return YES;
		}
		
		table.all(function(records) {
//			console.log('DatabaseDataSource.fetch: Read from %@ got %@ records'
//					.fmt(name.table, records.length));

			records.forEach(function(record) {
//				console.log('DatabaseDataSource.fetch: Read from %@ loading record id:%@'
//					.fmt(name.table, record.key));
				store.loadRecord(query.recordType, record.record, record.key);
			});
			
			if( records.length === 0 && name.table === 'SchemaVersion' ) {
				var r = App.store.createRecord(App.model.SchemaVersion, {version: '0.1.0'}, '1');
				store.dataSourceDidFetchQuery(query);
				return YES;
			}
			// If the query returned no results, delegate it to 
			// the nested datasource.
			// TODO: We're only dealing with this one special case where the
			// DB returns no records and interpret this as a signal that we need to
			// ask the server.. Need a generic sync solution.
			if( records.length === 0 ) {
				var nestedDataSource = that.getNestedDataSource();
				if( nestedDataSource ) {
					nestedDataSource.fetch(
							store, 
							query,
							{outerDataSource: that});
				}
			}
			else {
				store.dataSourceDidFetchQuery(query);
			}
		});
		
		
		return YES;
	},

  /**
    Invoked by the store whenever it needs to cancel one or more records that
    are currently in-flight.  If any of the storeKeys match records you are
    currently acting upon, you should cancel the in-progress operation and 
    return YES.
    
    If you implement an in-memory data source that immediately services the
    other requests, then this method will never be called on your data source.
    
    To support cascading data stores, be sure to return NO if you cannot 
    retrieve any of the keys, YES if you can retrieve all of the, or
    SC.MIXED_STATE if you can retrieve some of the.
    
    @param {SC.Store} store the requesting store
    @param {Array} storeKeys array of storeKeys to retrieve
    @returns {Boolean} YES if data source can handle keys
  */
  cancel: function(store, storeKeys) {
    return NO;
  },
  

  // ..........................................................
  // SINGLE RECORD ACTIONS
  // 
  
  /**
    Called from updatesRecords() to update a single record.  This is the 
    most basic primitive to can implement to support updating a record.
    
    To support cascading data stores, be sure to return NO if you cannot 
    handle the passed storeKey or YES if you can.
    
    @param {SC.Store} store the requesting store
    @param {Array} storeKey key to update
    @param {Hash} params to be passed down to data source. originated
      from the commitRecords() call on the store
    @returns {Boolean} YES if handled
  */
  updateRecord: function(store, storeKey, params) {
		// get or create a table
	    var name = this._getStoreTableNamesFromStoreKey(storeKey);
		var id = store.idFor(storeKey);

		var table = this._getTable(name.store, name.table);

		// store the record
		var dataHash = store.readDataHash(storeKey);
		var that = this;
		table.update( {
			key : id,
			record : dataHash
		}, function() {
			console.log('DatabaseDataSource.updateRecord: Wrote %@:%@ to db'
					.fmt(name.table, id));
			
			store.writeStatus(storeKey, SC.Record.READY_CLEAN);
			
			var nestedDataSource = that.getNestedDataSource();
			if( nestedDataSource ) {
				nestedDataSource.updateRecord(store, storeKey, params);
			}
		});

		
		return YES;
  },

  /**
    Called from retrieveRecords() to retrieve a single record.
    
    If the record isn't found in the DB, nested datasource will be asked.
    If nested datasource does have the record, it will then be cached in the DB.
    
    @param {SC.Store} store the requesting store
    @param {Array} storeKey key to retrieve
    @param {String} id the id to retrieve
    @returns {Boolean} YES if handled
  */
    retrieveRecordWithCallbacks : function(store, storeKey, id, onFound, onNotFound) {
		var name = this._getStoreTableNamesFromStoreKey(storeKey);
		var id = store.idFor(storeKey);
		var table = this._getTable(name.store, name.table);
		var that = this;
		table.get(id, function(record) {
			
//			console.log('DatabaseDataSource.retrieveRecord: Read %@:%@ got %@'
//					.fmt(name.table, id, record));
			
			if( record ) {
				store.loadRecord(SC.Store.recordTypeFor(storeKey), 
						record.record,
						record.key);
				
				if( onFound ) onFound(store, storeKey, id, record);
			} else {
				/*
				 * Can't find the record by ID?
				 * Try nested source then 
				 */
				var nestedDataSource = that.getNestedDataSource();
				if( nestedDataSource ) {
					nestedDataSource.retrieveRecord(
							store, 
							storeKey, 
							id, 
							{outerDataSource: that});
				}
				if( onNotFound ) onNotFound(store, storeKey, id, record);
			}
		});
	},
	retrieveRecord: function(store, storeKey, id) {
		retrieveRecordWithCallbacks(store, storeKey, id, null, null);
	},
	
	
	/**
	 * When a nested data source retrieves the record, it writes it into
	 * in-memory store, but doesn't not insert it into the DB. This callback is
	 * called by the nested DS to let the DBDS insert the content into the DB.
	 * 
	 * @param store
	 * @param query
	 *            The query that was retrieved.
	 * @returns
	 */
	didRetrieveQueryFromNestedStore : function(store, query) {
		var records = store.find(query);
		var that = this;
		records.forEach(function(record) {
			that.didRetrieveRecordFromNestedStore(store, record.storeKey);
		});
	},

	/**
	 * The app tried to retrieveRecord, but this DB-backed datasource passed the control
	 * to the nested datasource.
	 * The nested datasource end up retrieving the record and did put it into the in-memory
	 * store. But this datastore is not in position to insert the record into DB.
	 * 
	 * This callback puts the record into the DB
	 */
	didRetrieveRecordFromNestedStore: function(store, storeKey) {
		// get or create a table
	    var name = this._getStoreTableNamesFromStoreKey(storeKey);
		var id = store.idFor(storeKey);

		var table = this._getTable(name.store, name.table);

		// store the record
		var dataHash = store.readDataHash(storeKey);
		var that = this;
		table.insert( {
				key : dataHash.guid,
				record : dataHash
			}, 
			function() {
				console.log('DatabaseDataSource.didRetrieveRecordFromNestedStore: Wrote %@:%@ to db'
					.fmt(name.table, dataHash.guid));
			});
	},
  

	/**
	 * Called from createdRecords() to created a single record. This is the most
	 * basic primitive to can implement to support creating a record.
	 * 
	 * To support cascading data stores, be sure to return NO if you cannot
	 * handle the passed storeKey or YES if you can.
	 * 
	 * @param {SC.Store}
	 *            store the requesting store
	 * @param {Array}
	 *            storeKey key to update
	 * @param {Hash}
	 *            params to be passed down to data source. originated from the
	 *            commitRecords() call on the store
	 * @returns {Boolean} YES if handled
	 */
	createRecord : function(store, storeKey, params) {
		// get or create a table
	    var name = this._getStoreTableNamesFromStoreKey(storeKey);
		var id = store.idFor(storeKey);

		var table = this._getTable(name.store, name.table);

		// store the record
		var dataHash = store.readDataHash(storeKey);
		var that = this;
//		console.log('DatabaseDataSourcecreateRecord: insert into %@ key %@ values %@'.fmt(name.table, id, JSON.stringify(dataHash)));
		
		table.insert( {
			key : id,
			record : dataHash
		}, function() {
//			console.log('DatabaseDataSource.createRecord: Wrote %@:%@ to db'
//					.fmt(name.table, id));
			
			store.writeStatus(storeKey, SC.Record.READY_CLEAN);
			
			var nestedDataSource = that.getNestedDataSource();
			if( nestedDataSource ) {
				nestedDataSource.createRecord(store, storeKey, params);
			}
		});

		
		return YES;
	},
    /**
	 * Called from destroyRecords() to destroy a single record. This is the most
	 * basic primitive to can implement to support destroying a record.
	 * 
	 * To support cascading data stores, be sure to return NO if you cannot
	 * handle the passed storeKey or YES if you can.
	 * 
	 * @param {SC.Store}
	 *            store the requesting store
	 * @param {Array}
	 *            storeKey key to update
	 * @param {Hash}
	 *            params to be passed down to data source. originated from the
	 *            commitRecords() call on the store
	 * @returns {Boolean} YES if handled
	 */
	destroyRecord : function(store, storeKey, params) {
		var name = this._getStoreTableNamesFromStoreKey(storeKey);
		var id = store.idFor(storeKey);
		var table = this._getTable(name.store, name.table);
		var that = this;
		
		table.remove(
			id,
			function() {
//				console.log('DatabaseDataSource.destroyRecord: Deleted %@:%@ to db'
//								.fmt(name.table, id));

				var nestedDataSource = that.getNestedDataSource();
				if( nestedDataSource ) {
					nestedDataSource.destroyRecord(store, storeKey, params);
				}

				store.unloadRecord(undefined, undefined, storeKey);
				// See thread "SC.Store leaking memory"
				// http://sproutcore.markmail.org/thread/ob2acolksydfoe2o
				delete store.statuses[storeKey];
			});
	
		return YES;
	}  

});
