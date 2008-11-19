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
		Log			= YAHOO.log,	
        Dom         = YAHOO.util.Dom,
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
	 * 
	 * @param {Object} el
	 * @param {Object} json
	 */
	Page.createPages = function( el, json ) {
		var processingContext = new JsEvalContext(json);
		var template = jstGetTemplate('pages.template');
		var container = Dom.get(el);
		
		container.appendChild(template);
		jstProcess(processingContext, template);

		for (var i = 0; i < json.pages.length; i++) {
			var p = new Page(container, {showDocument: true, showFullPage: false, pageId : json.pages[i].id});
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
		ID_PAGE_TEMPLATE : 'page.template',
		ID_FULL_PAGE_TEMPLATE : 'full.page.template',
		ID_DOCUMENT_CAROUSEL_TEMPLATE : 'carousel.template',
		ID_SUFFIX_THUMBNAIL : 'page-item-thumbnail',
		ID_SUFFIX_PAGE_ITEM_FRAGMENT : 'page-item-fragment',
		ID_SUFFIX_FRAGMENT_IMAGE : 'page-item-fragment/img/',
		ID_SUFFIX_CAROUSEL_PANEL : 'page-item-document-carousel',			
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
		
        /**
         * The original Y position of the fragment element
         *
         * @property _pageFragmentOriginalY
         * @private
         */
		_pageFragmentOriginalY : null,
		
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
			//TODO this._createSearchOverlays(pageJson);
			
			if (this._config.showDocument) {
				Connect.asyncRequest('GET', pageJson.document, {
					scope: this,
					faulure: this._processApiFailure,
					success: this._processGetDocument
				});
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
		 * Creates overnaly objects to display search hits
		 * @param {Object} pageJson - json from search API
		 */
		_createSearchOverlays: function(pageJson) {
			var idThumbnail = pageJson.url + Page.CONFIG.ID_SUFFIX_PAGE_ITEM_FRAGMENT;
			var thbRegion = Dom.getRegion(idThumbnail);
			var thbWidth = thbRegion.right - thbRegion.left;
			var thbHeight = thbRegion.bottom - thbRegion.top;
			var widthRatio = thbWidth/parseInt(pageJson.width);
			var heigthRatio = thbHeight/parseInt(pageJson.height);

			var thbX = Dom.getX(idThumbnail);
			var thbY = Dom.getY(idThumbnail);
			for (var j = 0; j < pageJson.hits.length; j++) {
				var x1 = Math.floor(thbX + parseInt(pageJson.hits[j].x1)*widthRatio);
				var y1 = Math.floor(thbY + parseInt(pageJson.hits[j].y1)*heigthRatio);
				var x2 = Math.floor(thbX + parseInt(pageJson.hits[j].x2)*widthRatio);
				var y2 = Math.floor(thbY + parseInt(pageJson.hits[j].y2)*heigthRatio);
				
				var hitId = pageJson.url + 'hit/' + x1 + ':' + y1 + ':' + x2 + ':' + y2;
				var o = new YAHOO.widget.Overlay(hitId, {
					x: x1,
					y: y1,
					visible: false,
					width: (x2-x1)+'px',
					height: (y2-y1)+'px'
				});
				o.render(idThumbnail);
				o.show();
			}	
		},
		
		_initEvents: function() {
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
			var responseJSON = eval('(' + response.responseText + ')');
			var processingContext = new JsEvalContext(responseJSON);
			var template = null;
			if (this._config.showFullPage) {
				template = jstGetTemplate(Page.CONFIG.ID_FULL_PAGE_TEMPLATE);
			}
			else {
				template = jstGetTemplate(Page.CONFIG.ID_PAGE_TEMPLATE);
			}
				
			var panel = Dom.get(Page.CONFIG.ID_PANEL);
			
			panel.appendChild(template);
			jstProcess(processingContext, template);
			
			if (this._config.showDocument) {
				Connect.asyncRequest('GET', responseJSON.page.document, {
					scope: this,
					faulure: this._processApiFailure,
					success: this._processGetDocument
				});
			}
		},

		
		/**
		 * 
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
		},
		
		/**
		 * 
		 * @param {Object} pos : Position of the mouse
		 * @protected
		 */
		_mousemoveEventHandler: function(pos, page) {
			var th = Dom.get(page._pageId + Page.CONFIG.ID_SUFFIX_THUMBNAIL);
			var offsetPercent = (Dom.getXY(th.id)[1] - pos.clientY) / th.clientHeight;
			var fragment = Dom.get(page._pageId + Page.CONFIG.ID_SUFFIX_FRAGMENT_IMAGE);
			
			if (page._pageFragmentOriginalY === undefined) {
				page._pageFragmentOriginalY = Dom.getY(fragment.id);
			};
			Dom.setY(fragment.id, page._pageFragmentOriginalY + fragment.clientHeight * offsetPercent);
		}

    });

})();

YAHOO.register("page", YAHOO.donomo.Page, {version: "1.0", build: "$Rev:$"});
	