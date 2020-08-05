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

from zope.annotation.interfaces import IAnnotations
import logging


logger = logging.getLogger('Transmogrifier')


@implementer(ISection)
@provider(ISectionBlueprint)
class Skipper(object):
    """Skip Plonesite, subsites folder, and subsite
       They will (have been) already created
       ...
       Skip any paths that consistently give problems.
    """
    badpaths = ('/rfa/subsites/english/multimedia/MekongProject/banner/content/image1.jpg',
                '/rfa/subsites/english/multimedia/MekongProject/banner/content/image2.jpg',
                '/rfa/subsites/english/multimedia/MekongProject/banner/content/image3.jpg',
                '/rfa/subsites/english/multimedia/MekongProject/banner/content/image4.jpg',
                '/rfa/subsites/english/multimedia/MekongProject/banner/content/image5.jpg',
                '/rfa/subsites/english/multimedia/MekongProject/banner/content/image6.jpg',
                '/rfa/subsites/english/multimedia/MekongProject/banner/content/image7.jpg',
                '/rfa/subsites/english/multimedia/MekongProject/banner/content/image8.jpg',
                '/rfa/subsites/english/Test-for-Minh-Ha/banner/content/images/image1.jpg',
                '/rfa/subsites/english/Test-for-Minh-Ha/banner/content/images/image2.jpg',
                '/rfa/subsites/english/Test-for-Minh-Ha/banner/content/images/image3.jpg',
                '/rfa/subsites/english/Test-for-Minh-Ha/banner/content/images/image4.jpg',
                '/rfa/subsites/english/Test-for-Minh-Ha/banner/content/images/image5.jpg',
                '/rfa/subsites/english/Test-for-Minh-Ha/banner/content/images/image6.jpg',
                '/rfa/subsites/english/Test-for-Minh-Ha/banner/content/images/image7.jpg',
                '/rfa/subsites/english/Test-for-Minh-Ha/banner/content/images/image8.jpg',
                '/rfa/subsites/english/news/myanmar/aung-san-suu-kyi/aung-san-suu-kyi',
    )


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
            
            if item['_path'] in self.badpaths:
                logger.info(f'[SKIPPING {item["_path"]}')
                continue
            
            yield item
            
            
