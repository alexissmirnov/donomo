YAHOO.namespace("donomo");

function onApiFailure(o) {
	console.log('api request failed : ' + o);
}

if (YAHOO.donomo.Panel == undefined) { YAHOO.donomo.Panel = function(){
		var Event = YAHOO.util.Event;
		var Dom = YAHOO.util.Dom;
		var Element = YAHOO.util.Element;
		
		var config = {
			panelId: 'panel', //TODO: remove built-in references to panel ID
			idTagEditor: 'tageditor',
			panelScrollContainerId: 'panel-scroll-container', // dynamic scrolling impl
			dynamicPaginationSize : 40, // how many documents to load in a single batch
		};
		
		var panel =  new YAHOO.util.Element(config.panelId);
		
		// This variable maintains the index used to load the next batch of
		// documents when the user scrolls to the end of the list
		var currentDocumentIndex = 0;
		
		// This variable maintains the number of documents returned by the
		// lastest request of the batch of documents. We know we hit the end
		// of the document list when this variable is 0.
		// The variable is set by renderDocumentJSON and is used by onScroll handler
		var lastDocumentLoadCount = -1;
		
		var eventPageSelected = new YAHOO.util.CustomEvent("pageSelected", this);
		var eventDocumentExpanded = new YAHOO.util.CustomEvent("documentExpanded", this);
		var eventDocumentCollapsed = new YAHOO.util.CustomEvent("documentCollapsed", this);
		var eventDocumentTagEditorOpen = new YAHOO.util.CustomEvent("documenttagEditorOpen", this);
		var eventViewFullPage = new YAHOO.util.CustomEvent("viewFullPage", this);
		var eventDocumentsLoaded = new YAHOO.util.CustomEvent("documentsLoaded", this);
		
		// Create the panel object
		var onMouseOver = function(e){
			// Capture the current target element
			var elTarget = Event.getTarget(e);
			// Step through this section of the DOM looking for a page-separator 
			// in the target's ancestory, stop at the panel container
			while (elTarget.id != config.panelId) {
				// If we're over a page-separator, turn it on and stop
				if (Dom.hasClass(elTarget, 'page-separator')) {
					Dom.addClass(elTarget, 'page-separator-over');
					break;
					// Keep looking one level up
				}
				else 
					if (Dom.hasClass(elTarget, 'doc-separator')) {
						Dom.addClass(elTarget, 'doc-separator-over');
						break;
					// Keep looking one level up
					}
					else {
						elTarget = elTarget.parentNode;
					}
			}
		};
		// Reset panel styles
		var onMouseOut = function(e){
			var sep = Dom.getElementsByClassName('page-separator', 'div', this);
			Dom.removeClass(sep, 'page-separator-over');
			
			sep = Dom.getElementsByClassName('doc-separator', 'div', this);
			Dom.removeClass(sep, 'doc-separator-over');
		};
		
		function getParentNodeOfClass(el, className){
			var parent = el.parentNode;
			while (parent) {
				if (Dom.hasClass(parent, className)) {
					return parent;
				}
				else {
					parent = parent.parentNode;
				}
			}
			return null;
		}
		
		function getParentNodeByAttribute(el, attributeName){
			var parent = el.parentNode;
			while (parent) {
				if (parent.attributes && parent.attributes[attributeName]) {
					return parent;
				}
				else {
					parent = parent.parentNode;
				}
			}
			return null;
		}
				
		var splitDocument = function(elSeparator){
			Dom.removeClass(elSeparator, 'page-separator-over');
			Dom.removeClass(elSeparator, 'page-separator');
			Dom.addClass(elSeparator, 'doc-separator');
			Dom.addClass(elSeparator, 'doc-separator-over');
		};
		
		var joinDocument = function(elSeparator){
			Dom.removeClass(elSeparator, 'doc-separator-over');
			Dom.removeClass(elSeparator, 'doc-separator');
			Dom.addClass(elSeparator, 'page-separator');
			Dom.addClass(elSeparator, 'page-separator-over');
		};
		
		var onClick = function(e){
			// Capture the current target element
			var elTarget = Event.getTarget(e);
			while (elTarget.id != config.panelId) {
			
				// If we're over a page-separator, split the document
				if (Dom.hasClass(elTarget, 'page-separator-over')) {
					splitDocument(elTarget);
					break;
					// If we're over document separator, join the document
				}
				else 
					if (Dom.hasClass(elTarget, 'doc-separator-over')) {
						joinDocument(elTarget.id);
						break;
					// If we got a click on a page, fire an event
					}
					else 
						if (Dom.hasClass(elTarget, 'page')) {
							var pageSeparators = Dom.getElementsByClassName('page-selected', 'div', this);
							Dom.removeClass(pageSeparators, 'page-selected');
							
							eventPageSelected.fire(elTarget);
							Dom.addClass(elTarget, "page-selected");
							break;
						}
						else 
							if (Dom.hasClass(elTarget, "doc-tag")) {
								eventDocumentTagEditorOpen.fire(getParentNodeByAttribute(elTarget, "donomo.tags"));
								break;
							}
							else 
								if (Dom.hasClass(elTarget, "doc-collapse")) {
									eventDocumentCollapsed.fire(getParentNodeOfClass(elTarget, "page"));
									break;
								}
								else 
									if (Dom.hasClass(elTarget, "view-full-page")) {
										eventViewFullPage.fire(getParentNodeOfClass(elTarget, "page"));
										break;
									}
									else 
										if (Dom.hasClass(elTarget, "doc-expand")) {
											eventDocumentExpanded.fire(getParentNodeOfClass(elTarget, "document"));
											break;
										// Keep looking one level up
										}
										else {
											elTarget = elTarget.parentNode;
										}
			}
		};

		var removeChildren = function(el) {
			while (el.get('childNodes').length) {
				el.removeChild(el.get('childNodes')[0]);
			}			
		}
		
		var loadSearchResults = function(query, startIndex){
			YAHOO.util.Connect.asyncRequest(
				'GET', 
				"/api/1.0/search/?view_name=thumbnail&q=" + query
				+ '&start_index='
				+ startIndex
				+ '&num_rows='
				+ config.dynamicPaginationSize, {
				success: renderSearchResultsJSON,
				faulure: onApiFailure
			});
		};
		
		var renderSearchResultsJSON = function(response) {
			try {
				var responseJSON = eval('(' + response.responseText + ')');
				lastDocumentLoadCount = responseJSON.pages.length;
				
				var processingContext = new JsEvalContext(responseJSON);
				var template = jstGetTemplate('searchresults.template');
				
				panel.appendChild(template);
				jstProcess(processingContext, template);
				
				//Add search hit overlays
				for(var i = 0; i < responseJSON.pages.length; i++) {
					var idThumbnail = responseJSON.pages[i].url + 'thb/'
					var thb = new Element(Dom.get(idThumbnail));
					var thbRegion = Dom.getRegion(idThumbnail);
					var thbWidth = thbRegion.right - thbRegion.left;
					var thbHeight = thbRegion.bottom - thbRegion.top;
					var widthRatio = thbWidth/parseInt(responseJSON.pages[i].width);
					var heigthRatio = thbHeight/parseInt(responseJSON.pages[i].height);

					for (var j = 0; j < responseJSON.pages[i].hits.length; j++) {
						var x1 = Math.floor(Dom.getX(idThumbnail) + parseInt(responseJSON.pages[i].hits[j].x1)*widthRatio);
						var y1 = Math.floor(Dom.getY(idThumbnail) + parseInt(responseJSON.pages[i].hits[j].y1)*heigthRatio);
						var x2 = Math.floor(Dom.getX(idThumbnail) + parseInt(responseJSON.pages[i].hits[j].x2)*widthRatio);
						var y2 = Math.floor(Dom.getY(idThumbnail) + parseInt(responseJSON.pages[i].hits[j].y2)*heigthRatio);
						
						var hitId = responseJSON.pages[i].url + 'hit/' + x1 + ':' + y1 + ':' + x2 + ':' + y2;
						var o = new YAHOO.widget.Overlay(hitId, {
							x: x1,
							y: y1,
							visible: false,
							width: (x2-x1)+'px',
							height: (y2-y1)+'px'
						});
						o.render(responseJSON.pages[i].url);
						
						console.log(Dom.getRegion(hitId));
						o.show();
					}
				}
			} 
			catch (e) {
				console.log('renderSearchResultsJSON throws:');
				console.log(e);
			}
			
		}
		
		var onSeachStringChanged = function(type, args){
			currentDocumentIndex = 0;
			removeChildren(panel);
			loadPanelContents(currentDocumentIndex);
		};
		
		var onTagSelected = function(type, args) {
			var tagName = args[0].getAttribute('name');
			removeChildren(panel);
			
			YAHOO.util.Connect.asyncRequest('GET', '/api/1.0/tags/' + tagName + '/?view_name=thumbnail',
			{ 	success : renderDocumentsJSON,
				faulure : onApiFailure
			});		
		};
		
		
		var loadPanelContents = function(startIndex) {
			if (lastDocumentLoadCount == 0) {
				return;
			}

			var postHashPathParts = location.hash.toString().split('/');
			
			if (postHashPathParts.length >= 3 && postHashPathParts[1] == 'search') {
				loadSearchResults(postHashPathParts[2], startIndex);
			}
			else {
				loadDocuments(startIndex);
			}

			// increase the document index to be used next time we load more documents
			currentDocumentIndex = startIndex + config.dynamicPaginationSize;
		};
		
		var loadDocuments = function(startIndex) {
			YAHOO.util.Connect.asyncRequest(
				'GET',
				'/api/1.0/documents/?view_name=thumbnail&start_index='
					+startIndex
					+'&num_rows='
					+config.dynamicPaginationSize,
				{ 	success : renderDocumentsJSON ,
					faulure : onApiFailure
				});
		}
		
		var renderDocumentsJSON = function(response) {
			var responseJson = eval('('+response.responseText+')');
			
			lastDocumentLoadCount = responseJson.documents.length;
			
			var processingContext = new JsEvalContext(responseJson);
			var template = jstGetTemplate('document.template');
			panel.appendChild(template);
			jstProcess(processingContext, template);
			eventDocumentsLoaded.fire(responseJson);
		};

		var onScroll = function(e) {
			// The algorithm is based on
			// http://www.developer.com/design/article.php/3681771
			var scrollContainerPanel = new YAHOO.util.Element(config.panelScrollContainerId);
			
			// get the current height of a panel item. Sinse thumbnails can be resized, the height
			// may be different every time onScroll is fired.
			// Assumption: panel-items are children of panel
			var panelItem = new YAHOO.util.Element(YAHOO.util.Dom.getFirstChild(config.panelId));
			var panelItemHeigth = panelItem.get('clientHeight');
			
			var intElemScrollWidthOuter = scrollContainerPanel.get('clientWidth');
			var intElemScrollHeightOuter = scrollContainerPanel.get('clientHeight');
			var intElemScrollHeightInner = scrollContainerPanel.get('scrollHeight');
			var intElemScrolled = scrollContainerPanel.get('scrollTop');
			var height = intElemScrollHeightInner - intElemScrollHeightOuter;
			
			// Make sure we always have enough doduments in the scroll buffer to fill up
			// twice the item heigth. This means we'll be loading new data when the user
			// scrolls to the second last line.
			// If the last attempt to load more documents returned 0, then don't try to 
			// load any more
			if (intElemScrolled >= height - 2*panelItemHeigth && lastDocumentLoadCount != 0) {
				
				// load documents
				loadPanelContents(currentDocumentIndex);
			}
		};		
		
		var init = function(){
			loadPanelContents(currentDocumentIndex);
			
			// Assign event listeners to just the panel
			Event.on(config.panelId, 'mouseover', onMouseOver);
			Event.on(config.panelId, 'mouseout', onMouseOut);
			Event.on(config.panelId, 'click', onClick);
			Event.on(config.panelScrollContainerId, 'scroll', onScroll);
			
			YAHOO.donomo.TagEditorDialog.init();
		};

		return {
			init: init,
			eventPageSelected: eventPageSelected,
			eventDocumentExpanded: eventDocumentExpanded,
			eventDocumentCollapsed: eventDocumentCollapsed,
			eventViewFullPage: eventViewFullPage,
			eventDocumentTagEditorOpen: eventDocumentTagEditorOpen,
			eventDocumentsLoaded: eventDocumentsLoaded,
			renderSearchResultsJSON: renderSearchResultsJSON,
			onSeachStringChanged: onSeachStringChanged,
			onTagSelected: onTagSelected
		};
}();}

