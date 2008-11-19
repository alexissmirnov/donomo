YAHOO.namespace("donomo");

if (YAHOO.donomo.SearchResultPanel == undefined) { YAHOO.donomo.SearchResultPanel = function(){
		var Event = YAHOO.util.Event;
		var Dom = YAHOO.util.Dom;
		var Element = YAHOO.util.Element;
		var Connect = YAHOO.util.Connect;
		
		var config = {
			urlGetSearch : '/api/1.0/search/?view_name=thumbnail&q={0}&start_index={1}&num_rows={2}',
			dynamicPaginationSize : 40,
			idPageTemplate : 'full.page.template',
			idPanel : 'page-panel',
 		};
		var lastDocumentLoadCount;
		
		var init = function(query) {
			Connect.asyncRequest('GET',
				config.urlGetSearch.format(query, 0, config.dynamicPaginationSize),
				{ faulure: processApiFailure, success: processGetSearch });
			
			//TODO subscribe to bubbled up mousemove event
			// Event.on(elementId + config.idSuffixThumbnail, 'mousemove', onThumbnailMouseMove);
			// might need to set 'background-position', '0% 0%' on mouseout, 
			// but i'm not crazy about the snapping effect
							
		};
		
		var processGetSearch = function(response) {
			var responseJSON = eval('(' + response.responseText + ')');
			
			YAHOO.donomo.Page.createPages(config.idPanel, responseJSON);
		};

		var processApiFailure = function(o) { 
			console.error(o); 
		};
		
		
	
		return {
			init: init
		};
}();}


