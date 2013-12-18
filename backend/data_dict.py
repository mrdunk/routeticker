from google.appengine.ext import ndb    # For converting keys.
from google.appengine.api import users

from types import *
import logging

gContainer = {}
gKeyCounter = 0

root_key = 'dct_root'


class ContentType(object):
  ROOT = 1
  AREA = 2
  CRAG = 3
  CLIMB = 4


class BooleanProperty(object):
    def __init__(self, default=None):
        if default is None or type(default) is BooleanType:
            self.value = default
            return
        raise TypeError

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        if type(value) is not BooleanType and value is not None:
            raise TypeError
        self.value = value


class EnumProperty(object):
    def __init__(self, classType, default=None):
        self.classType = classType
        if default is None or default in [getattr(self.classType, k) for k in dir(self.classType) if k[0] != '_']:
            self.value = default
            return
        raise TypeError

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        if value not in [getattr(self.classType, k) for k in dir(self.classType) if k[0] != '_'] and value is not None:
            raise TypeError
        self.value = value


class StringProperty(object):
    def __init__(self, default=None, repeated=False):
        self.repeated = repeated
        if repeated == True:
            self.value = []
            if type(default) is StringType:
                self.value.append(default)
            elif type(default) is ListType:
                self.value = default
            return
        elif default is None or type(default) is StringType:
            self.value = default
            return
        raise TypeError

    def __get__(self, instance, owner):
        logging.error(instance)
        logging.error(owner)
        return self.value

    def __set__(self, instance, value):
        if value is None:
            self.value = value
            return
        if self.repeated and type(value) is ListType and len([val for val in value if type(val) is not StringType]) == 0:
            self.value = value
            return
        if self.repeated and type(value) is StringType:
            self.value = [value]
            return
        if not self.repeated and type(value) is StringType:
            self.value = value
            return
        raise TypeError

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        logging.error("__setitem__")
        if type(value) is StringType:
            self.value[key] = value
            return
        raise TypeError


class DataStore(object):
    def __init__(self, key=None, **kwargs):
        self.key = key
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def get(self, key=None):
        if key is None:
            key = self.key
        return gContainer.get(key)

    def put(self, value=None):
        global gKeyCounter
        if self.key is None:
            gKeyCounter += 1
            self.key = DataStore.make_key(gKeyCounter)
        if value is None:
            value = self
        gContainer[self.key] = value
        return self.key

    def __setitem__(self, value, key=None):
        if key is None:
            key = self.key
        gContainer[key] = value

    def __getitem__(self, key=None):
        if key is None:
            key = self.key
        return gContainer[key]

    @staticmethod
    def make_key(intiger):
        return 'dct_%s' % intiger


class Container(DataStore):
    active = BooleanProperty()
    contType = EnumProperty(ContentType)
    menuParent = StringProperty()
    menuChildren = StringProperty(repeated=True)
    attributes = StringProperty(repeated=True)

class Attrib(DataStore):
    authur = None
    created = None
    modified = None
    active = BooleanProperty()

class AttribName(Attrib):
    text = StringProperty()

class AttribDescription(Attrib):
    text = StringProperty()


class Element:
    def __init__(self, key=None, active=None, contType=None, menuParent=None):
        self.key = None
        self.container = None
        self.attribs = None
        self.keys = []
        self.containers = []
        if key is not None:
            self.lookup(key=key, active=active, contType=contType)
        else:
            self.create(active=active, contType=contType, menuParent=menuParent)

    def lookup(self, key=None, active=None, contType=None):
        if contType is not None and type(contType) is not ListType:
            contType = [contType]

        if type(key) is ndb.Key:
            key = 'ndb_%s_%s' % (key.kind(), key.id())

        if type(key) is ndb.Key:
            self.lookupSingle(key, active, contType)
        elif type(key) is ListType:
            self.lookupMultiple(key, active, contType)
        else:
            logging.error('Not a key: %s' % key)
            raise TypeError

    def lookupSingle(self, key=None, active=None, contType=None):
        if type(key) is StringType:
            key = DataStore(key)
        self.container = key.get()
        if self.container is None:
            return

        if active is not None and not self.container.active == active:
            self.container = None
            return
        if contType is not None and self.container.contType not in contType:
            self.container = None
            return
        self.key = key
        return

    def lookupMultiple(self, key=None, active=None, contType=None):
            key = list(set(key))
            key = [k for k in key if type(k) is ndb.Key]
            self.keys = []
            self.containers = []
            for entity in ndb.get_multi(key):
                if active is not None and not entity.active == active:
                    continue
                if contType is not None and entity.contType not in contType:
                    continue
                self.keys.append(entity.key)
                self.containers.append(entity)
            return

    def create(self, active=None, contType=None, menuParent=None):
        user = users.get_current_user()
        if user is not None:
            tmpKey = self.key
            if contType == ContentType.ROOT:
                if users.is_current_user_admin():
                    #tmpContainer = root_key.get()
                    tmpContainer = Container(key=root_key).get()
                    if tmpContainer is None:
                        tmpContainer = Container(key=root_key, active=True, contType=contType, menuParent=None, menuChildren=[])
                        tmpKey = tmpContainer.put()

                        attribute = AttribName(parent=tmpKey, text="root", authur=user)
                        attributeKey = attribute.put()

                        tmpContainer.attributes = [attributeKey]
                        tmpContainer.put()
                if tmpKey is None:
                    logging.info('Tried to bootstrap but something went wrong')
                    logging.info('user:  %s' % user)
                    logging.info('admin: %s' % users.is_current_user_admin())
                    tmpKey = root_key
                    tmpContainer = tmpKey.get()
            else:
                if type(menuParent) is ndb.Key:
                    menuParent = menuParent.get()
                elif menuParent.__class__ is Element and type(menuParent.key) is ndb.Key:
                    # Re-fetch menuParent from db to ensure fresh data.
                    menuParent = menuParent.key.get()
                else:
                    logging.error('Not a key: %s' % menuParent)
                    raise TypeError
                if active is None:
                    active = False
                #self.container = Container(parent=root_key, active=active, contType=contType, menuParent=menuParent.key)
                tmpContainer = Container(active=active, contType=contType, menuParent=menuParent.key, menuChildren=[])
                tmpKey = tmpContainer.put()

                if tmpKey not in menuParent.menuChildren:
                    menuParent.menuChildren.append(tmpKey)
                    menuParent.put()

            # Do these last so they are not done yet if transaction is rolled back.
            self.key = tmpKey
            self.container = tmpContainer

