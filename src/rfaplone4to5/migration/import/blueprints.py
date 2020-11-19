# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultKeys
from collective.transmogrifier.utils import Matcher, Condition
from collective.transmogrifier.utils import defaultMatcher
from Products.CMFPlone.utils import safe_unicode
from zope.interface import provider
from zope.interface import implementer
from plone.app.discussion.interfaces import IConversation
from zope.component import createObject
from plone.folder.interfaces import IExplicitOrdering
from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName

from zope.annotation.interfaces import IAnnotations
import logging


logger = logging.getLogger('Transmogrifier')


#subsites will be manually created on the destination, so they do not share UID's
#this is a map between UIDS old plone4 ->new plone5.
#Use when setting a UID reference that might reference the subsite.
SUBSITE_UID_MAP = { "b94ea5cb25534de16a27cf14ebc5146b": "8e4a64b88944430e8176ec0246c16791", #RFA English
                    "1139461407fb44dde199fa20b831bf2a": "0513ae1803244ea49d8386488c674792", #RFA Burmese
                    "861a0515d689434257b9f0987adc9a13": "612b18f8da1e49998f5c02a07b139f14", #RFA Cantonese
                    "3fa001f04d764cbd6801949fbf6f8c77": "00522c941ee648d888d9812de57c86d8", #RFA Khmer
                    "90554ae2948934c4d025a644690fa15d": "267ae7c7631545ad990f871b8e4829ca", #RFA Korean
                    "386c2bbbb5584fc30f8802d121bc5d39": "142595ab036e47fa90a69acbc3f3618f", #RFA Lao
                    "ed1b7dfe708544a0e92682fa4ff35ac7": "f2d512cd11b741c9b5799d2479ed2316", #RFA Mandarin
                    "6eddde38850fb0eca03032738196b79e": "2e682c8db7b242a397540ad18b12841e", #RFA Tibetan
                    "b11a23cb938d4a5d84d1c28e0ca4108a": "d768f385904e4248a7c62e43e167a015", #RFA Uyghur
                    "68df45895b53f4eac3dd8a4671b74f3a": "a9ef99005b4843468baf2403de5642e2", #RFA Vietnamese
                    "86204499-5db6-4538-b6f9-36b580b0e6ce": "016fb0a7e679410b8babc377fa672c94", #RFA About
                    "6f69153b-5016-4ff6-8264-5a6ad3243efe": "062f5af91d2a4b8b801d01bd046c3774", #Benar News English
                    "b19480ac-5916-4649-8d32-bbc70f2a0da9": "01123d0547a34f8ea11788abaf0a8fac", #Benar News Bengali
                    "baa5c449-0e00-4ceb-9a82-3973fd0e5c77": "61bcd2d70fb94fbebd47f552919694d3", #Benar News Indonesian
                    "494305b7-78bc-4868-b2fb-c648b25d41ba": "c74f2c7a723248ebba82568cc4c70fb6", #Benar News Malay
                    "2b573b1b-5a9c-432e-b64e-c2fb3f51a9a9": "3409f01121d94f0881282545a3006023", #Benar News Thai
                    
                }
                    
                    
                    


