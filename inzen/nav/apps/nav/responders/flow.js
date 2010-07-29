require('responders/main');

/** @namespace

  Hanles sender classification commands
  
  @extends SC.Responder
*/
Nav.states.flow = SC.Responder.create({
	// when we become first responder, show classification panel
	didBecomeFirstResponder: function () {	
		console.log(this.get('resource'));
		console.log(this.get('content'));

		// show the page
		Nav.getPath('flowPage.mainPane').append();
	},

	willLoseFirstResponder: function () {
		// hide the page and reset the current conent
		this.set('content', null);
	    Nav.getPath('flowPage.mainPane').remove();
	}
});