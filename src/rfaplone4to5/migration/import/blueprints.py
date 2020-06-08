# -*- coding: utf-8 -*-
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.utils import defaultKeys
from collective.transmogrifier.utils import Matcher
from Products.CMFPlone.utils import safe_unicode
from zope.interface import provider
from zope.interface import implementer

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
        for item in self.previous:
            type_maps = {'Section': 'section',
                         'Story': 'story',
                         'AudioClip': 'Audio Clip', 
                         }
            if type_maps.get(item['_type']):
                logger.info('[MAPPING] %s to %s', item['_type'], type_maps[item['_type']])
                item['_type'] = type_maps[item['_type']]
                
            yield item
            
@implementer(ISection)
@provider(ISectionBlueprint)
class Debugger(object):
    """A Debugger Blueprint to stick in the pipeline somewhere
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
            if item['_path'] == '/rfa/subsites/lao/Multimedia/LaoGame-12302010114149.html/talkback/1374893596':
                import pdb; pdb.set_trace()
            
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