function onTagEditorOpen( type, args ) {
	try {
		var doc = args[0];
		console.log(doc.id);
		YAHOO.donomo.TagEditorDialog.show(doc, doc.id);
	} catch(e) {
		console.log(e);
	}
}


function onPageSelected( type, args ) {
	console.log("event " + type + ' with args ' + args);
}



/*
 * This handler fires when the page is loaded. We handle two cases
 * frist is when the url has a serach term in its fragment. it may be set by the search panel
 * second is the mainstream case when a user navigates to the archive page after logging in
 */
YAHOO.util.Event.onContentReady("panel", function () {		
});
	
function onDocumentExpanded( type, args ) {
	var doc = args[0];
	var id = doc.id;
	YAHOO.util.Connect.asyncRequest('GET', doc.id + "?view_name=thumbnail",
	{ argument : doc,
	  success : function(o) {
		  	var doc = o.argument;
			jsonResponse = eval('('+o.responseText+')');
			var processingContext = new JsEvalContext(jsonResponse);
			processingContext.setVariable('title', jsonResponse.document.title);
			processingContext.setVariable('doc_id', doc.id);
			processingContext.setVariable('total_pages', jsonResponse.document.pages.length);
			processingContext.setVariable('search_result', false);
			processingContext.setVariable('tags_string', jsonResponse.document.tags_string);
			var template = jstGetTemplate('page.template');
			var panel = document.getElementById('panel');
			
			
			// replace a document node with a list of page nodes
			panel.insertBefore(template, doc.parentNode);
			// keep the parent node in the Dom so that we can show it when the document is collapsed
			YAHOO.util.Dom.addClass(doc.parentNode, "hidden-item");
			
			jstProcess(processingContext, template);
		},
		faulure : function(o) {
			console.log('failure');
		}
	});
}
function onDocumentCollapsed( type, args ) {
	var page = args[0];
	var id = page.id;
	var docid = page.attributes['donomo-doc-id'].value;
	var panel = document.getElementById('panel');
	var pages = YAHOO.util.Dom.getElementsByClassName('page', 'div', panel);
	for (var i = 0; i < pages.length; i++) {
		var attr = pages[i].getAttribute('donomo-doc-id');
		if (attr !== null && attr == docid) {
			// we're removing parentNode, not the page itself because the page
			// is wrapped into a 'panel-item'
			panel.removeChild(pages[i].parentNode);				
		}
	}
	
	// Now that we've removed all pages of the document, unhide the
	// banner page
	var doc = document.getElementById(docid);
	YAHOO.util.Dom.removeClass(doc.parentNode, "hidden-item");
}

