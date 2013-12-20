import unittest
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util
from google.appengine.api import users

import data_ndb

class ElementTestCase(unittest.TestCase):

  def setUp(self):
    # First, create an instance of the Testbed class.
    self.testbed = testbed.Testbed()
    # Then activate the testbed, which prepares the service stubs for use.
    self.testbed.activate()
    
    # Next, declare which service stubs you want to use.
    #self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()
    self.testbed.init_user_stub()

    # Create a consistency policy that will simulate the High Replication consistency model.
    self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=0)
    # Initialize the datastore stub with this policy.
    self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)

  def tearDown(self):
    self.testbed.deactivate()

  def testInitCreateRootNodeSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)

    # Ancestor querys: 
    # root container is ancestor of it's self.
    self.assertEqual(1, data_ndb.Container.query(ancestor=data_ndb.root_key).count(10))

    # root's "name" is an ancestor of root node.
    self.assertEqual(1, data_ndb.AttribName.query(ancestor=root_node.key).count(10))
    self.assertEqual(root_node.key, data_ndb.root_key)

    self.assertEqual(data_ndb.Type.ROOT, root_node.container.contType)
    self.assertIsNone(root_node.container.menuParent)

  def testInitCreateRootNodeTwice(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)

    self.assertEqual(1, data_ndb.Container.query(ancestor=data_ndb.root_key).count(10))
    self.assertEqual(1, data_ndb.AttribName.query(ancestor=data_ndb.root_key).count(10))

    root_node2 = data_ndb.Element(contType=data_ndb.Type.ROOT)

    self.assertEqual(1, data_ndb.Container.query(ancestor=data_ndb.root_key).count(10))
    self.assertEqual(1, data_ndb.AttribName.query(ancestor=data_ndb.root_key).count(10))

    self.assertEqual(root_node.key, root_node2.key)

  def testInitCreateRootNodeNotAdmin(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)

    self.assertEqual(0, data_ndb.Container.query(ancestor=data_ndb.root_key).count(10))

  def testInitCreateRootNodeNotUser(self):
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    
    self.assertEqual(0, data_ndb.Container.query(ancestor=data_ndb.root_key).count(10))

  def testInitCreateContainerSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)

    # Using root_node as parent.
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)
    # re-read the root_node to update child keys.
    root_node = data_ndb.Element(key=root_node.key)

    self.assertEqual(1, data_ndb.Container.query(ancestor=root_node.key).count(10))
    self.assertEqual(1, data_ndb.Container.query(ancestor=child_node.key).count(10))
    self.assertEqual(2, data_ndb.Container.query().count(10))

    self.assertNotEqual(child_node.key, data_ndb.root_key)
    
    self.assertIn(child_node.key, root_node.container.menuChildren)
    self.assertEqual(1, len(root_node.container.menuChildren))

    self.assertEqual(child_node.container.menuParent, root_node.key)

    self.assertEqual(data_ndb.Type.AREA, child_node.container.contType)

  def testInitCreateContainerFromParentKeySucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)

    # Using root_node.key as parent.
    child_node = data_ndb.Element(menuParent=root_node.key, contType=data_ndb.Type.AREA)
    # re-read the root_node to update child keys.
    root_node = data_ndb.Element(key=root_node.key)

    self.assertEqual(1, data_ndb.Container.query(ancestor=root_node.key).count(10))
    self.assertEqual(1, data_ndb.Container.query(ancestor=child_node.key).count(10))
    self.assertEqual(2, data_ndb.Container.query().count(10))

    self.assertNotEqual(child_node.key, data_ndb.root_key)

    self.assertIn(child_node.key, root_node.container.menuChildren)
    self.assertEqual(1, len(root_node.container.menuChildren))

    self.assertEqual(child_node.container.menuParent, root_node.key)

    self.assertEqual(data_ndb.Type.AREA, child_node.container.contType)

  def testInitCreateContainerX10Flat(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)

    child_nodes = [data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA) for unused in range(10)]
    # re-read the root_node to update child keys.
    root_node = data_ndb.Element(key=root_node.key)

    self.assertEqual(1, data_ndb.Container.query(ancestor=root_node.key).count(100))
    for child_node in child_nodes:
        self.assertEqual(1, data_ndb.Container.query(ancestor=child_node.key).count(100))
        self.assertNotEqual(child_node.key, data_ndb.root_key)

        self.assertIn(child_node.key, root_node.container.menuChildren)

        self.assertEqual(child_node.container.menuParent, root_node.key)
    self.assertEqual(10, len(root_node.container.menuChildren))

  def testInitCreateContainerX10Stacked(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)

    nodeHolder = root_node
    child_nodes = []
    for unused in range(10):
        # Each new node is a child of the previous.
        nodeHolder = data_ndb.Element(menuParent=nodeHolder, contType=data_ndb.Type.AREA)
        child_nodes.append(nodeHolder)

    root_node = data_ndb.Element(key=root_node.key)

    self.assertEqual(1, data_ndb.Container.query(ancestor=root_node.key).count(100))
    self.assertEqual(1, len(root_node.container.menuChildren))

    lastChild = root_node
    for child_node in child_nodes:
        # Re-read child_node to ensure .menuChildren is uptodate.
        child_node = data_ndb.Element(key=child_node.key)
        self.assertNotEqual(child_node.key, data_ndb.root_key)
        self.assertNotEqual(child_node.key, lastChild.key)

        self.assertLessEqual(len(lastChild.container.menuChildren), 1)  # The last node has no children
        self.assertIn(child_node.key, lastChild.container.menuChildren)
        self.assertEqual(child_node.container.menuParent, lastChild.key)

        lastChild = child_node

    self.assertEqual(0, len(lastChild.container.menuChildren))  # The last node has no children

  def testInitCreateContainerNotUser(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    self.assertIsNone(users.get_current_user())

    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)
    
    self.assertEqual(1, data_ndb.Container.query(ancestor=root_node.key).count(10))
    self.assertIsNone(child_node.key)

  def testInitLookupOneSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_ndb.Element(key=root_node.key)

    self.assertEqual(root_node.key, test_node.key)
    self.assertEqual(root_node.container, test_node.container)

  def testInitLookupOneByKeyString(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_ndb.Element(key=root_node.key.id())

    self.assertEqual(root_node.key, test_node.key)
    self.assertEqual(root_node.container, test_node.container)    

  def testInitLookupOneFail(self):
    badKey1 = ndb.Key('Container', 'earwax')
    badKey2 = ndb.Key('AttribName', data_ndb.root_key.id())
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)

    test_node1 = data_ndb.Element(key=badKey1)

    self.assertNotEqual(root_node, test_node1)

    test_node2 = data_ndb.Element(key=badKey2)

    self.assertNotEqual(root_node, test_node2)

  def testInitLookupManySucess(self):
    NUMBER = 10
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA).key for unused in range(NUMBER)]

    test_lookup = data_ndb.Element(key=child_nodes_keys)
    self.assertEqual(len(test_lookup.keys), NUMBER)
    self.assertEqual(len(test_lookup.containers), NUMBER)

    # Cross group transactions can only span 5 or less groups so try a lower number that uses transactions too.
    NUMBER = 3
    child_nodes_keys = child_nodes_keys[:NUMBER]
    test_lookup = data_ndb.Element(key=child_nodes_keys)
    self.assertEqual(len(test_lookup.keys), NUMBER)
    self.assertEqual(len(test_lookup.containers), NUMBER)

  def testInitLookupManyFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA).key for unused in range(10)]

    child_nodes_keys[0] = None

    test_lookup = data_ndb.Element(key=child_nodes_keys)
    self.assertEqual(len(test_lookup.keys), 9)
    self.assertEqual(len(test_lookup.containers), 9)

    child_nodes_keys[0] = child_nodes_keys[1]
    test_lookup = data_ndb.Element(key=child_nodes_keys)
    self.assertEqual(len(test_lookup.keys), 9)
    self.assertEqual(len(test_lookup.containers), 9)

  def testInitLookupLimitedSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_ndb.Element(key=root_node.key, active=True, contType=data_ndb.Type.ROOT)

    self.assertEqual(root_node.key, test_node.key)
    self.assertEqual(root_node.container, test_node.container)

  def testInitLookupLimitedListSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_ndb.Element(key=root_node.key, active=True, contType=[data_ndb.Type.ROOT, data_ndb.Type.AREA])

    self.assertEqual(root_node.key, test_node.key)
    self.assertEqual(root_node.container, test_node.container)

  def testInitLookupLimitedFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_ndb.Element(key=root_node.key, contType=data_ndb.Type.AREA)

    self.assertNotEqual(root_node.key, test_node.key)
    self.assertNotEqual(root_node.container, test_node.container)

    test_node = data_ndb.Element(key=root_node.key, active=False)

    self.assertNotEqual(root_node.key, test_node.key)
    self.assertNotEqual(root_node.container, test_node.container)

  def testInitLookupLimitedListFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_ndb.Element(key=root_node.key, contType=[data_ndb.Type.AREA, data_ndb.Type.CRAG])

    self.assertNotEqual(root_node.key, test_node.key)
    self.assertNotEqual(root_node.container, test_node.container)

  def testInitLookupManyLimitedSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA).key for unused in range(10)]

    test_lookup = data_ndb.Element(key=child_nodes_keys, active=False, contType=data_ndb.Type.AREA)
    self.assertEqual(len(test_lookup.keys), 10)
    self.assertEqual(len(test_lookup.containers), 10)

  def testInitLookupManyLimitedListSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA).key for unused in range(10)]

    test_lookup = data_ndb.Element(key=child_nodes_keys, active=False, contType=[data_ndb.Type.AREA, data_ndb.Type.CRAG])
    self.assertEqual(len(test_lookup.keys), 10)
    self.assertEqual(len(test_lookup.containers), 10)

  def testInitLookupManyLimitedFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA).key for unused in range(10)]
  
    test_lookup = data_ndb.Element(key=child_nodes_keys, contType=data_ndb.Type.CRAG)
    self.assertEqual(len(test_lookup.keys), 0)
    self.assertEqual(len(test_lookup.containers), 0)

    test_lookup = data_ndb.Element(key=child_nodes_keys, active=True)
    self.assertEqual(len(test_lookup.keys), 0)
    self.assertEqual(len(test_lookup.containers), 0)

  def testInitLookupManyLimitedListFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA).key for unused in range(10)]
  
    test_lookup = data_ndb.Element(key=child_nodes_keys, contType=[data_ndb.Type.ROOT, data_ndb.Type.CRAG])
    self.assertEqual(len(test_lookup.keys), 0)
    self.assertEqual(len(test_lookup.containers), 0)

  def testInitLookupManyLimitedListPartialSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA).key for unused in range(10)]
    child_nodes_keys.append(data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.CRAG).key)
    child_nodes_keys.append(data_ndb.Element(menuParent=root_node, active=True, contType=data_ndb.Type.AREA).key)
  
    test_lookup = data_ndb.Element(key=child_nodes_keys, contType=data_ndb.Type.CRAG)
    self.assertEqual(len(test_lookup.keys), 1)
    self.assertEqual(len(test_lookup.containers), 1)

    test_lookup = data_ndb.Element(key=child_nodes_keys, active=True)
    self.assertEqual(len(test_lookup.keys), 1)
    self.assertEqual(len(test_lookup.containers), 1)

  def testAddAttribSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)

    child_node.addAttrib(data_ndb.AttribName(text="test name"))
    child_node.addAttrib(data_ndb.AttribDescription(text="test description"))

    self.assertEqual(1, data_ndb.AttribName.query(ancestor=root_node.key).count(10))
    self.assertEqual(1, data_ndb.AttribName.query(ancestor=child_node.key).count(10))

    self.assertEqual(2, len(child_node.container.attributes))
    
    atribs_name = data_ndb.AttribName.query(ancestor=child_node.key).fetch(10)
    self.assertEqual(1, len(atribs_name))
    self.assertIn(atribs_name[0].key, child_node.container.attributes)

  def testAddAttribMultiple(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node_l1 = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)
    child_node_l2 = data_ndb.Element(menuParent=child_node_l1, contType=data_ndb.Type.AREA)

    # Create child_node_l2 attributes first to make sure ancestor queries do not get confused.
    child_node_l2.addAttrib(data_ndb.AttribName(text="test name 3"))

    # Same user should not be able to create duplicate attributes
    child_node_l1.addAttrib(data_ndb.AttribName(text="test name"))
    child_node_l1.addAttrib(data_ndb.AttribDescription(text="test description"))
    child_node_l1.addAttrib(data_ndb.AttribName(text="test name 2"))
    child_node_l1.addAttrib(data_ndb.AttribDescription(text="test description 2"))
    
    # Create child_node_l2 attribute second to make sure ancestor queries do not get confused.
    child_node_l2.addAttrib(data_ndb.AttribDescription(text="test description 3"))

    self.assertEqual(2, len(child_node_l1.container.attributes))

    self.assertEqual(1, data_ndb.AttribName.query(ancestor=child_node_l1.key).count(10))
    atribs_name = data_ndb.AttribName.query(ancestor=child_node_l1.key).fetch(10)
    self.assertEqual(1, len(atribs_name))
    self.assertIn(atribs_name[0].key, child_node_l1.container.attributes)
    self.assertEqual(atribs_name[0].text, "test name 2")
    self.assertEqual(1, data_ndb.AttribName.query(ancestor=child_node_l1.key).count(10))

    self.assertEqual(1, data_ndb.AttribDescription.query(ancestor=child_node_l1.key).count(10))
    atribs_description = data_ndb.AttribDescription.query(ancestor=child_node_l1.key).fetch(10)
    self.assertEqual(1, len(atribs_description))
    self.assertIn(atribs_description[0].key, child_node_l1.container.attributes)
    self.assertEqual(atribs_description[0].text, "test description 2")
    self.assertEqual(1, data_ndb.AttribDescription.query(ancestor=child_node_l1.key).count(10))

    # TODO check timesamps

    # Different user can create another attribute.
    self.testbed.setup_env(USER_EMAIL='different@gmail.com', USER_ID='2', USER_IS_ADMIN='0', overwrite = True)
    child_node_l1.addAttrib(data_ndb.AttribName(text="test name 3"))
    child_node_l1.addAttrib(data_ndb.AttribDescription(text="test description 3"))

    self.assertEqual(2, data_ndb.AttribName.query(ancestor=child_node_l1.key).count(10))
    self.assertEqual(4, len(child_node_l1.container.attributes))
    atribs_name = data_ndb.AttribName.query(ancestor=child_node_l1.key).fetch(10)
    self.assertEqual(2, len(atribs_name))
    self.assertIn(atribs_name[0].key, child_node_l1.container.attributes)
    self.assertEqual(atribs_name[0].text, "test name 2")
    self.assertIn(atribs_name[1].key, child_node_l1.container.attributes)
    self.assertEqual(atribs_name[1].text, "test name 3")

  def testAddAttribUserFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    child_node.addAttrib(data_ndb.AttribName(text="test name"))

    self.assertEqual(1, data_ndb.AttribName.query(ancestor=root_node.key).count(10))
    self.assertEqual(0, data_ndb.AttribName.query(ancestor=child_node.key).count(10))

  def testAddAttribUpdateSelfAttribs(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)

    child_node.attribs = []
    attribute = child_node.addAttrib(data_ndb.AttribName(text="test name"))

    # Test placeholder in child_node.attribs
    self.assertIn("AttribName", child_node.attribs)

    child_node.attribs = [[attribute]]
    self.testbed.setup_env(USER_EMAIL='otheruser@gmail.com', USER_ID='2', USER_IS_ADMIN='0', overwrite = True)
    attribute_2 = child_node.addAttrib(data_ndb.AttribName(text="test name 2"))

    # Test poulated list in child_node.attribs
    self.assertIn(attribute, child_node.attribs[0])
    self.assertIn(attribute_2, child_node.attribs[0])    

  def testGetAtribTypes(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)

    child_node.addAttrib(data_ndb.AttribName(text="test name"))

    self.testbed.setup_env(USER_EMAIL='otheruser@gmail.com', USER_ID='2', USER_IS_ADMIN='0', overwrite = True)
    child_node.addAttrib(data_ndb.AttribName(text="test name 2"))
 
    child_node.getAtribTypes()
    self.assertEqual(1, len(child_node.attribs))

    child_node.addAttrib(data_ndb.AttribDescription(text="test description"))

    child_node.getAtribTypes()
    self.assertEqual(2, len(child_node.attribs))

  def testGetAttribShallow(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)

    child_node.addAttrib(data_ndb.AttribName(text="test name"))

    self.testbed.setup_env(USER_EMAIL='otheruser@gmail.com', USER_ID='2', USER_IS_ADMIN='0', overwrite = True)
    child_node.addAttrib(data_ndb.AttribName(text="test name 2", active=True))

    self.testbed.setup_env(USER_EMAIL='billythefish@gmail.com', USER_ID='3', USER_IS_ADMIN='0', overwrite = True)
    child_node.addAttrib(data_ndb.AttribName(text="test name 3"))

    attribute = data_ndb.AttribName()
    child_node.getAttribShallow(attribute)

    self.assertEqual(1, len(child_node.attribs))
    self.assertEqual(3, len(child_node.attribs[0]))
    self.assertEqual("test name 2", child_node.attribs[0][0].text)
    self.assertIs(None, child_node.attribs[0][1])
    self.assertIs(None, child_node.attribs[0][2])

    child_node.addAttrib(data_ndb.AttribDescription(text="test description", active=True))

    attribute = data_ndb.AttribDescription()
    child_node.getAttribShallow(attribute)

    # Check existing data has not moved.
    self.assertEqual(2, len(child_node.attribs))
    self.assertEqual(3, len(child_node.attribs[0]))
    self.assertEqual("test name 2", child_node.attribs[0][0].text)
    self.assertIs(None, child_node.attribs[0][1])
    self.assertIs(None, child_node.attribs[0][2])

    self.assertEqual(1, len(child_node.attribs[1]))
    self.assertEqual("test description", child_node.attribs[1][0].text)

  def testGetAttribDeep(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)

    attribute_0 = child_node.addAttrib(data_ndb.AttribDescription(text="test description", active=True))
    attribute_1 = child_node.addAttrib(data_ndb.AttribName(text="test name"))

    self.testbed.setup_env(USER_EMAIL='otheruser@gmail.com', USER_ID='2', USER_IS_ADMIN='0', overwrite = True)
    attribute_2 = child_node.addAttrib(data_ndb.AttribName(text="test name 2", active=True))

    self.testbed.setup_env(USER_EMAIL='billythefish@gmail.com', USER_ID='3', USER_IS_ADMIN='0', overwrite = True)
    attribute_3 = child_node.addAttrib(data_ndb.AttribName(text="test name 3"))

    attribute = data_ndb.AttribName()
    attributes = child_node.getAttribDeep(attribute)

    # Placeholder
    self.assertIn(type(attribute_0).__name__, child_node.attribs)
    # Fully populated list
    self.assertIn(attributes, child_node.attribs)
    self.assertIn(attribute_1, attributes)
    self.assertIn(attribute_2, attributes)
    self.assertIn(attribute_3, attributes)

    self.assertEqual("test name", attribute_1.text)
    self.assertEqual("test name 2", attribute_2.text)
    self.assertEqual("test name 3", attribute_3.text)

  def testGetAttribShallowAll(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)

    attribute_0 = child_node.addAttrib(data_ndb.AttribDescription(text="test description", active=True))
    attribute_1 = child_node.addAttrib(data_ndb.AttribName(text="test name"))

    self.testbed.setup_env(USER_EMAIL='otheruser@gmail.com', USER_ID='2', USER_IS_ADMIN='0', overwrite = True)
    attribute_2 = child_node.addAttrib(data_ndb.AttribDescription(text="test description 2"))
    attribute_3 = child_node.addAttrib(data_ndb.AttribName(text="test name 2", active=True))

    self.testbed.setup_env(USER_EMAIL='billythefish@gmail.com', USER_ID='3', USER_IS_ADMIN='0', overwrite = True)
    attribute_4 = child_node.addAttrib(data_ndb.AttribDescription(text="test description 3"))
    attribute_5 = child_node.addAttrib(data_ndb.AttribName(text="test name 3"))

    child_node.getAttribShallowAll()

    self.assertEqual(2, len(child_node.attribs))
    flatList = [item for sublist in child_node.attribs for item in sublist]
    self.assertEqual(6, len(flatList))
    self.assertIn(attribute_0, flatList)
    self.assertIn(attribute_3, flatList)
    self.assertNotIn(attribute_1, flatList)
    self.assertNotIn(attribute_2, flatList)
    self.assertNotIn(attribute_4, flatList)
    self.assertNotIn(attribute_5, flatList)
    self.assertIn(None, flatList)

  def testGetMenuChildren(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node_1 = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)
    child_node_2 = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)
    child_node_3 = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)
    # re-read the root_node to update child keys.
    root_node = data_ndb.Element(key=root_node.key)

    children = root_node.getMenuChildren()
    self.assertIn(child_node_1.key.id(), children)
    self.assertIn(child_node_2.key.id(), children)
    self.assertIn(child_node_3.key.id(), children)
    self.assertEqual(3, len(children))

  def testGetMenuParent(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)
    # re-read the root_node to update child keys.
    root_node = data_ndb.Element(key=root_node.key)

    parent = child_node.getMenuParent()
    self.assertEqual(parent, root_node.key.id())

  def testSetAttribActive(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_ndb.Element(contType=data_ndb.Type.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_ndb.Element(menuParent=root_node, contType=data_ndb.Type.AREA)
    # re-read the root_node to update child keys.
    root_node = data_ndb.Element(key=root_node.key)

    attribute_0 = child_node.addAttrib(data_ndb.AttribDescription(text="test description", active=True))
    attribute_1 = child_node.addAttrib(data_ndb.AttribName(text="test name"))

    self.testbed.setup_env(USER_EMAIL='otheruser@gmail.com', USER_ID='2', USER_IS_ADMIN='0', overwrite = True)
    attribute_2 = child_node.addAttrib(data_ndb.AttribDescription(text="test description 2"))
    attribute_3 = child_node.addAttrib(data_ndb.AttribName(text="test name 2", active=True))

    self.testbed.setup_env(USER_EMAIL='billythefish@gmail.com', USER_ID='3', USER_IS_ADMIN='0', overwrite = True)
    attribute_4 = child_node.addAttrib(data_ndb.AttribDescription(text="test description 3"))
    attribute_5 = child_node.addAttrib(data_ndb.AttribName(text="test name 3"))

    child_node.setAttribActive(attribute_4.key)
    child_node.setAttribActive(attribute_5.key)

    attribute_0 = attribute_0.key.get()
    attribute_1 = attribute_1.key.get()
    attribute_2 = attribute_2.key.get()
    attribute_3 = attribute_3.key.get()
    attribute_4 = attribute_4.key.get()
    attribute_5 = attribute_5.key.get()

    self.assertEqual(False, attribute_0.active)
    self.assertEqual(False, attribute_1.active)
    self.assertEqual(False, attribute_2.active)
    self.assertEqual(False, attribute_3.active)
    self.assertEqual(True, attribute_4.active)
    self.assertEqual(True, attribute_5.active)


if __name__ == '__main__':
    unittest.main()
