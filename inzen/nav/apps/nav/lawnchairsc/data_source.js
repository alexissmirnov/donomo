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
    specific query, triggered by find().  This method is called anytime
    you invoke SC.Store#find() with a query or SC.RecordArray#refresh().  You 
    should override this method to actually retrieve data from the server 
    needed to fulfill the query.  If the query is a remote query, then you 
    will also need to provide the contents of the query as well.
    
    h3. Handling Local Queries
    
    Most queries you create in your application will be local queries.  Local
    queries are populated automatically from whatever data you have in memory.
    When your fetch() method is called on a local queries, all you need to do
    is load any records that might be matched by the query into memory. 
    
    The way you choose which queries to fetch is up to you, though usually it
    can be something fairly straightforward such as loading all records of a
    specified type.
    
    When you finish loading any data that might be required for your query, 
    you should always call SC.Store#dataSourceDidFetchQuery() to put the query 
    back into the READY state.  You should call this method even if you choose
    not to load any new data into the store in order to notify that the store
    that you think it is ready to return results for the query.
    
    h3. Handling Remote Queries
    
    Remote queries are special queries whose results will be populated by the
    server instead of from memory.  Usually you will only need to use this 
    type of query when loading large amounts of data from the server.
    
    Like Local queries, to fetch a remote query you will need to load any data
    you need to fetch from the server and add the records to the store.  Once
    you are finished loading this data, however, you must also call
    SC.Store#loadQueryResults() to actually set an array of storeKeys that
    represent the latest results from the server.  This will implicitly also
    call datasSourceDidFetchQuery() so you don't need to call this method 
    yourself.
    
    If you want to support incremental loading from the server for remote 
    queries, you can do so by passing a SC.SparseArray instance instead of 
    a regular array of storeKeys and then populate the sparse array on demand.
    
    h3. Handling Errors and Cancelations
    
    If you encounter an error while trying to fetch the results for a query 
    you can call SC.Store#dataSourceDidErrorQuery() instead.  This will put
    the query results into an error state.  
    
    If you had to cancel fetching a query before the results were returned, 
    you can instead call SC.Store#dataSourceDidCancelQuery().  This will set 
    the query back into the state it was in previously before it started 
    loading the query.
    
    h3. Return Values
    
    When you return from this method, be sure to return a Boolean.  YES means
    you handled the query, NO means you can't handle the query.  When using
    a cascading data source, returning NO will mean the next data source will
    be asked to fetch the same results as well.
    
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
			console.log('DatabaseDataSource.fetch: Read from %@ got %@ records'
					.fmt(name.table, records.length));

			records.forEach(function(record) {
				console.log('DatabaseDataSource.fetch: Read from %@ loading record id:%@'
					.fmt(name.table, record.key));
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
    retrieveRecord : function(store, storeKey, id) {
		var name = this._getStoreTableNamesFromStoreKey(storeKey);
		var id = store.idFor(storeKey);
		var table = this._getTable(name.store, name.table);
		var that = this;
		table.get(id, function(record) {
			
			console.log('DatabaseDataSource.retrieveRecord: Read %@:%@ got %@'
					.fmt(name.table, id, record));
			
			if( record ) {
				store.loadRecord(SC.Store.recordTypeFor(storeKey), 
						record.record,
						record.key);
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
			}
		});
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
		console.log('DatabaseDataSourcecreateRecord: insert into %@ key %@ values %@'.fmt(name.table, id, JSON.stringify(dataHash)));
		
		table.insert( {
			key : id,
			record : dataHash
		}, function() {
			console.log('DatabaseDataSource.createRecord: Wrote %@:%@ to db'
					.fmt(name.table, id));
			
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
	
		table.remove(
			id,
			function() {
				console.log('DatabaseDataSource.destroyRecord: Deleted %@:%@ to db'
								.fmt(name.table, id));

			});
	
		return YES;
	}  

});
