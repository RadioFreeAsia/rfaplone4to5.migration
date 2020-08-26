from plone import api
import transaction
import zExceptions

from zope.component import getGlobalSiteManager
from plone.app.contenttypes.interfaces import IFile
from rfa.kaltura2.kaltura_video import IKaltura_Video
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from plone.app.contenttypes.subscribers import set_title_description
from rfa.kaltura2.events.events import addVideo, modifyVideo

from bs4 import BeautifulSoup
from plone.uuid.interfaces import IUUID
from plone.app.textfield.value import RichTextValue

import logging

logger = logging.getLogger("Plone")

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
    
def add_resolveuid(context):
    
    story_brains = api.content.find(portal_type="story")
    count = 0
    for brain in story_brains:
        story = brain.getObject()

        # A broken text field contains an <img> tag with class="image-inline caption" \
        # and src attribute does not contain 'resolveuid'
        #example: <p><img src="200803-PH-covid-inside.jpg" class="image-inline captioned" /></p>
        if story.text is None:
            continue
        
        soup = BeautifulSoup(story.text.raw, "html.parser")
        images = soup.findAll('img', class_="image-inline")
        changed = False
        for image in images:
            if 'resolveuid' not in image['src']:
                #we found a broken one.
                #get uid of image:
                
                #handle image scale - ex: 'foo.jpeg/@@images/image/thumb'    
                image_split = image['src'].split('@@images')
                image_id = image_split[0]
                if len(image_split) > 1:
                    image_scale = image_split[1]
                else:
                    image_scale = None
                    
                    
                try:
                    image_object = context.unrestrictedTraverse('/'.join(story.getPhysicalPath()) + 
                                                                '/' + image_id)
                except zExceptions.NotFound:
                    logger.warn("couldn't find image " + '/'.join(story.getPhysicalPath()) + 
                                                                '/' + image_id)
                    continue
                    
                uuid = IUUID(image_object)
                #replace <img> src with 'resolveuid/{uuid}'
                if image_scale is not None:
                    image['src'] = f'resolveuid/{uuid}/@@images/{image_scale}'
                else:
                    image['src'] = f'resolveuid/{uuid}'
                changed = True
                
        if changed:
            count = count + 1
            new = RichTextValue(str(soup), story.text.mimeType, story.text.outputMimeType)
            story.text = new
            logger.info("fixed " + '/'.join(story.getPhysicalPath()))
        
        if count >= 100:
            transaction.commit()
            count = 0
            
    transaction.commit()
    logger.info("Done")