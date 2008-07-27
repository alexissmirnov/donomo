YAHOO.namespace("donomo");
YAHOO.donomo.SearchPanel = function(){
	var config = {};
	var Dom = YAHOO.util.Dom;
	var Event = YAHOO.util.Event;
	
	function onChangeSearchText(e){
		var searchQuery = Dom.get(config.idSearchBox).value;
		var url = location.href.split('#')[0];
		if (searchQuery.length > 0) {
			url = url + '#/search/' + Dom.get(config.idSearchBox).value + '/';
			location.replace(url);
			eventSearchStringChanged.fire(this);
		} else {
			location.replace(url);
			location.reload();
		}
	}
	init = function(idSearchForm, idResultPanel){
		config.idSearchBox = idSearchForm;
		Event.addListener(config.idSearchBox, 'change', onChangeSearchText);
	};
	
	var eventSearchStringChanged = new YAHOO.util.CustomEvent("eventSearchStringChanged", this);
	
	return {
		init : init,
		eventSearchStringChanged : eventSearchStringChanged,
	}
}();
