App = Nav;

App.state.READY = SC.Responder.create( {
	/**
	 * Called when Profile button is clicked
	 * @returns
	 */
	onProfile: function () {
		App.state.transitionTo(App.state.MANAGING_PROFILE);
	}
});