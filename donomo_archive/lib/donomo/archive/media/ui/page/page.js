YAHOO.namespace("donomo");

if (YAHOO.donomo.Page == undefined) { YAHOO.donomo.Page = function(){
		var Event = YAHOO.util.Event;
		var Dom = YAHOO.util.Dom;
		var Element = YAHOO.util.Element;
		var Connect = YAHOO.util.Connect;
		var Panel = YAHOO.donomo.Panel;

		var init = function() {
			console.log('this is page init');
		}

		return {
			init: init
		};
}();}
