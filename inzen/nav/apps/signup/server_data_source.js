Signup.ServerDataSource = SC.DataSource.extend({
	createRecord : function(store, storeKey, params) {
		if (SC.kindOf(store.recordTypeFor(storeKey), Signup.Account)) {
			// check to see if we already have a user object
			var user = store.find(Signup.User, '1');
			var id = store.idFor(storeKey);
			var url = '/api/1.0/accounts/'+id+'/';
			if( user ) {
				url = url + '?username=' + user.get('username');
			}
			SC.Request.putUrl(url)
			.header({
                'Accept': 'application/json'
            })
            .json()
			.notify(this, '_didCreateAccount', store, storeKey, params )
			.send(store.readDataHash(storeKey));
		}
	},
	
	_didCreateAccount: function(response, store, storeKey, params) {
		console.log(''+response);
		if (SC.ok(response)) {
			//var parser = /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/;
		    //var url = parser.exec(response.header('Location'))[8];
			//store.dataSourceDidComplete(storeKey, null, url); // update ID
			
			// create a User object if it doesn't yet exist
			if( !Signup.store.dataHashes[Signup.store.storeKeyFor(Signup.User, '1')] )
				store.createRecord(Signup.User, response.get('body'), '1');
			
			this.invokeLater('downloadMessages', 5000);
		} else {
			console.log(response.rawRequest.responseText);
			store.dataSourceDidError(storeKey, response);
		}
	},
	
	downloadMessages: function() {
		Signup.store.createRecord(Signup.Message, {body: 'body body %@'.fmt(this.toString())});
		this.invokeLater('downloadMessages', 5000);
	},
	
	retrieveRecord : function(store, storeKey, id, callback) {
		
	}
	
});