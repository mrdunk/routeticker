from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from protorpc import messages
from google.appengine.api import users
import logging
from types import *

root_key = ndb.Key('Container', 'root')

class Type(messages.Enum):
  ROOT = 1
  AREA = 2
  CRAG = 3
  CLIMB = 4

class Container(ndb.Model):
    active = ndb.BooleanProperty(default=False)
    contType = msgprop.EnumProperty(Type, required=True)
    menuParent = ndb.KeyProperty()
    menuChildren = ndb.KeyProperty(repeated=True)
    attributes = ndb.KeyProperty(repeated=True)


class Attrib(ndb.Model):
    authur = ndb.UserProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    modified = ndb.DateTimeProperty(auto_now=True)
    active = ndb.BooleanProperty(default=False)


class AttribName(Attrib):
    text = ndb.StringProperty()


class AttribDescription(Attrib):
    text = ndb.TextProperty()


class Element:
    """
    Instance variables:
        self.key:        Key of single element.
                         If a lookup of multiple elemets was performed, this field will be Null and self.keys will be used instead.
        self.container:  Datastore entry for single element.
                         If a lookup of multiple elemets was performed, this field will be Null and self.container will be used instead.
        self.keys:       If a lookup for multiple keys has been performed this will contain a list of sucessfully retreived keys.
                         Otherwise it will contain an empty list.
        self.containers: If a lookup for multiple keys has been performed this will contain a list of sucessfully retreived elements.
                         Otherwise it will contain an empty list.
    """
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
            self.lookupSingle(key, active, contType)
        elif type(key) is ListType:
            # Cross group transactions can only span 5 or less groups.
            if len(key) <= 5:
                ndb.transaction(lambda: self.lookupMultiple(key, active, contType), xg=True)
            else:
                # LOOKUP NOT IN TRANSACTION.
                self.lookupMultiple(key, active, contType)
        else:
            logging.error('Not a key: %s' % key)
            raise TypeError

    @ndb.transactional
    def lookupSingle(self, key=None, active=None, contType=None):
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

    @ndb.transactional(xg=True)
    def create(self, active=None, contType=None, menuParent=None):
        user = users.get_current_user()
        if user is not None:
            tmpKey = self.key
            if contType == Type.ROOT:
                if users.is_current_user_admin():
                    tmpContainer = root_key.get()
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
         
    @ndb.transactional
    def addAttrib(self, attribute):
        user = users.get_current_user()
        if user is not None:
            attributeClass = type(attribute)
            existingAttribs = attributeClass.query(ancestor=self.key).filter(attributeClass.authur==user).fetch(1)

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

    @ndb.transactional
    def setAttribActive(self, key):
        attribute = key.get()
        attributeClass = type(attribute)
        existingAttribs = attributeClass.query(ancestor=self.key).fetch(1000)
        for a in existingAttribs:
            if key == a.key:
                a.active = True
            else:
                a.active = False
        ndb.put_multi(existingAttribs)

    @ndb.transactional
    def getAtribTypes(self):
        # self.attribs = [attribType1, attribType2 ...]
        attribs = list(set([key.kind() for key in self.container.attributes]))
        if self.attribs is not None:
            for attrib in self.attribs:
                if type(attrib) is ListType:
                    attrib = type(attrib[0])
                if attrib not in attribs:
                    attribs.append(attrib)
        self.attribs = attribs

    @ndb.transactional
    def getAttribDeep(self, attribute):
        # self.attribs = [attribType1, [attribType2_instance1, attribType2_instance2 ...] ...]
        if self.attribs is None:
            self.getAtribTypes()
        outList = []
        for attrib in self.attribs:
            if type(attrib) is ListType:
                for attribInstance in attrib:
                    if attribInstance is not None:
                        if type(attribInstance) is not type(attribute):
                            # Not a match so copy it to new list.
                            outList.append(attrib)
                        break
            else:
                # this attrib is still just a placeholder
                if not attrib == type(attribute).__name__:
                    outList.append(attrib)

        attributes = type(attribute).query(ancestor=self.key).fetch(100)
        outList.append(attributes)

        self.attribs = outList
        return attributes

    @ndb.transactional
    def getAttribShallow(self, attribute):
        """ Populate self.attribs with only the active attribute and pad the remainder of the array with None."""
        # self.attribs = [attribType1, [attribType2_instance1, None, None ...] ...]
        if self.attribs is None:
            self.getAtribTypes()
        outList = []
        for attrib in self.attribs:
            if type(attrib) is ListType:
                # this attrib has already been populated
                correctlyPopulated = 0
                for attribInstance in attrib:
                    if attribInstance is not None:
                        if type(attribInstance) is not type(attribute):
                            outList.append(attrib)
                            break
                        correctlyPopulated += 1
                if correctlyPopulated == len(attrib) and correctlyPopulated > 0:
                    # Has already been populated
                    return
            else:
                # this attrib is still just a placeholder
                if not attrib == type(attribute).__name__:
                    outList.append(attrib)

        numOfAttribs = type(attribute).query(ancestor=self.key).count(100)
        attributes = type(attribute).query(ancestor=self.key).filter(type(attribute).active==True).fetch(1)
        outList.append(attributes + [None] * (numOfAttribs -1))

        self.attribs = outList
        return attributes[0]

    @ndb.transactional
    def getAttribShallowAll(self):
        if self.attribs is None:
            self.getAtribTypes()
        outList = []
        for attrib in self.attribs:
            if type(attrib) is ListType:
                # this attrib has already been populated
                outList.append(attrib)
            else:
                # globals()[attrib] is the class whose name mathches the attrib string.
                numOfAttribs = globals()[attrib].query(ancestor=self.key).count(100)
                attributes = globals()[attrib].query(ancestor=self.key).filter(globals()[attrib].active==True).fetch(1)
                outList.append(attributes + [None] * (numOfAttribs -1))
        self.attribs = outList

    def getMenuChildren(self):
        return self.container.menuChildren

    def getMenuParent(self):
        return self.container.menuParent


def copyAttrib(attribute, parent):
    attributeClass = type(attribute)
    props = attribute.to_dict()
    props['parent'] = parent
    logging.info(props)

    return attributeClass(**props)

def clear():
    #q = Container.query().fetch(20)
    q = ndb.gql("SELECT __key__").fetch(100)
    logging.info("deleting\n%s" % q)
    ndb.delete_multi(q)