@implementer(ISection)
@provider(ISectionBlueprint)
class Skipper(object):
    """Skip Plonesite, subsites folder, and subsite
       They will (have been) already created
       ...
       Skip any paths that consistently give problems.
    """
    badpaths = ('/rfa/subsites/burmese/commentaries/cyclone_nargis_news',
                '/rfa/subsites/cantonese/5fb557307cfe7d1b',
                '/rfa/subsites/cantonese/6e2f592798a86ce2',
                '/rfa/subsites/cantonese/7fd28fd15e738a2a82f1',
                '/rfa/subsites/cantonese/commentaries/jctk-04082017090822.html/cp_container/filled_slots/body/2017-04-08.3369033073',
                '/rfa/subsites/cantonese/news/hk-arrest-10152015093314.html/cp_container/filled_slots/body/2015-10-16.3520230437',
                '/rfa/subsites/english/multimedia/MekongProject/banner/content/image1.jpg',
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
                '/rfa/subsites/mandarin/rfashipin-old/video/video-player-page/cp_container/filled_slots/first/2010-02-015186648535',
                '/rfa/subsites/mandarin/rfashipin-old/video/cp_container/filled_slots/first/2010-05-249830491285',
                '/rfa/subsites/mandarin/video/tpp-10082015163237.html',
                '/rfa/subsites/mandarin/yataibaodao/dalailama-10282010114739.html',
                '/rfa/subsites/uyghur/kopxilwaste/video/cp_container/filled_slots/second/2010-10-068989339183',
                '/rfa/subsites/uyghur/xewerler/medeniyet-tarix/istanbulda-noruz-2018-03232018191016.html/cp_container/filled_slots/body/2018-03-23.7543164676',
                '/rfa/subsites/vietnamese/in_depth/Two-professors-theorize-on-bin-laden-hideout-vlong-02212009132321.html',
                '/rfa/subsites/vietnamese/multimedia/video-import/bloggers-react-to-blogger-arrests-and-crackdown-08042010131848.html/DiemThi09302010-90.jpg',
                '/rfa/subsites/korean/news/k020907ne-yk.mp3-20070209.html',
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
            if item['_type'] in ('Story', 'PressRelease', 'Kaltura Video') and \
               item['_id'] == 'talkback' and \
               item['_classname'] == "DiscussionItemContainer":
                logger.info('[SKIPPING talkback] %s', item['_path'])
                continue
            
            if item['_type'] == 'Topic':
                path = item['_path']
                path = path.replace('/rfa/subsites', '')
                pathlist = path.split('/')
                parent_path = '/'.join(pathlist[:-1])
                parent_path = '/' + self.context.id + parent_path
                parent_obj = self.context.unrestrictedTraverse(parent_path,None)
                if hasattr(parent_obj, 'portal_type') \
                   and parent_obj.portal_type == "Collection":
                    logger.info(f'[SKIPPING Topic] {path} is Child of Collection {parent_path} and not allowed')
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
                 'JobPosting': 'job posting',
                 'VideoLink': "Video Link",
                 'PDF File': "File",
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
                    try:    
                        adapter = IExplicitOrdering(story)
                    except TypeError:
                        pass
                    else:
                        adapter.moveObjectsToTop(item['_id'])
                    finally:
                        #delete from dict to save some memory
                        del self.featured_images[item['_uid']]
                    
                yield item; continue;
                
            yield item;
            
            
@implementer(ISection)
@provider(ISectionBlueprint)
class CopyKeywords(object):
    """Take standard and extended keywords and add them together for 'subjects' field
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
            if item.get('_type') != 'story':
                yield item
                continue
            if item.get('_id') == "talkback":
                yield item
                continue
          
            keywords = item['standard_keywords'] + item['extended_keywords']

            while True:
                try:
                    keywords.remove('')
                except ValueError:
                    break;

            item['subject'] = keywords
            item['subjects'] = keywords
            
            yield item


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
                    yield item
                    continue
                for uid in value:
                    value = uid
                    #if old subsite uid, use new subsite uid - otherwise, do nothing to the value
                    value = SUBSITE_UID_MAP.get(value, value) 
                    if item["recurse"]:
                        value += "::-1"
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
            
            

from BTrees.LLBTree import LLSet

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
        self.wftool = getToolByName(self.context, 'portal_workflow')

    def __iter__(self):
        for item in self.previous:
            if item['_type'] != 'Discussion Item': # not a comment
                yield item; continue
            path = item['_path']
            
            pathlist = path.split('/')
            pathlist.remove('talkback')
            path = '/'.join(pathlist[:-1])
            
            
            ob = self.context.unrestrictedTraverse(path.lstrip('/'), None)
            if ob is None:
                yield item; continue # object not found

            logger.info("importing Comment on %s", ob)
            conversation = IConversation(ob)

            #check to see if comment already exists
            already_exists = False
            for comment in conversation.getComments():
                if comment.text == item['text']:
                    already_exists = True
                    continue
                
            if already_exists:
                logger.info('comment already exists, skipping')
                yield item; continue
            
            comment = createObject('plone.Comment')
            comment.text              = item['text']
            comment.author_name       = item.get('author_name') 
            comment.author_email      = item.get('author_email')
            comment.creation_date     = DateTime(item['creation_date']).asdatetime()
            comment.modification_date = comment.creation_date
            in_reply_to = item.get('_in_reply_to', 0)
            if in_reply_to:
                comment.in_reply_to = self.comment_map[in_reply_to]

            id = conversation.addComment(comment)
            self.comment_map[item['_id']] = id
            
            
            item_tmp = item
            workflowhistorykey = "_workflow_history"
            # get back datetime stamp and set the workflow history
            for workflow in item_tmp[workflowhistorykey]:
                for k, workflow2 in enumerate(item_tmp[workflowhistorykey][workflow]):  # noqa
                    if 'time' in item_tmp[workflowhistorykey][workflow][k]:
                        item_tmp[workflowhistorykey][workflow][k]['time'] = DateTime(  # noqa
                            item_tmp[workflowhistorykey][workflow][k]['time'])  # noqa
                                    
            #change workflow key/name from 'comment_worklfow' to 'comment_review_workflow'
            item_tmp[workflowhistorykey]['comment_review_workflow'] = \
                item_tmp[workflowhistorykey].pop('comment_workflow')
            comment.workflow_history.data = item_tmp[workflowhistorykey]
            
            # update security
            workflows = self.wftool.getWorkflowsFor(comment)
            if workflows:
                workflows[0].updateRoleMappingsFor(comment)

            yield item
            

@implementer(ISection)
@provider(ISectionBlueprint)
class VideoPathFix(object):
    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context

    def __iter__(self):
        
        for item in self.previous:
            path = item['_path']
            
            if item['_type'] != 'Kaltura Video':
                yield item
                continue
                     
            pathlist = path.split('/')
            parentpath = '/'.join(path[:-1])
            video_id = path[-1]
            subsite = path[0]
            
            parent = self.context.unrestrictedTraverse(
                safe_unicode(parentpath.lstrip('/')).encode('utf-8'),
                None,
            )
            if parent:
                #do nothing - video will import correctly without path change
                yield item
                continue
            
            parentpath = f"{subsite}/video-import"
            item['_path'] = f"{parentpath}/{video_id}"
            
            yield item
            
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
                
            elif item["_type"] in ("story", 'press release'):
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
class HubpageFixer(object):
    def __init__(self, transmogrifier, name, options, previous):
        self.transmogrifier = transmogrifier
        self.name = name
        self.options = options
        self.previous = previous
        self.context = transmogrifier.context
    
    def __iter__(self):
        for item in self.previous:
            
            if item["_type"] == "Audio Clip":
                if item.get("_datafield_file") is None:
                    yield item
                    continue
                    
                #Check datafield mimetype
                #Change item["_type"] to HTML File for text/html
                #Change to File for non audio types
                if item["_datafield_file"]["content_type"] == "text/html":
                    item["_type"] = "raw html"
                elif "audio/" not in item["_datafield_file"]["content_type"]:
                    item["_type"] = "File"
        
            yield item
            
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

@implementer(ISection)
@provider(ISectionBlueprint)
class TimezoneFixerSection(object):
    """
    Fixes UnknownTimeZoneError: (UnknownTimeZoneError('GMT+1',),
    by replacing the (unknown) GMT+x timezone with Etc/GMT+x
    """

    def __init__(self, transmogrifier, name, options, previous):
        keys = options.get('keys') or 'regexp:(.*[Dd]ate)$'
        self.keys = Matcher(*keys.splitlines())
        self.condition = Condition(options.get('condition', 'python:True'),
                                   transmogrifier, name, options)
        self.previous = previous

    def __iter__(self):
        for item in self.previous:
            if self.condition(item):
                for key in item.keys():
                    match = self.keys(key)[1]
                    if match:
                        try:
                            item[key] = item[key].replace(" GMT", " Etc/GMT")
                        except AttributeError:  #No attribute named 'replace' b/c it's not a string
                            pass

            yield item
