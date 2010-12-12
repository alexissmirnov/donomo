App = Signup;
Signup.ServerDataSource = SC.DataSource.extend({
	createRecord : function(store, storeKey, params) {
		if (SC.kindOf(store.recordTypeFor(storeKey), Signup.Account)) {
			var that = this,
				runRequest = function(user) {
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
					.notify(that, '_didCreateAccount', store, storeKey, params )
					.send(store.readDataHash(storeKey));
				};
			App.User.objects().runGet({guid:"1"}, runRequest, runRequest);
		}
	},
	
	_didCreateAccount: function(response, store, storeKey, params) {
		console.log(''+response);
		if (SC.ok(response)) {
			//var parser = /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/;
		    //var url = parser.exec(response.header('Location'))[8];
			//store.dataSourceDidComplete(storeKey, null, url); // update ID
			
			App.User.objects().getOrCreate({guid : App.User.prototype.ID}, response.get('body'), 
				function(record, created){
					console.log('getOrCreate returned %@ Created? %@'.fmt(record, created));
				});
			this.downloadMessages();
			//this.invokeLater('downloadMessages', 5000);
		} else {
			console.log(response.rawRequest.responseText);
			store.dataSourceDidError(storeKey, response);
		}
	},
	
	downloadMessages: function() {
		Signup.store.createRecord(Signup.Message, {body: 'body body %@'.fmt(this.toString())});
		//this.invokeLater('downloadMessages', 5000);
	},
	
	retrieveRecord : function(store, storeKey, id, callback) {
		
	}
	
});