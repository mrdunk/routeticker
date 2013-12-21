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


class AllProperties(object):
    """
    It is important not to modify self.index.
    This value is a unique identifier for the Property Instance so it can be tracked accross multiple instances of it's parent class.
    The unique self.index is registerd in self.instanceIndexed of the parent class.
    """
    index = 0

    @classmethod
    def increaseIndex(cls):
        """ Keep a counter of how many Properties (of all kinds) have been initialised."""
        cls.index += 1

    def checkInput(self, data):
        return (not self.repeated and \
                    (data is None or type(data) is self.dataType)) or \
               (self.repeated and type(data) is ListType and \
                    len([item for item in data if type(item) is self.dataType]) == len(data))

    def __init__(self, dataType, default=None, repeated=False):
        AllProperties.increaseIndex()

        if repeated == True and default is None:
            default = []

        self.default = default
        self.instanceIndexed = []
        self.instanceIndex = self.index
        self.repeated = repeated
        self.dataType = dataType
        if self.checkInput(default):
            return
        raise TypeError

    def __get__(self, instance, owner):
        if "instanceIndexed" not in dir(instance):
            instance.instanceIndexed = []
        if self.instanceIndex not in self.instanceIndexed:
            instance.instanceIndexed.append(self.instanceIndex)

        index = instance.instanceIndexed.index(self.instanceIndex)

        if "values" not in dir(instance):
            instance.values = []
        if len(instance.values) <= index:
            instance.values.extend([None] * (1 + index - len(instance.values)))
            if self.repeated:
                self.default = self.ListValue(self.dataType, self.default)
            instance.values[index] = self.default

        return instance.values[index]

    def __set__(self, instance, value):
        if not self.checkInput(value):
            raise TypeError

        if "instanceIndexed" not in dir(instance):
            instance.instanceIndexed = []
        if self.instanceIndex not in self.instanceIndexed:
            instance.instanceIndexed.append(self.instanceIndex)
        index = instance.instanceIndexed.index(self.instanceIndex)

        if "values" not in dir(instance):
            instance.values = []
        if len(instance.values) <= index:
            instance.values.extend([None] * (1 + index - len(instance.values)))

        if self.repeated:
            value = self.ListValue(self.dataType, value)
        instance.values[index] = value

    class ListValue(list):
        """Overload a list to perform some value checking on repeated values."""

        def __init__(self, dataType, *kargs):
            list.__init__(self, *kargs)
            self.dataType = dataType

        def __setitem__(self, key, value):
            if type(value) is self.dataType:
                list.__setitem__(self, key, value)
            elif type(value) is ListType and len([item for item in value if type(item) is self.dataType]) == len(value):
                list.__setitem__(self, key, value)
            else:
                raise TypeError

class BooleanProperty(AllProperties):
    def __init__(self, default=None, repeated=False):
        AllProperties.__init__(self, BooleanType, default=default, repeated=repeated)


class EnumProperty(AllProperties):
    def __init__(self, classType, default=None, repeated=False):
        AllProperties.__init__(self, classType, default=default, repeated=repeated)

    def checkInput(self, data):
        return (not self.repeated and \
                    (data is None or data in [getattr(self.dataType, k) for k in dir(self.dataType) if k[0] != '_'])) or \
               (self.repeated and type(data) is ListType and \
                    len([item for item in data if type(item) is self.dataType]) == len(data))


class StringProperty(AllProperties):
    def __init__(self, default=None, repeated=False):
        AllProperties.__init__(self, StringType, default=default, repeated=repeated)

class StringProperty2(object):
    def __init__(self, default=None, repeated=False):
        if repeated:
            self.obj = StringPropertyRepeated(default=default)
        else:
            self.obj = StringPropertySingle(default=default)

    def __get__(self, instance, owner):
        if self.obj is not None:
            if self.obj.__class__ is StringPropertySingle:
                # Single value
                return self.obj.__get__(instance, owner)
            # List of values
            # http://stackoverflow.com/questions/20648366/strange-interaction-between-setitem-and-get
            return self.obj
        return

    def __set__(self, instance, value):
        self.obj.__set__(instance, value)

    def __getitem__(self, key):
        return self.obj.__getitem__(key)

    def __setitem__(self, key, value):
        self.obj.__setitem__(key, value)

class StringPropertyRepeated(list):
    def __init__(self, default=None):
        if type(default) is StringType:
            list.__init__(self, [default])
            return
        elif type(default) is ListType and ListType and len([val for val in default if type(val) is not StringType]) == 0:
            list.__init__(self, default)
            return
        elif default is None:
            list.__init__(self, [])
            return
        raise TypeError

    def __set__(self, instance, value):
        if value is None:
            list.__init__(self, [])
            return
        if type(value) is ListType and len([val for val in value if type(val) is not StringType]) == 0:
            list.__init__(self, value)
            return
        if type(value) is StringType:
            list.__init__(self, [value])
            return
        raise TypeError

    def __getitem__(self, key):
        return list.__getitem__(self, key)

    def __setitem__(self, key, value):
        if type(value) is StringType:
            list.__setitem__(self, key, value)
            return
        raise TypeError

