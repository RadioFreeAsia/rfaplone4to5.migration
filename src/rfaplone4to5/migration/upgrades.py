from plone import api

from zope.component import getGlobalSiteManager
from plone.app.contenttypes.interfaces import IFile
from rfa.kaltura2.kaltura_video import IKaltura_Video
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from plone.app.contenttypes.subscribers import set_title_description
from rfa.kaltura2.events.events import addVideo, modifyVideo
 
def run_pre_migration(context):
    """ Use this for any steps that need to be done before the migration

        Example for disabling a subscriber:
        
        for subscriber:
        <subscriber
            for="plone.app.contenttypes.interfaces.IDocument
               zope.lifecycleevent.interfaces.IObjectModifiedEvent"
            handler=".events.subscriber_name"
            />
        
        from zope.component import getGlobalSiteManager
        gsm = getGlobalSiteManager()
        gsm.unregisterHandler(
            subscriber_name, (IDocument, IObjectModifiedEvent))
    """


    #disable file subscirber so Audio Clip's can import - plone.app.contenttypes
    #  <subscriber
    #       for=".interfaces.IFile
    #       zope.lifecycleevent.interfaces.IObjectCreatedEvent"
    #       handler=".subscribers.set_title_description"
    #  />
    #
    # Disable Kaltura video add subscriber
    # <subscriber
    #       for="rfa.kaltura2.kaltura_video.IKaltura_Video
    #       zope.lifecycleevent.interfaces.IObjectAddedEvent"
    #       handler=".events.addVideo"
    # />
    #<subscriber
    #       for="rfa.kaltura2.kaltura_video.IKaltura_Video
    #       zope.lifecycleevent.interfaces.IObjectModifiedEvent"
    #       handler=".events.modifyVideo"
    #  />

    gsm = getGlobalSiteManager()
    gsm.unregisterHandler(set_title_description,(IFile, IObjectCreatedEvent))
    gsm.unregisterHandler(addVideo,(IKaltura_Video, IObjectAddedEvent))
    gsm.unregisterHandler(modifyVideo,(IKaltura_Video, IObjectModifiedEvent))
    
def run_migration(context):
    setup_tool = api.portal.get_tool('portal_setup')
    setup_tool.runAllImportStepsFromProfile(
        'profile-rfaplone4to5.migration.import:import_content')


def run_post_migration(context):
    """ Use this for any steps that need to be done after the migration
        To go with the pre_migration example,
        you can re-register a subscriber:
        gsm.registerHandler(subscriber_name, (IDocument, IObjectModifiedEvent)
    """
    gsm = getGlobalSiteManager()
    gsm.registerHandler(set_title_description,
                          (IFile, IObjectCreatedEvent))
    gsm.registerHandler(addVideo,(IKaltura_Video, IObjectAddedEvent))
    gsm.registerHandler(modifyVideo,(IKaltura_Video, IObjectModifiedEvent))