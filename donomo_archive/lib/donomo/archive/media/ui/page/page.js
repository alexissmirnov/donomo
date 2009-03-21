/*
Copyright (c) 2008, Donomo Inc. All rights reserved.
*/
YAHOO.namespace("donomo");

//TODO: move to utils
String.prototype.format = function() {
	var pattern = /\{\d+\}/g;
	var args = arguments;
	return this.replace(pattern, function(capture){ return args[capture.match(/\d+/)]; });
};

/**
 * The Page module provides a widget for interacting with a single page
 *
 * @module page
 * @requires yahoo, dom, event, element
 * @optional animation
 * @namespace YAHOO.donomo
 * @title Page Donomo Widget
 */
(function () {
    var WidgetName;             // forward declaration

    /**
     * The Page widget.
     *
     * @class Page
     * @extends YAHOO.util.Element
     * @constructor
     * @param el {HTMLElement | String} The HTML element that represents the
     * the container that houses the Page.
     * @param cfg {Object} (optional) The configuration values
     */
    YAHOO.donomo.Page = function (el, cfg) {
		YAHOO.log("Component creation", "info", WidgetName);

		/*
		 * Instance specific variable initializers
		 * this._something 
		 */

        YAHOO.donomo.Page.superclass.constructor.call(this, el, cfg);
    };

    /*
     * Private variables of the Carousel component
     */

    /* Some abbreviations to avoid lengthy typing and lookups. */
    var Page    = YAHOO.donomo.Page,
        Dom         = YAHOO.util.Dom,
		Element     = YAHOO.util.Element,
        Event       = YAHOO.util.Event,
		Connect		= YAHOO.util.Connect,
        JS          = YAHOO.lang;

    /**
     * The widget name.
     * @private
     * @static
     */
    WidgetName = "Page";
	
    /**
     * The internal table of Carousel instances.
     * @private
     * @static
     */
    var instances = {};

    /*
     * Custom events of the Page component
     */

    /**
     * @event beforeHide
     * @description Fires before the Page is hidden.  See
     * <a href="YAHOO.util.Element.html#addListener">Element.addListener</a>
     * for more information on listening for this event.
     * @type YAHOO.util.CustomEvent
     */
    var beforeHideEvent = "beforeHide";

    /**
     * @event beforeShow
     * @description Fires when the Page is about to be shown. The operation will
     * be aborted in case the even handler returns false.  See
     * <a href="YAHOO.util.Element.html#addListener">Element.addListener</a>
     * for more information on listening for this event.
     * @type YAHOO.util.CustomEvent
     */
    var beforeShowEvent = "beforeShow";

    /**
     * @event hide
     * @description Fires when the Page is hidden.  See
     * <a href="YAHOO.util.Element.html#addListener">Element.addListener</a>
     * for more information on listening for this event.
     * @type YAHOO.util.CustomEvent
     */
    var hideEvent = "hide";

    /**
     * @event show
     * @description Fires when the Page is shown.  See
     * <a href="YAHOO.util.Element.html#addListener">Element.addListener</a>
     * for more information on listening for this event.
     * @type YAHOO.util.CustomEvent
     */
    var showEvent = "show";

    /*
     * Private static private (helpers) functions used by the Page component
     */
	
    /*
     * Static public members and methods of the Page component
     */

    /**
     * Return the appropriate Page object based on the id associated with
     * the Page element or false if none match.
     * @method getById
     * @public
     * @static
     */
    Page.getById = function (id) {
        return instances[id] ? instances[id] : false;
    };
	
	/**
	 * Creates page nstances based on a given JSON. The instances of Page class
	 * will be created around exisging DOM objects.
	 * @param {Object} el
	 * @param {Object} json
	 */
	Page.createPages = function( el, json ) {
		var processingContext = new JsEvalContext(json);
		var showFullPage = false;
		
		var template;
		if (showFullPage) {
			template = jstGetTemplate(Page.CONFIG.ID_PAGES_FULL_TEMPLATE);
		}
		else {
			template = jstGetTemplate(Page.CONFIG.ID_PAGES_FRAGMENT_TEMPLATE);
		}
		var container = Dom.get(el);
		
		container.appendChild(template);
		jstProcess(processingContext, template);

		for (var i = 0; i < json.pages.length; i++) {
			var p = new Page(container, {showDocument: true, showFullPage: showFullPage, pageId : json.pages[i].id});
			p.insert(json.pages[i]);
		}
	}
	
    /*
     * CSS classes used by the Page component
     */

    Page.CLASSES = {
        /**
         * The class name of the thumbnail element.
         *
         * @property THUMBNAIL
         * @default "page-item-thumbnail"
         */
        THUMBNAIL: "page-item-thumbnail",
		
        /**
         * The class name of a visible Page.
         *
         * @property VISIBLE
         * @default "donomo-page-visible"
         */
        VISIBLE: "donomo-page-visible"
	};
    /*
     * Configuration attributes for configuring the Page component
     */

    Page.CONFIG = {

        /**
         * API to get a given page. Expects page id as paramater
         *
         * @property API_GET_PAGE
         * @default '/api/1.0/pages/{0}/'
         */
        API_GET_PAGE: '/api/1.0/pages/{0}/',
		API_GET_DOCUMENT : '/api/1.0/documents/{0}/',
		ID_PANEL : 'page-panel',
		
		ID_PAGES_FULL_TEMPLATE : 'pages.full.template',
		ID_PAGES_FRAGMENT_TEMPLATE : 'pages.fragment.template',
		ID_PAGE_FULL_TEMPLATE : 'page.full.template',
		ID_PAGE_FRAGMENT_TEMPLATE : 'page.fragment.template',
		ID_DOCUMENT_CAROUSEL_TEMPLATE : 'carousel.template',
		
		ID_SUFFIX_THUMBNAIL : 'page-item-thumbnail',
		ID_SUFFIX_PAGE_ITEM_FRAGMENT : 'page-item-fragment',
		ID_SUFFIX_FRAGMENT_IMAGE : 'page-item-fragment/img/',
		ID_SUFFIX_CAROUSEL_PANEL : 'page-item-document-carousel',
		ID_SUFFIX_PAGE_ITEM_STATUS : 'page-item-status',	
	};
    /*
     * Internationalizable strings in the Page component
     */

    Page.STRINGS = {
	};
	
	YAHOO.extend(Page, YAHOO.util.Element, {
        /*
         * Internal variables used within the Page component
         */
				
		_config : null, // TODO: figure out how to use this.get('param')
		_pageId : null, // full URL id
		
        /*
         * Public methods of the Page component
         */
		
		setPageId: function(pageId) {
			this._pageId = pageId;
		},
		/**
		 * Init is called indirectly by the ctor by the superclass (Element)
		 * @param {Object} el
		 * @param {Object} attrs
		 */
		init: function (el, attrs) {
            var elId  = el;

			this._config = attrs;
			this._pageId = Page.CONFIG.API_GET_PAGE.format(attrs.pageId);
			
            if (!el) {
                YAHOO.log(el + " is neither an HTML element, nor a string",
                        "error", WidgetName);
                return;
            }

            YAHOO.log("Component initialization", "info", WidgetName);

            if (JS.isString(el)) {
                el = Dom.get(el);
            } else if (!el.nodeName) {
                YAHOO.log(el + " is neither an HTML element, nor a string",
                        "error", WidgetName);
                return;
            }

            if (el) {
                if (!el.id) {   // in case the HTML element is passed
                    el.setAttribute("id", Dom.generateId());
                }
                //this._createPage(el);
            }
            elId = el.id;

            Page.superclass.init.call(this, el, attrs);

            this._initEvents();

            instances[attrs.pageId] = this;
		},
		
		load: function() {
			Connect.asyncRequest(
				'GET',
				this._pageId,
				{ scope: this, faulure: this._processApiFailure, success: this._processGetPage }
			);
		},
		
		insert: function(pageJson) {
			/*
			 * If we're showing the document carousel, we have to defer the insertion
			 * of search overlays until after the document was processed.
			 * The reason is because the documetnt carousel, when created, will alter the
			 * height of the DOM node representing the page item. As a result, the subsequent 
			 * nodes will be offset further.
			 * If the overlays are added before the carousel is fully created, they will appear
			 * out of sync with the page layout. 
			 */
			if (this._config.showDocument) {
				var request = Connect.asyncRequest('GET', pageJson.document, {
					scope: this,
					argument: pageJson,
					faulure: this._processApiFailure,
					success: this._processGetDocument,
					customevents: {
						onComplete: 
							function (eventType, args) {
								this._createSearchOverlays(args[1]);
							},
					}
				});
			}
			else {
				this._createSearchOverlays(pageJson);
			}
		},
		

        /**
         * Display the Page.
         *
         * @method show
         * @public
         */
        show: function () {
            if (this.fireEvent(beforeShowEvent) !== false) {
                this.addClass(this.CLASSES.VISIBLE);
                this.fireEvent(showEvent);
            }
        },
		
        /**
         * Hide the Page.
         *
         * @method hide
         * @public
         */
        hide: function () {
            if (this.fireEvent(beforeHideEvent) !== false) {
                this.removeClass(this.CLASSES.VISIBLE);
                this.fireEvent(hideEvent);
            }
        },		

        /**
         * Return the string representation of the widget.
         *
         * @method toString
         * @public
         * @return {String}
         */
        toString: function () {
            return WidgetName + (this.get ? " (#" + this.get("id") + ")" : "");
        },
		
		/*
         * Protected methods of the Page component
         */

		/**
		 * Creates overlay objects to display search hits. The size and position
		 * of each overlay is mapped in proporsiton from the coordinates of the image
		 * used by OCR to the coordinates of the image being displayed
		 * @param {Object} pageJson - json from search API
		 */
		_createSearchOverlays: function(pageJson) {
			// get the element representing the page image
			var idPageImage = pageJson.url + Page.CONFIG.ID_SUFFIX_FRAGMENT_IMAGE;
			var elPageImage = new Element(Dom.get(idPageImage));

			// get image width and height
			var widthPageImage = elPageImage.get('scrollWidth');
			var heightPageImage = elPageImage.get('scrollHeight');
			
			// determine the ratio between the image used by OCR and
			// the displayed image
			var widthRatio = widthPageImage/parseInt(pageJson.width);
			var heigthRatio = heightPageImage/parseInt(pageJson.height);

			/**
			 * overlay objects use relative position
			 * (because i could not make absolutute positioned overlays show up on top of the image)
			 * each appended child overlay adds its height to elPageImage
			 * as a result i need to compansate for it, by making each subsequent overlay
			 * include that height.
			 * 
			 * I've also tried to re-get the height of the element because 
			 * we keep adding overlay elements to it in the loop like so
			 * heightPageImage = elPageImage.get('scrollHeight');
			 * but it worked only when the page image is shows in full mode, not in fragment
			 * 
			 * better solution is welcome
			 */  
			var heightCompensation = 0;
			
			// iterate across all search hits
			for (var j = 0; j < pageJson.hits.length; j++) {
				// map coordinates from OCR image to display image using the
				// image ratio
				var x1 = Math.floor(parseInt(pageJson.hits[j].x1)*widthRatio);
				var y1 = Math.floor(parseInt(pageJson.hits[j].y1)*heigthRatio);
				var x2 = Math.floor(parseInt(pageJson.hits[j].x2)*widthRatio);
				var y2 = Math.floor(parseInt(pageJson.hits[j].y2)*heigthRatio);
				
				// generate a unique id for the overlay based the coordinates and page url
				// eg. the id would look like "/api/1.0/pages/760/hit/86:476:241:491"
				var hitId = pageJson.url + 'hit/' + x1 + ':' + y1 + ':' + x2 + ':' + y2;

				// create an overlay div
				var o = document.createElement('div');
				o.id = hitId;
				
				// since the div is appended at the end of the image element
				// we use a negative Y coordinate to move it up to overlay the image
				// also add heightCompensation -- a total of heights of every overlay
				// element appended so far
				Dom.setStyle(o, 'top', -(heightPageImage-y1+heightCompensation) + 'px');
				Dom.setStyle(o, 'left', x1 + 'px');
				Dom.setStyle(o, 'width', (x2-x1)+'px');
				Dom.setStyle(o, 'height', (y2-y1)+'px');
				Dom.addClass(o, 'search-hit');

				// append the overlay
				elPageImage.appendChild(o);

				heightCompensation += (y2-y1);
			}	
		},
		
		_initEvents: function() {
			//TODO replace this by a more efficient option of
			// subscribing to bulled-up notifications
			Event.on(this._pageId + Page.CONFIG.ID_SUFFIX_THUMBNAIL, 
					'mousemove', 
					this._mousemoveEventHandler,
					this);
		},
		
	    /**
	     * Handles an error responce by an API
	     * @method _processApiFailure
	     * @param response {Object} HTTP response object
	     * @private
	     */
		_processApiFailure: function (response) { 
				YAHOO.log(response, "error", WidgetName); 
		},
		
		_processGetPage: function(response) {
			console.log(response.responseText)
			
			var responseJSON = eval('(' + response.responseText + ')');
			var processingContext = new JsEvalContext(responseJSON.page);
			var template = null;
			if (this._config.showFullPage) {
				template = jstGetTemplate(Page.CONFIG.ID_PAGE_FULL_TEMPLATE);
			}
			else {
				template = jstGetTemplate(Page.CONFIG.ID_FRAGMENT_TEMPLATE);
			}
				
			var panel = Dom.get(Page.CONFIG.ID_PANEL);
			
			panel.appendChild(template);
			jstProcess(processingContext, template);

			var panel = Dom.get(Page.CONFIG.ID_PANEL);
			
			if (this._config.showDocument) {
				Connect.asyncRequest('GET', responseJSON.page.document, {
					scope: this,
					faulure: this._processApiFailure,
					success: this._processGetDocument
				});
			}
		},

		
		/**
		 * Process the API response that returns a document.
		 * @param {Object} response
		 * @protected
		 */
		_processGetDocument: function(response) {
			var responseJSON = eval('(' + response.responseText + ')');
			var processingContext = new JsEvalContext(responseJSON);
			var template = jstGetTemplate(Page.CONFIG.ID_DOCUMENT_CAROUSEL_TEMPLATE);
			var panel = Dom.get(this._pageId + Page.CONFIG.ID_SUFFIX_CAROUSEL_PANEL);
			
			panel.appendChild(template);
			jstProcess(processingContext, template);

		    carousel = new YAHOO.widget.Carousel(panel.id, {
		        isCircular: false, // for a circular Carousel
		        revealAmount: 53,
				animation: { speed: 0.5 },
				numVisible: 9,
		        });
			carousel.render();
			carousel.show();
			
			// Now that we got the document, display its name in the 
			var status = Dom.get(this._pageId + Page.CONFIG.ID_SUFFIX_PAGE_ITEM_STATUS);
			status.innerHTML = responseJSON.document.title;
		},
		
		/**
		 * Handle mousemove over the thumbnail.
		 * The mousemove over the thumbnail controls the scrolling of the image and highlights
		 * of the image fragment.
		 * When the mouse is at the top of the thumbnail, the image is set with 0 scroll offset.
		 * When mouse is at the bottom of the thumbnail, the image is scrolled to the bottom
		 * with its bottom line flush with the bottom line of the thumbnail.
		 * @param {Object} pos : Position of the mouse
		 * @protected
		 */
		_mousemoveEventHandler: function(pos, page) {
			// Get the element of the thumbnail - this is where the mouse moves
			var th = Dom.get(page._pageId + Page.CONFIG.ID_SUFFIX_THUMBNAIL);
			
			// Get the element representing the image fragment
			var fragment = Dom.get(page._pageId + Page.CONFIG.ID_SUFFIX_FRAGMENT_IMAGE);

			// Get the element of fragmentContainer -- we need this to get its
			// clientHeight.			
			var fragmentContainer = Dom.get(page._pageId + Page.CONFIG.ID_SUFFIX_PAGE_ITEM_FRAGMENT);
			
			// Calculate the persent of the distance between top edge of the
			// thumbnail and the current mouse position
			var offsetPercent = (Dom.getY(th.id) - pos.clientY) / th.clientHeight;

			// Calculate the entre height of the scrollable area.
			// This is the value by which the image will be scrolled when the mouse reaches
			// the bottom of the thumbnail.
			var scollableHeight = fragment.scrollHeight-fragmentContainer.clientHeight;

			// Finnaly, scroll the fragment to the determined persent
			fragment.scrollTop = -(scollableHeight * offsetPercent);
		}
    });
})();

YAHOO.register("page", YAHOO.donomo.Page, {version: "1.0", build: "$Rev:$"});
	