function onViewFullPage( type, args ) {
	try {
		var page = args[0];
		var docid = page.getAttribute('donomo-doc-id');
		
		var panel = document.getElementById('panel');
		new YAHOO.util.Element(panel).setStyle('display', 'none');
		
		YAHOO.util.Connect.asyncRequest('GET', docid + '?view_name=image', {
				argument: page,
				success: function(o) {
					var page = o.argument;
					jsonResponse = eval('('+o.responseText+')');
					var processingContext = new JsEvalContext(jsonResponse);
					processingContext.setVariable('page_id', page.id);
					var template = jstGetTemplate('full-view-page.template');
					
					var parent = panel.parentNode;
					
					parent.insertBefore(template, panel);
					jstProcess(processingContext, template);
				},
				faulure : function(o) {
					console.log('failure');
				}
			});
	} catch (e) {
		console.log(e);
	}
}

YAHOO.donomo.Panel.eventPageSelected.subscribe(onPageSelected);
YAHOO.donomo.Panel.eventDocumentExpanded.subscribe(onDocumentExpanded);
YAHOO.donomo.Panel.eventDocumentCollapsed.subscribe(onDocumentCollapsed);
YAHOO.donomo.Panel.eventDocumentTagEditorOpen.subscribe(onTagEditorOpen);
YAHOO.donomo.Panel.eventViewFullPage.subscribe(onViewFullPage);

