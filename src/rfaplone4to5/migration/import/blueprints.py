# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultKeys
from collective.transmogrifier.utils import Matcher
from collective.transmogrifier.utils import defaultMatcher
from Products.CMFPlone.utils import safe_unicode
from zope.interface import provider
from zope.interface import implementer
from plone.app.discussion.interfaces import IConversation
from zope.component import createObject
from plone.folder.interfaces import IExplicitOrdering


import logging


logger = logging.getLogger('Transmogrifier')


@implementer(ISection)
@provider(ISectionBlueprint)
class Skipper(object):
    """Skip Plonesite, subsites folder, and subsite
       They will (have been) already created
    """

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

    def __iter__(self):
        for item in self.previous:
            if item['_path'] in ("/rfa",
                                 "/rfa/subsites"):
                logger.info('[SKIPPING] %s', item['_path'])
                continue
            if item['_type'] == "Subsite":
                logger.info('[SKIPPING Subsite] %s', item['_path'])
                continue
            
            #skip talkback items
            if item['_type'] == 'Story' and \
               item['_id'] == 'talkback' and \
               item['_classname'] == "DiscussionItemContainer":
                logger.info('[SKIPPING talkback] %s', item['_path'])
                continue
            
            yield item
            
            
@implementer(ISection)
@provider(ISectionBlueprint)
class ContentTypeMapper(object):
    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

    def __iter__(self):
        type_maps = {'Section': 'section',
                     'Story': 'story',
                     'AudioClip': 'Audio Clip', 
                     }
        
        for item in self.previous:
            if type_maps.get(item['_type']):
                logger.info('[MAPPING] %s to %s', item['_type'], type_maps[item['_type']])
                item['_type'] = type_maps[item['_type']]
                
            yield item


@implementer(ISection)
@provider(ISectionBlueprint)
class SetFeaturedImage(object):
    """Make sure featured image is at top of folder
    """
    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        
        #Dict storing a image UID -> Story UID
        self.featured_images = {}
        
    def __iter__(self):
        for item in self.previous:
                
            if item["_type"] == "story":
                #store the featured image
                featured_image_uid = item.get('featured_image', None)
                if featured_image_uid is not None:
                    self.featured_images[featured_image_uid] = item['_uid']
                yield item; continue;
            
            if item["_type"] == "Image":
                #look for this image in the featured images dict
                story_uid = self.featured_images.get(item['_uid'], None)
                if story_uid is not None:
                    story = api.content.get(UID=story_uid)
                    #move this image to the top of the story container:
                    adapter = IExplicitOrdering(story)
                    adapter.moveObjectsToTop(item['_id'])
                    #delete from dict to save some memory
                    del self.featured_images[item['_uid']]
                    
                yield item; continue;
                
            yield item;
            


@implementer(ISection)
@provider(ISectionBlueprint)
class CommentConstructor(object):
    """Create a comment on a object
    """

    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.options = options
        self.context = transmogrifier.context
        self.typekey = '_type'
        self.pathkey = '_path'
        self.comment_map = {}

    def __iter__(self):
        for item in self.previous:
            if item['_type'] != 'Discussion Item': # not a comment
                yield item; continue
            path = item['_path']
            
            pathlist = path.split('/')
            pathlist.remove('talkback')
            path = '/'.join(pathlist)
            
            
            ob = self.context.unrestrictedTraverse(path.lstrip('/'), None)
            if ob is None:
                yield item; continue # object not found

            #COMMENTS NOT READY
            logger.info("Skipping comment")
            yield item
            #REMOVE WHEN READY

            # XXX make sure comment doesn't exist already?

            conversation = IConversation(ob)
            comment = createObject('plone.Comment')
            comment.text              = item['text']
            comment.author_name       = item['author_name']
            comment.author_email      = item['author_email']
            comment.creation_date     = DateTime(item['creation_date']).asdatetime()
            comment.modification_date = comment.creation_date
            in_reply_to = item.get('_in_reply_to', 0)
            if in_reply_to:
                comment.in_reply_to = self.comment_map[in_reply_to]

            id = conversation.addComment(comment)
            self.comment_map[item['_comment_id']] = id

               


            
@implementer(ISection)
@provider(ISectionBlueprint)
class Example(object):
    """An example blueprint.
    """

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

        if 'path-key' in options:
            pathkeys = options['path-key'].splitlines()
        else:
            pathkeys = defaultKeys(options['blueprint'], name, 'path')
        self.pathkey = Matcher(*pathkeys)

    def __iter__(self):
        for item in self.previous:
            pathkey = self.pathkey(*item.keys())[0]

            # if you need to get the object (after the constructor part)
            obj = self.context.unrestrictedTraverse(
                safe_unicode(item['_path'].lstrip('/')).encode('utf-8'),
                None,
            )
            if not obj:
                yield item
                continue

            # do things here

            logger.info('[processing path] %s', pathkey)

            # always end with yielding the item,
            # unless you don't want it imported, or want
            # to bail on the rest of the pipeline
            yield item
