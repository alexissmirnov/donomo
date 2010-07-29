// ==========================================================================
// Project:   Nav
// ==========================================================================
/*globals Signup */

/** @class

  Renders a table with contact information.  Since we need to render a bunch of 
  information about the content object, a simple custom view like this is 
  simpler than trying to layout a bunch of label views in the page design.
  
  Both approaches would work.  This approach is just easier.

  @extends SC.View
*/
Nav.SenderClassificationView = SC.View.extend(SC.Control,
/** @scope Signup.AccountInfoView.prototype */ {

  /**
    Here is the account info content.
  */
  content: null,
  classNames: "sender-classification-view", // added to class names for outer div
  
  /** called by SC.Control anytime a content property changes.  just render */
  contentPropertyDidChange: function() {
    this.displayDidChange();
  },
  
  render: function(context) {
    context = context.begin("table");
    
    var controller = Nav.senderClassificationController;
    
    var content = controller.objectAt(controller.get('senderSelectionIndex')); //this.get('content');
    "email name".w().forEach(function(key) {
      context.begin("tr")
        .begin("th").push("_%@:".fmt(key.titleize()).loc()).end()
        .begin("td")
          .push(content.get(key))
        .end()
      .end();
    }, this);
    context.end();
  }

});