@implementer(ISection)
@provider(ISectionBlueprint)
class ContentTypeMapper(object):
    type_maps = {'Section': 'section',
                 'Story': 'story',
                 'AudioClip': 'Audio Clip',
                 'Topic': 'Collection',
                 'PressRelease': 'press release',
                 'JobPosting': 'job posting'
                 }    

    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
        
        
    def __iter__(self):
        for item in self.previous:
            if self.type_maps.get(item['_type']):
                logger.info('[MAPPING] %s to %s', item['_type'], self.type_maps[item['_type']])
                item['_type'] = self.type_maps[item['_type']]
                
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
class CollectionConstructor(object):
    """ Create a criterion on a parent Collection """
    
    criterionTypes = ('ATBooleanCriterion',
                      'ATCurrentAuthorCriterion',
                      'ATDateCriteria',
                      'ATDateRangeCriterion',
                      'ATListCriterion',
                      'ATPathCriterion',
                      'ATPortalTypeCriterion',
                      'ATReferenceCriterion',
                      'ATRelativePathCriterion',
                      'ATSelectionCriterion',
                      'ATSimpleIntCriterion',
                      'ATSimpleStringCriterion',
                      'ATSortCriterion' )
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        self.options = options
        self.context = transmogrifier.context
        self.typekey = '_type'
        self.pathkey = '_path'
        
    def __iter__(self):
        for item in self.previous:
            query = None
            
            if item['_type'] not in self.criterionTypes:
                logger.warning(f'Not a known criterion Type {item["_type"]}')
                yield item
                continue
            
            #get the parent, which is a Collection
            path = item['_path']
            pathlist = path.split('/')
            path = '/'.join(pathlist[:-1])
            path = '/' + self.context.id + path
            
            newCollection = self.context.unrestrictedTraverse(path,None,)
            if not newCollection:
                logger.error("Couldn't find parent Collection")
                yield item
                continue

            if newCollection.portal_type != "Collection":
                logger.error(f"Parent object {path} not a Collection")
                yield item
                continue
            
            logger.info(f"Adding {item['_type']}")
            if item['_type'] == 'ATBooleanCriterion':
                logger.error("ATBooleanCriterion Not Implemented")
                raise NotImplementedError
                
            elif item['_type'] == 'ATCurrentAuthorCriterion':
                logger.error("ATCurrentAuthorCriterion Not Implemented")
                raise NotImplementedError
            
            elif item['_type'] == 'ATDateCriteria':
                field = item['field']
                value = item['value']
                operation = item.get('operation', '')
                
                dateRange = item.get('dateRange', '')
                if dateRange == '-':
                    value = -value
                    
                if operation == "within_day":
                    if value == 0:
                        operation = "plone.app.querystring.operation.date.today"
                        query = dict(i=field, o=operation, v=str(value))
                    else:
                        date = DateTime() + value
                        date_range = (date - value,
                                      date + value)
                        operation = "plone.app.querystring.operation.date.between"
                        
                        query = dict(i=field, o=operation, v=date_range)    


                elif operation == "more":
                    if value == 0:
                        operation = "plone.app.querystring.operation.date.afterToday"
                    elif value > 0:   
                        operation = "plone.app.querystring.operation.date.largerThanRelativeDate"
                    elif value < 0:
                        operation = "plone.app.querystring.operation.date.beforeRelativeDate"
                        
                    query = dict(i=field, o=operation, v=str(abs(value)))
                    
                elif operation == "less":
                    if value == 0:
                        operation = "plone.app.querystring.operation.date.beforeToday"
                    elif value > 0:
                        operation = "plone.app.querystring.operation.date.lessThanRelativeDate"
                    elif value < 0:
                        operation = "plone.app.querystring.operation.date.afterRelativeDate"
                
                    query = dict(i=field, o=operation, v=str(abs(value)))

                
            elif item['_type'] == 'ATDateRangeCriterion':
                operator_code = 'date.between'
                field = item['field']
                value = [ item['start'], item['end'] ]
                query = dict(i=field,
                             o='plone.app.querystring.operation.date.between',
                             v=value)
           
            elif item['_type'] == 'ATListCriterion':
                items = item["value"]
                operator = item["operator"]
                field = item["field"]
                
                if field == "review_state":
                    operation = "plone.app.querystring.operation.selection.any"
                else:
                    operation = "plone.app.querystring.operation.selection.{}".format(
                                  "any" if operator == "or" else "all")
                
                query = dict(i=field,
                             o=operation,
                             v=items,
                )
           
            elif item['_type'] == 'ATPathCriterion':
                value = item.get('value')
                if not value:
                    return
                for uid in value:
                    value = uid
                    if item["recurse"]:
                        value += "::1"
                    query = dict(
                        i="path",
                        o="plone.app.querystring.operation.string.absolutePath",
                        v=value,
                    )
                    
            elif item['_type'] == 'ATPortalTypeCriterion':
                values = [ContentTypeMapper.type_maps.get(v,v) for v in item['value']]
                query = dict(
                    i="portal_type",
                    o="plone.app.querystring.operation.selection.any",
                    v=values,
                )
            
            elif item['_type'] == 'ATReferenceCriterion':
                logger.error("ATReferenceCriterion Not Implemented")
                raise NotImplementedError
            
            elif item['_type'] == 'ATRelativePathCriterion':
                field = item["field"]
                recursive = item["recurse"]
                value = item["relativePath"]
            
                query= dict(i=field, o="plone.app.querystring.operation.string.relativePath",
                            v=value)
            
            elif item['_type'] == 'ATSelectionCriterion':
                field = item["field"]
                value = item["value"]
                operator = item["operator"]
        
                if field == "Subject":
                    if operator == "and":
                        operation = "plone.app.querystring.operation.selection.all"
                    else:
                        operation = "plone.app.querystring.operation.selection.any"
                else:
                    operation = "plone.app.querystring.operation.selection.any"
        
                query = dict(i=field, o=operation, v=value)
                
                
            elif item['_type'] == 'ATSimpleIntCriterion':
                logger.error("ATSimpleIntCriterion Not Implemented")
                raise NotImplementedError
            
            elif item['_type'] == 'ATSimpleStringCriterion':
                field = item["field"]
                value = item["value"]
                operation = "plone.app.querystring.operation.selection.any"

                query = dict(i=field, o=operation, v=[value])

            elif item['_type'] == 'ATSortCriterion':
                newCollection.sort_on = item['field']
                newCollection.sort_reversed = item['reversed']
                
            if query is not None:
                if newCollection.query is None or newCollection.query is '':
                    newCollection.query = list()
                if query in newCollection.query:
                    pass #allow multuple runs without duplication
                else:
                    newCollection.query.append(query)
                
            yield item
            
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
class AnnotateObject(object):
    """ Make any notes necessary on the newly constructed object """

    KEY_PREFIX = "rfaplone4to5.migration."
    
    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

    def __iter__(self):
        
        for item in self.previous:
            path = item['_path']
            logger.info('[annotating] %s', path)
            
            if item["_type"] == "CompositePack Element":
                self.annotate_embeded(item)
                
            elif item["_type"] == "story":
                self.annotate_story(item)
            
            # always end with yielding the item,
            yield item
    
    def annotate_embeded(self, item):
        #get the parent
        path = item['_path']
        pathlist = path.split('/cp_container')
        path = self.context.id + pathlist[0]

        parent_obj = self.context.unrestrictedTraverse(path)
        if not parent_obj:
            return
        
        annotations = IAnnotations(parent_obj)
        
        atrefs = item.get('_atrefs')
        if atrefs:
            viewlet = atrefs.get("viewlet")
            if viewlet is not None:    
                if any('kaltura_video_box' in s for s in viewlet): 
                    annotations[self.KEY_PREFIX+"cp_kaltura_video"] = (item["target"], item["viewlet"])
                if any('gallery' in s for s in viewlet):
                    annotations[self.KEY_PREFIX+"cp_slideshow"] = (item["target"], viewlet)
            
        
        
    def annotate_story(self, item):
        
        #Slideshow(field), 
        #Video (kaltura and link via cp) 
        #Featured Image
        #additional images
        
        path = item['_path']
        obj = self.context.unrestrictedTraverse(path.lstrip('/'))
        if not obj:
            return
        
        annotations = IAnnotations(obj)
        if item.get('featured_image'):
            annotations[self.KEY_PREFIX+"featured_image"] = item.get('featured_image')
        if item.get('audio_clip'):
            annotations[self.KEY_PREFIX+"audio_clip"] = item.get('audio_clip')
        if item.get('slideshow'):
            annotations[self.KEY_PREFIX+"slideshow"] = item.get('slideshow')
        if item.get('additional_images'):
            annotations[self.KEY_PREFIX+"additional_images"] = item.get('additional_images')
        if item.get('video_link'):
            annotations[self.KEY_PREFIX+"video_link"] = item.get('video_link')
            
      
            
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
