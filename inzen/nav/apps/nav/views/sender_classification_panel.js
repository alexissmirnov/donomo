Nav.SenderClassificationPanel = SC.PanelPane.extend(SC.Animatable, {
	  modalPane: SC.ModalPane.extend(SC.Animatable, {
	    classNames: 'for-sc-panel',
	    transitions: {
	      opacity: 0.25
	    },
	    style: {opacity: 0.0 }
	  }),
	  
	  transitions: {
	    transform: {
	      duration: 0.5,
	      timing: SC.Animatable.TRANSITION_EASE_IN_OUT
	    },
	    opacity: {
	      duration: 0.5,
	      timing: SC.Animatable.TRANSITION_EASE_IN_OUT,
	      action: function(){
	        if (this.style.opacity === 0) this._call_when_done();
	      }
	    }
	  },
	  style: { opacity: 0.0, transform: "scale3d(.1,.1,1)" },
	  layout: { width: 250, height: 480 },
	  theme: "popover",
	  
	  append: function() {
	    sc_super();
	    this.invokeLater("sizeUp", 1);
	  },
	  
	  sizeUp: function() {
	    this.adjust({
	      opacity: 1,
	      transform: "scale3d(1,1,1)"
	    });
	    this.modalPane.adjust("opacity", 0.50);
	  },
	  
	  remove: function() {
	    this._call_when_done = arguments.callee.base;
	    this.adjust({
	      opacity: 0,
	      transform: "scale3d(.1,.1,1)"
	    });
	    this.modalPane.adjust("opacity", 0);
	  },
	  
	  classNames: "contact-classification-panel".w(),

	  defaultResponder: Nav,
	  layout: { top: 0, bottom: 0, width: 768, centerX: 0 },
	  contentView: null,
	  theme: "iphone",
	  
	  generateWithView: function (view) {
		  return Nav.SenderClassificationPanel.create({
			  contentView: SC.View.design({
				  childViews: "form".w(),
				  nowShowingBinding: "Nav.senderClassificationController.nowShowing",
				  nowShowing: "none",
				  form: SC.WorkspaceView.design(SC.Animatable, {
					  classNames: "flippable".w(),
				      transitions: {
					  	"transform": {
				        "duration": 0.5, timing: SC.Animatable.TRANSITION_EASE_IN_OUT
				        }
				      },
				      style: {
				        "rotateY": "0deg"
				      },
				      topToolbar: SC.ToolbarView.design({
				          layout: { top: 0, height: 44, left: 0, right: 0 },
				          childViews: "close source".w(), // not "closed" source-- close & source
				          close: SC.ButtonView.design({
				        	  layout: { left: 7, centerY: 0, height: 30, width: 100 },
				              title: "Close",
				              action: "closeDemo",
				              controlSize: SC.AUTO_CONTROL_SIZE,
				              isCancel: YES
				          }),
			              source: SC.ButtonView.design({
				              layout: { right: 7, centerY: 0, height: 30, width: 100 },
				              title: "Source",
				              action: "showSource",
				              controlSize: SC.AUTO_CONTROL_SIZE,
				              isDefault: YES
				          })
				      }),
				      contentView: view
				  })
			  })
		  });
	  }
});