class StringPropertySingle(object):
    def __init__(self, default=None):
        self.value = None
        if default is None or type(default) is StringType:
            self.value = default
            return
        raise TypeError

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        if value is None:
            self.value = value
            return
        if type(value) is StringType:
            self.value = value
            return
        raise TypeError

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        if type(value) is StringType:
            self.value[key] = value
            return
        raise TypeError


class DataStore(object):
    def __init__(self, **kwargs):
        logging.debug("__init__")
        self.key = None     # May get overwritten by kwargs.
        for k in kwargs:
            setattr(self, k, kwargs[k])

    def get(self, key=None):
        if key is None:
            key = self.key
        if key is None:
            raise KeyError
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

    # Don't know if we'll use this
    def __setitem__(self, key, value):
        if key is not None:
            self.key = key
        self.put(value)

    # Don't know if we'll use this
    def __getitem__(self, key=None):
        if key is None:
            key = self.key
        if key is None:
            raise KeyError
        return gContainer[key]

    @staticmethod
    def make_key(intiger):
        return 'dct_%s' % intiger

    @classmethod
    def query(cls, **kwargs):
        logging.debug("DataStore.query(%s, %s)" % (cls, kwargs))
        self = cls.__new__(cls)
        return self

    def filter(self, **kwargs):
        logging.debug("DataStore.filter(%s)" % kwargs)
        return self
    def fetch(self, **kwargs):
        logging.debug("DataStore.fetch(%s)" % kwargs)
        return self
    def count(self, **kwargs):
        logging.debug("DataStore.count(%s)" % kwargs)
        return 0


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

        if type(key) is StringType:
            self.lookupSingle(key, active, contType)
        elif type(key) is ListType:
            self.lookupMultiple(key, active, contType)
        else:
            logging.error('Not a key: %s' % key)
            raise TypeError

    def lookupSingle(self, key=None, active=None, contType=None):
        self.container = DataStore(key=key).get()
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

    def lookupMultiple(self, keys=None, active=None, contType=None):
            keys = list(set(keys))
            keys = [k for k in keys if type(k) is StringType]
            self.keys = []
            self.containers = []
            for key in keys:
                entity = DataStore(key=key).get()
                if entity is None:
                    continue
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
                    tmpContainer = DataStore(key=tmpKey).get()
            else:
#                if type(menuParent) is ndb.Key:
#                    logging.warning("Dangerous key type.")
#                    menuParent = menuParent.get()
#                elif menuParent.__class__ is Element and type(menuParent.key) is not None:
#                    # Re-fetch menuParent from db to ensure fresh data.
#                    menuParent = menuParent.container.get()

                if type(menuParent) is StringType:
                    #menuParent = DataStore(key=menuParent).get()
                    menuParent = Element(key=menuParent)
                else:
                    #menuParent = DataStore(key=menuParent.key).get()
                    menuParent = Element(key=menuParent.key)

                if menuParent.container.__class__ is not Container:
                    logging.error('Not a key: %s' % menuParent)
                    raise TypeError

                if active is None:
                    active = False

                #self.container = Container(parent=root_key, active=active, contType=contType, menuParent=menuParent.key)
                tmpContainer = Container(active=active, contType=contType, menuParent=menuParent.key, menuChildren=[])
                tmpKey = tmpContainer.put()

                if tmpKey not in menuParent.container.menuChildren:
                    menuParent.container.menuChildren.append(tmpKey)
                    menuParent.container.active = True
                    menuParent.container.put()
            # Do these last so they are not done yet if transaction is rolled back.
            self.key = tmpKey
            self.container = tmpContainer

    def addAttrib(self, attribute):
        user = users.get_current_user()
        if user is not None:
            attributeClass = type(attribute)
            attributeInstance = AttribName()
            logging.debug(attributeInstance)
            logging.debug(dir(attributeInstance))

            query = attributeInstance.query(ancestor=self.key)
            logging.debug(query)

            #query = query.filter(authur==user)
            #existingAttribs = query.fetch(1)
            #existingAttribs = attributeInstance.query(ancestor=self.key)#.filter(attributeInstance.authur==user).fetch(1)

            if len(existingAttribs):
                props = attribute.to_dict()
                attribute = existingAttribs[0]
                attribute.populate(**props)
            else:
                attribute.authur = user
                attribute = copyAttrib(attribute, self.key)
            attributeKey = attribute.put()

            # Get up to date version of container from datastore incase the one hee is stale.
            tmpContainer = self.key.get()
            if attributeKey and attributeKey not in tmpContainer.attributes:
                tmpContainer.attributes.append(attributeKey)
                tmpContainer.put()
                # Do this after .put() so self.container is not modified if transaction is rolledback.
                self.container = tmpContainer

            # Update record with new attribute.
            if self.attribs is not None:
                outAtribList = []
                attribFound = False
                for attrib in self.attribs:
                    if type(attrib) is ListType:
                        outInstanceList = []
                        for attribInstance in attrib:
                            outInstanceList.append(attribInstance)
                            match = False
                            if attribInstance is not None:
                                if type(attribInstance) is type(attribute):
                                    attribFound = True
                                    match = True
                        if match:
                            outInstanceList.append(attribute)
                        outAtribList.append(outInstanceList)
                    else:
                        if attrib == type(attribute).__name__:
                            attribFound = True
                        outAtribList.append(attrib)
                if not attribFound:
                    outAtribList.append(type(attribute).__name__)
                self.attribs = outAtribList
        return attribute
