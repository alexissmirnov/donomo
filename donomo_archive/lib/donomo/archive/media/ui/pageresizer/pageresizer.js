YAHOO.namespace("donomo");
YAHOO.donomo.PageResizer = function() {
	var Event = YAHOO.util.Event,
    Dom   = YAHOO.util.Dom,
    lang  = YAHOO.lang,
	cookie = YAHOO.util.Cookie;
    
	var slider;
			        
	// The slider can move 0 pixels up
	var topConstraint = 0;
	// The slider can move 200 pixels down
	var bottomConstraint = 200;
	// Custom scale factor for converting the pixel offset into a real value
	var scaleFactor = 1.5;
	// The amount the slider moves when the value is changed with the arrow
	// keys
	var keyIncrement = 20;
	var tickSize = 20;
	var minimalImageWidth = 40; 
	var cookieName = "donomo.archive.panelItemWidth";
	var initialImageWidth = 130;
	
	function init(idBackground, idHandle, classPanelItem, classPage) {
		try {
		    slider = YAHOO.widget.Slider.getHorizSlider(
							idBackground, 
		                    idHandle, 
							topConstraint, 
							bottomConstraint,
							keyIncrement);
			
			initialValue = cookie.get(cookieName, Number);
			
			if ( initialValue == undefined )
				initialValue = initialImageWidth - minimalImageWidth;
			
			slider.setValue(initialValue, true, true, false);
		
		    slider.getRealValue = function() {
		        return Math.round(this.getValue() * scaleFactor);
		    };
		
		    slider.subscribe("change", function(offsetFromStart) {
				try {
			        // use the scale factor to convert the pixel offset into a real
			        // value
			        var actualValue = slider.getRealValue();
			
			        // Update the title attribute on the background.  This helps assistive
			        // technology to communicate the state change
			        Dom.get(idBackground).title = "Thumbnail size is " + actualValue + ". Move the slider to change it.";

					// find out the size					
					imageWidth = actualValue + minimalImageWidth;
					imageHeight = Math.round( 1.4375 * imageWidth )

					// change height of every panel item - separators, pages
					var eltPanelItems = Dom.getElementsByClassName(classPanelItem);
					Dom.setStyle(eltPanelItems, 'height', imageHeight + 'px');
					
					// now resize pages -- don't resize separators
					var eltPages = Dom.getElementsByClassName(classPage);
					Dom.setStyle(eltPages, 'width', imageWidth+'px');

					cookie.set(cookieName, this.getValue());
				} catch(e) {
					console.log(e);
				}
			});
		} catch(e) {console.log(e);}	
	}
	return {
		init : init
	}
}();
