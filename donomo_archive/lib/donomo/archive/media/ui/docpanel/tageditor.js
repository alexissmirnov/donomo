YAHOO.namespace("donomo");
YAHOO.donomo.TagEditorDialog = function(){
	var Overlay = YAHOO.widget.Overlay;
	var Dialog = YAHOO.widget.Dialog;
	var ContainerEffect = YAHOO.widget.ContainerEffect;
	var Connect = YAHOO.util.Connect;
	
	var setTag = function(doc, tags) {
		console.log('submit ' + tags + ' with ' + doc.id);
		doc.attributes['donomo.tags'].value = tags;
		
		// This API is reall a PUT, but we don't want to risk
		// having a browser that doesn't support PUTs
		// so we make a POST request and overrride the HTTP method
		// by passing _method
		YAHOO.util.Connect.asyncRequest(
			'POST', 
			doc.id+'?_method=PUT',
			{ success : function(o) {
				console.log(o.responseText);
			  },
			  faulure : function(o) {
			  }
			},
			'tags='+tags);
		}
	
	var init = function(){
		// Define various event handlers for Dialog
		var handleSubmit = function(){
			var data = this.getData();
			this.hide();
			
			setTag(this.doc, data.tag);
		};
		var handleCancel = function(){
			this.cancel();
		};
		
		// Instantiate the Dialog
		YAHOO.donomo.dlgTagEditor = new Dialog("dlgTagEditor", {
			visible: false,
			close: false,
			modal : false,
			constraintoviewport: true,
			effect:{effect: ContainerEffect.FADE,duration:0.2},
			buttons: [{
				text: "Save",
				handler: handleSubmit,
				isDefault: true
			}, {
				text: "Cancel",
				handler: handleCancel
			}]
		});
		
		// Validate the entries in the form to require that both first and last name are entered
		YAHOO.donomo.dlgTagEditor.validate = function(){
			var data = this.getData();
			console.log('todo: validate ' + data.tag);
			//TODO: unify with handleSubmit
			// calling handleSubmit() has a wrong 'this' and causes an error this,getData is not a function
			this.hide();
			setTag(this.doc, data.tag);
		};
		
		// Render the Dialog
		YAHOO.donomo.dlgTagEditor.render();
	};
	
	var show = function(doc, eltAlignWith) {
		YAHOO.donomo.dlgTagEditor.cfg.setProperty('context',[eltAlignWith, 'tl', 'bl']);
		YAHOO.donomo.dlgTagEditor.doc = doc;
		
		var tags_string = '';
		if (doc.attributes['donomo.tags'].nodeValue) {
			tags_string = doc.attributes['donomo.tags'].value;
		}

		YAHOO.donomo.dlgTagEditor.form.elements[0].value = tags_string;
		YAHOO.donomo.dlgTagEditor.show();
	}
	
	var hide = function() {
		YAHOO.donomo.dlgTagEditor.hide();
	}
	
	return {
		init : init,
		show : show,
	}
}();
