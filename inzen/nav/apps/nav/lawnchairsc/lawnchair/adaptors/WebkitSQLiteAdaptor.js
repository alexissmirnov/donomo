/**
 * WebkitSQLiteAdaptor
 * ===================
 * Sqlite implementation for Lawnchair.
 *
 */
var WebkitSQLiteAdaptor = function(options) {
	for (var i in LawnchairAdaptorHelpers) {
		this[i] = LawnchairAdaptorHelpers[i];
	}
	this.init(options);
};


WebkitSQLiteAdaptor.prototype = {
	init:function(options) {
		var that = this;
		var merge = that.merge;
		var opts = (typeof arguments[0] == 'string') ? {table:options} : options;

		// default properties
		this.name		= merge('Lawnchair', opts.name	  	);
		this.version	= merge('1.0',       opts.version 	);
		this.table 		= merge('field',     opts.table	  	);
		this.display	= merge('shed',      opts.display 	);
		this.max		= merge(65536,       opts.max	  	);
		this.db			= merge(null,        opts.db		);
		this.perPage    = merge(10,          opts.perPage   );

		// default sqlite callbacks
		this.onError = function(){};
		this.onData  = function(){};

		if("onError" in opts) {
			this.onError = opts.onError;
		}

		// error out on shit browsers
		if (!window.openDatabase)
			throw('Lawnchair, "This browser does not support sqlite storage."');

		// instantiate the store
		this.db = openDatabase(this.name, this.version, this.display, this.max);

		// create a default database and table if one does not exist
		this.db.transaction(
			function(tx) {
				tx.executeSql("SELECT COUNT(*) FROM " + that.table, [], function(){}, function(tx, error) {
					that.db.transaction(function(tx) {
						tx.executeSql("CREATE TABLE "+ that.table + " (id NVARCHAR(32) UNIQUE PRIMARY KEY, value TEXT, timestamp REAL)", [], function(){
							console.log('created table %@'.fmt(that.table));
						}, that.onError);
					});
				});
			},
			that.onError,
			function() { console.log('Init: tx succeeded on table %@'.fmt(that.table)); }
		);
	},
	update: function(id, obj, callback) {
		var that = this;
		that.db.transaction(function(t) {
			console.log("SQL: UPDATE %@ SET value=%@, timestamp=%@ WHERE id=%@".fmt(that.table, that.serialize(obj), that.now(), id));
			t.executeSql(
				"UPDATE " + that.table + " SET value=?, timestamp=? WHERE id=?",
				[that.serialize(obj), that.now(), id],
				function() {
					if (callback != undefined) {
						obj.key = id;
						that.terseToVerboseCallback(callback)(obj);
					}
				},
				that.onError);
			},
			that.onError,
			function() { console.log('update: SQL void callback was called'); }
		);
	},
	insert: function(obj, callback) {
		var that = this;
		
		console.log("Lawnchair.save.insert obj=%@".fmt(obj));
		
		that.db.transaction(function(t) {
			console.log("Lawnchair.save.insert.transaction t=%@ obj.key=%@".fmt(t, obj.key));
			
			var id = (obj.key == undefined) ? that.uuid() : obj.key;
			delete(obj.key);
			console.log("SQL: INSERT INTO %@ (id, value,timestamp) VALUES (%@,%@,%@)".fmt(that.table, id, that.serialize(obj), that.now()));
			t.executeSql(
				"INSERT INTO " + that.table + " (id, value,timestamp) VALUES (?,?,?)",
				[id, that.serialize(obj), that.now()],
				function() {
					console.log("executeSQL INSERT success on %@ calling callback %@".fmt(that.table, callback));
					if (callback != undefined) {
						obj.key = id;
						that.terseToVerboseCallback(callback)(obj);
					}
				},
				that.onError);
			},
			that.onError,
			function() { console.log('INSERT: tx succeeded on table %@'.fmt(that.table));}
		);
	},
	save:function(obj, callback) {
		console.log("Lawnchair.save  obj.key=%@ obj.record=".fmt(obj.key, JSON.stringify(obj.record)));
		
		var that = this;
	

		if (obj.key == undefined) {
			this.insert(obj, callback);
		} else {
			console.log('Will call get to find out if we need to INSERT or UPDATE');
			this.get(obj.key, function(r) {
				console.log('SELECT returned r=%@'.fmt(r));
				
				var isUpdate = (r != null);
	
				if (isUpdate) {
					var id = obj.key;
					delete(obj.key);
					that.update(id, obj, callback);
				} else {
					console.log('will INSERT obj.key=%@ obj.record=%@'.fmt(obj.key, JSON.stringify(obj.record)));
					that.insert(obj, callback);
				}
			});
		}
	},
	get:function(key, callback) {
		var that = this;
		this.db.transaction(function(t) {
			console.log("SQL: SELECT value FROM %@ WHERE id = %@".fmt(that.table, key));
			t.executeSql(
				"SELECT value FROM " + that.table + " WHERE id = ?",
				[key],
				function(tx, results) {
					if (results.rows.length == 0) {
						that.terseToVerboseCallback(callback)(null);
					} else {
						var o = that.deserialize(results.rows.item(0).value);
						o.key = key;
						that.terseToVerboseCallback(callback)(o);
					}
				},
				this.onError);
		},
		this.onError,
		function() { console.log('SELECT: tx succeeded on table %@ where key=%@'.fmt(that.table, key));}
		);
	},
	all:function(callback) {
		var cb = this.terseToVerboseCallback(callback);
		var that = this;
		this.db.transaction(function(t) {
			console.log("SQL: SELECT value FROM %@".fmt(that.table));
			t.executeSql("SELECT * FROM " + that.table, [], function(tx, results) {
				if (results.rows.length == 0 ) {
					cb([]);
				} else {
					var r = [];
					for (var i = 0, l = results.rows.length; i < l; i++) {
						var raw = results.rows.item(i).value;
						var obj = that.deserialize(raw);
						obj.key = results.rows.item(i).id;
						r.push(obj);
					}
					cb(r);
				}
			},
			that.onError);
		});
	},
	paged:function(page, callback) {
		var cb = this.terseToVerboseCallback(callback);
		var that = this;
		this.db.transaction(function(t) {
		    var offset = that.perPage * (page - 1); // a little offset math magic so users don't have to be 0-based
		    var sql = "SELECT * FROM " + that.table + " ORDER BY timestamp ASC LIMIT ? OFFSET ?";
			t.executeSql(sql, [that.perPage, offset], function(tx, results) {
				if (results.rows.length == 0 ) {
					cb([]);
				} else {
					var r = [];
					for (var i = 0, l = results.rows.length; i < l; i++) {
						var raw = results.rows.item(i).value;
						var obj = that.deserialize(raw);
						obj.key = results.rows.item(i).id;
						r.push(obj);
					}
					cb(r);
				}
			},
			that.onError);
		});
	},
	remove:function(keyOrObj, callback) {
		var that = this;
        if (callback)
            callback = that.terseToVerboseCallback(callback);
		this.db.transaction(function(t) {
			t.executeSql(
				"DELETE FROM " + that.table + " WHERE id = ?",
				[(typeof keyOrObj == 'string') ? keyOrObj : keyOrObj.key],
				callback || that.onData,
				that.onError
			);
		});
	},
	nuke:function(callback) {
		var that = this;
        if (callback)
            callback = that.terseToVerboseCallback(callback);
		this.db.transaction(function(tx) {
			tx.executeSql(
				"DELETE FROM " + that.table,
				[],
				callback || that.onData,
				that.onError
			);
		});
	}
};
