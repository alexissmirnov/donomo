///**
// * 
// * Publication view shows a single message in a 'conversation'
// * and allows message side-swiping and scrubbing a-la Flibdoard
// * 
// */
//Nav.PublicationContentView = SC.View.extend(SC.StaticLayout, {
//    useStaticLayout: YES,
//
//    childViews: [
//    SC.StaticContentView.design({
//        classNames: 'conversation-item--body'.w(),
//        layout: {
//            left: 140,
//            width: 550
//        },
//        contentBinding: '.parentView.content.body'
//    })
//    ]    
//});
//
//Nav.PublicationScrollPanel = SC.ScrollView.extend({
//    // make sure the view doesn't react to side-ways swipes
//    alwaysBounceHorizontal: NO,
//    contentView: Nav.PublicationContentView.design({})
//});
//
//
//Nav.PublicationPanel = SC.View.extend({
//    childViews: 'scroll close'.w(),
//    close: SC.ButtonView.design({
//        layout: {
//            top: 0,
//            right: 0,
//            height: 20,
//            width: 20
//        },
//        title: 'full screen',
//        action: 'showFlowsFullScreen',
//        target: Nav.states.flows
//    }),
//    scroll: Nav.PublicationScrollPanel.design({
//        layout: {
//            top: 10
//        },
//        contentBinding: '.parentView.content'
//    }),
//    scrubber: Nav.PublicationScrubberView.design({
//        contentBinding: '.parentView.content'
//    })
//});