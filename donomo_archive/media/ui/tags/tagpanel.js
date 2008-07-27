if (YAHOO.donomo.TagPanel == undefined) { YAHOO.donomo.TagPanel = function(){
		var Event = YAHOO.util.Event;
		var Dom = YAHOO.util.Dom;
		
		var config = {
			urlTagList: '/tags/',
			idTagTemplate: 'tags.template',
			classTagItem: 'tag-item',
			panelId: 'tag.panel'
		};
		
		var eventTagSelected = new YAHOO.util.CustomEvent("tagSelected", this);
		
		var init = function(){
			// Assign event listeners to just the panel
			Event.on(config.panelId, 'click', onClick);
			Event.onContentReady(config.panelId, insertTagList);
		};
		
		var insertTagList = function(){
			YAHOO.util.Connect.asyncRequest('GET', config.urlTagList, {
				success: function(o){
					try {
						var processingContext = new JsEvalContext(eval('(' + o.responseText + ')'));
						var template = jstGetTemplate(config.idTagTemplate);
						var panel = new YAHOO.util.Element(config.panelId);
						var panelItems = panel.get('childNodes');
						while (panel.get('childNodes').length) {
							panel.removeChild(panel.get('childNodes')[0]);
						}
						panel.appendChild(template);
						jstProcess(processingContext, template);
					} 
					catch (e) {
						console.log(e);
					}
				},
				faulure: function(o){
					console.log('error: ' + o);
				}
			});
		};
		
		var onClick = function(e){
			// Capture the current target element
			var elTarget = Event.getTarget(e);
			while (elTarget.id != config.panelId) {
				if (Dom.hasClass(elTarget, config.classTagItem)) {
					// remove selected status from all tags
					var elTagItems = Dom.getElementsByClassName('tag-item', 'div', this);
					Dom.removeClass(elTagItems, 'tag-item-selected');
					
					// set this tag as selected
					Dom.addClass(elTarget, 'tag-item-selected');
					
					// TODO set browser history
					
					// now fire the event so that other panels can do their things
					eventTagSelected.fire(elTarget);				
					break;
				}
				else {
					elTarget = elTarget.parentNode;
				}
			}
		};
		
		
		return {
			init: init,
			eventTagSelected: eventTagSelected
		};
}();}