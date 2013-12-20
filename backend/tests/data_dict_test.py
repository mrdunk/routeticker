import unittest
from google.appengine.ext import testbed
from protorpc import messages
from google.appengine.api import users

import data_dict


class PropertysTestCase(unittest.TestCase):

  def setUp(self):
    # First, create an instance of the Testbed class.
    self.testbed = testbed.Testbed()
    # Then activate the testbed, which prepares the service stubs for use.
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testBooleanProperty(self):
    class Test(object):
        test = data_dict.BooleanProperty()
        test2 = data_dict.BooleanProperty(default=True)

    testInstance = Test()
    self.assertIs(testInstance.test, None)

    testInstance.test = True
    self.assertEqual(testInstance.test, True)

    testInstance.test = False
    self.assertEqual(testInstance.test, False)

    with self.assertRaises(TypeError):
        testInstance.test = "fish"

    self.assertEqual(testInstance.test2, True)

  def testEnumProperty(self):
    class Test(object):
        test = data_dict.EnumProperty(data_dict.ContentType)
        test2 = data_dict.EnumProperty(data_dict.ContentType, default=data_dict.ContentType().ROOT)

    testInstance = Test()
    self.assertIs(testInstance.test, None)

    testInstance.test = data_dict.ContentType.ROOT
    self.assertEqual(testInstance.test, data_dict.ContentType.ROOT)

    testInstance.test = data_dict.ContentType.CLIMB
    self.assertEqual(testInstance.test, data_dict.ContentType.CLIMB)

    with self.assertRaises(TypeError):
        testInstance.test = "fish"

    self.assertEqual(testInstance.test2, data_dict.ContentType.ROOT)

    with self.assertRaises(TypeError):
        class Bad(object):
            test2 = data_dict.EnumProperty(data_dict.ContentType, default=74)

        badtestInstance = Bad()

  def testStringProperty(self):
    class Test(object):
        test = data_dict.StringProperty()
        test2 = data_dict.StringProperty(default="haggis, neeps and tatties")
        test3 = data_dict.StringProperty(repeated=True)

    testInstance = Test()
    self.assertIs(testInstance.test, None)

    testInstance.test = "sure thing."
    self.assertEqual(testInstance.test, "sure thing.")

    with self.assertRaises(TypeError):
        testInstance.test = ["spam", "spam", "spam", "spam"]

    self.assertEqual(testInstance.test2, "haggis, neeps and tatties")

    self.assertEqual(testInstance.test3, [])

    testInstance.test3 = "its the little things"
    self.assertEqual(testInstance.test3, ["its the little things"])

    testInstance.test3 = ["one great thing", "deserves another"]
    self.assertEqual(testInstance.test3, ["one great thing", "deserves another"])

    testInstance.test3.append("litte thing")
    self.assertEqual(testInstance.test3, ["one great thing", "deserves another", "litte thing"])

    testInstance.test3[1] = "looks like"
    self.assertEqual(testInstance.test3, ["one great thing", "looks like", "litte thing"])

    with self.assertRaises(TypeError):
        testInstance.test = 1

    with self.assertRaises(TypeError):
        testInstance.test3 = 1

    with self.assertRaises(TypeError):
        testInstance.test3 = [1]

    # http://stackoverflow.com/questions/20648366/strange-interaction-between-setitem-and-get
    testInstance.test3 = ["one great thing", "deserves another", "and another"]
    with self.assertRaises(TypeError):
        (testInstance.test3[0]) = 1


class DataStoreTestCase(unittest.TestCase):

  def setUp(self):
    data_dict.gKeyCounter = 0
    data_dict.gContainer.clear()

    # First, create an instance of the Testbed class.
    self.testbed = testbed.Testbed()
    # Then activate the testbed, which prepares the service stubs for use.
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testDataStoreCreateNoKey(self):
    peramiters = {"method1":"content 1", "method2":"content 2"}
    instance = data_dict.DataStore(**peramiters)

    peramiters = {"method1":"content 1", "method2":"content 2"}
    instance2 = data_dict.DataStore(**peramiters)
    
    self.assertIs(instance.key, None)
    self.assertEqual(instance.method1, "content 1")
    self.assertEqual(instance.method2, "content 2")

    self.assertEqual(data_dict.gKeyCounter, 0)
    self.assertEqual(len(data_dict.gContainer), 0)

    instance.put()
    instance2.put()

    self.assertEqual(data_dict.gKeyCounter, 2)
    self.assertEqual(len(data_dict.gContainer), 2)

  def testDataStoreCreateWithKey(self):
    peramiters = {"key":"test_key", "method1":"content 1", "method2":"content 2"}
    instance = data_dict.DataStore(**peramiters)
    
    self.assertEqual(instance.key, "test_key")
    self.assertEqual(instance.method1, "content 1")
    self.assertEqual(instance.method2, "content 2")

    self.assertEqual(data_dict.gKeyCounter, 0)
    self.assertEqual(len(data_dict.gContainer), 0)

    instance.put()

    self.assertEqual(data_dict.gKeyCounter, 0)
    self.assertEqual(len(data_dict.gContainer), 1)

    retreivedInstance = data_dict.DataStore(key="test_key").get()

    self.assertEqual(instance.key, retreivedInstance.key)
    self.assertEqual(instance.method1, retreivedInstance.method1)
    self.assertEqual(instance.method2, retreivedInstance.method2)

    retreivedInstance2 = data_dict.DataStore().get("test_key")

    self.assertEqual(instance.key, retreivedInstance2.key)
    self.assertEqual(instance.method1, retreivedInstance2.method1)
    self.assertEqual(instance.method2, retreivedInstance2.method2)

    with self.assertRaises(KeyError):
        retreivedInstance3 = data_dict.DataStore().get()
    
    retreivedInstance4 = data_dict.DataStore().get("missing_key")

    self.assertIs(retreivedInstance4, None)

  def testDataStoreByIndex(self):
    # Don't think we need to use the index methods but nice to know they work.
    peramiters = {"key":"test_key", "method1":"content 1", "method2":"content 2"}
    instance = data_dict.DataStore(**peramiters)

    data_dict.DataStore()["test_key"] = instance

    retreivedInstance = data_dict.DataStore()["test_key"]

    self.assertEqual(instance.key, retreivedInstance.key)
    self.assertEqual(instance.method1, retreivedInstance.method1)
    self.assertEqual(instance.method2, retreivedInstance.method2)

  def testDataStoreAsMixin(self):
    class Test(data_dict.DataStore):
      def fields(self):
        testBool = data_dict.BooleanProperty()
        testString = data_dict.StringProperty()
        testStringRepeated = data_dict.StringProperty(repeated=True)

    instance = Test()
    instance.testBool = True
    instance.testString = "song"
    instance.testStringRepeated = ["moma", "dont", "like"]
    instance.testStringRepeated.append("us all singing at the same time.")

    self.assertEqual(data_dict.gKeyCounter, 0)
    self.assertEqual(len(data_dict.gContainer), 0)

    instance.put()

    self.assertEqual(data_dict.gKeyCounter, 1)
    self.assertEqual(len(data_dict.gContainer), 1)

    retreived = Test(key=instance.key).get()
    self.assertEqual(retreived.testBool, True)
    self.assertEqual(retreived.testString, "song")
    self.assertEqual(len(retreived.testStringRepeated), 4)

    retreived2 = data_dict.DataStore(key=instance.key).get()
    self.assertEqual(retreived2.testBool, True)
    self.assertEqual(retreived2.testString, "song")
    self.assertEqual(len(retreived2.testStringRepeated), 4)


class DataListTestCase(unittest.TestCase):

  def setUp(self):
    data_dict.gKeyCounter = 0
    data_dict.gContainer.clear()

    # First, create an instance of the Testbed class.
    self.testbed = testbed.Testbed()
    # Then activate the testbed, which prepares the service stubs for use.
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testInitCreateRootNodeSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    rootNode = data_dict.Element(contType=data_dict.ContentType.ROOT)

    self.assertEqual(data_dict.gContainer[data_dict.root_key].contType, data_dict.ContentType.ROOT)
    self.assertEqual(data_dict.gContainer[data_dict.root_key].active, True)
    self.assertEqual(data_dict.gContainer[data_dict.root_key].menuParent, None)
    self.assertEqual(data_dict.gContainer[data_dict.root_key].menuChildren, [])
    self.assertEqual(len(data_dict.gContainer[data_dict.root_key].attributes), 1)

    attribKey = data_dict.gContainer[data_dict.root_key].attributes[0]
    self.assertEqual(data_dict.gContainer[attribKey].text, 'root')

    self.assertEqual(data_dict.gKeyCounter, 1)
    self.assertEqual(len(data_dict.gContainer), 2)
    self.assertIn(data_dict.root_key, data_dict.gContainer)
    self.assertIn(attribKey, data_dict.gContainer)

  def testInitCreateRootNodeTwice(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)

    self.assertIn(data_dict.root_key, data_dict.gContainer)
    self.assertEqual(len(data_dict.gContainer), 2)

    root_node2 = data_dict.Element(contType=data_dict.ContentType.ROOT)

    self.assertIn(data_dict.root_key, data_dict.gContainer)
    self.assertEqual(len(data_dict.gContainer), 2)

    self.assertEqual(root_node.key, root_node2.key)

  def testInitCreateRootNodeNotAdmin(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)

    self.assertNotIn(data_dict.root_key, data_dict.gContainer)
    self.assertEqual(len(data_dict.gContainer), 0)

  def testInitCreateRootNodeNotUser(self):
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)

    self.assertNotIn(data_dict.root_key, data_dict.gContainer)
    self.assertEqual(len(data_dict.gContainer), 0)

  def testInitCreateContainerSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)

    # Using root_node as parent.
    child_node = data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA)
    # re-read the root_node to update child keys.
    root_node = data_dict.Element(key=root_node.key)

    self.assertIn(data_dict.root_key, data_dict.gContainer)
    self.assertIn(child_node.key, data_dict.gContainer)
    self.assertEqual(len(data_dict.gContainer), 3)

    self.assertNotEqual(child_node.key, data_dict.root_key)

    self.assertIn(child_node.key, root_node.container.menuChildren)
    self.assertEqual(1, len(root_node.container.menuChildren))

    self.assertEqual(child_node.container.menuParent, root_node.key)

    self.assertEqual(data_dict.ContentType.AREA, child_node.container.contType)

  def testInitCreateContainerFromParentKeySucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)

    # Using root_node.key as parent.
    child_node = data_dict.Element(menuParent=root_node.key, contType=data_dict.ContentType.AREA)
    # re-read the root_node to update child keys.
    root_node = data_dict.Element(key=root_node.key)

    self.assertIn(data_dict.root_key, data_dict.gContainer)
    self.assertIn(child_node.key, data_dict.gContainer)
    self.assertEqual(len(data_dict.gContainer), 3)

    self.assertNotEqual(child_node.key, data_dict.root_key)

    self.assertIn(child_node.key, root_node.container.menuChildren)
    self.assertEqual(1, len(root_node.container.menuChildren))

    self.assertEqual(child_node.container.menuParent, root_node.key)

    self.assertEqual(data_dict.ContentType.AREA, child_node.container.contType)
 
  def testInitCreateContainerX10Flat(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)

    child_nodes = [data_dict.Element(menuParent=root_node.key, contType=data_dict.ContentType.AREA) for unused in range(10)]
    # re-read the root_node to update child keys.
    root_node = data_dict.Element(key=root_node.key)

    self.assertIn(data_dict.root_key, data_dict.gContainer)
    for child_node in child_nodes:
        self.assertIn(child_node.key, data_dict.gContainer)
        self.assertNotEqual(child_node.key, data_dict.root_key)

        self.assertIn(child_node.key, root_node.container.menuChildren)

        self.assertEqual(child_node.container.menuParent, root_node.key)
    self.assertEqual(10, len(root_node.container.menuChildren))

  def testInitCreateContainerX10Stacked(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)

    nodeHolder = root_node
    child_nodes = []
    for unused in range(10):
        # Each new node is a child of the previous.
        nodeHolder = data_dict.Element(menuParent=nodeHolder, contType=data_dict.ContentType.AREA)
        child_nodes.append(nodeHolder)

    # re-read the root_node to update child keys.
    root_node = data_dict.Element(key=root_node.key)

    self.assertIn(data_dict.root_key, data_dict.gContainer)
    self.assertEqual(1, len(root_node.container.menuChildren))

    lastChild = root_node
    for child_node in child_nodes:
        # Re-read child_node to ensure .menuChildren is uptodate.
        child_node = data_dict.Element(key=child_node.key)
        self.assertNotEqual(child_node.key, data_dict.root_key)
        self.assertNotEqual(child_node.key, lastChild.key)

        self.assertLessEqual(len(lastChild.container.menuChildren), 1)  # The last node has no children
        self.assertIn(child_node.key, lastChild.container.menuChildren)
        self.assertEqual(child_node.container.menuParent, lastChild.key)

        lastChild = child_node

    self.assertEqual(0, len(lastChild.container.menuChildren))  # The last node has no children

  def testInitCreateContainerNotUser(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    self.assertIsNone(users.get_current_user())
    self.assertEqual(data_dict.gKeyCounter, 1)
    self.assertEqual(len(data_dict.gContainer), 2)

    child_node = data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA)

    self.assertEqual(data_dict.gKeyCounter, 1)
    self.assertEqual(len(data_dict.gContainer), 2)

    self.assertIsNone(child_node.key)

  def testInitLookupOneSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_dict.Element(key=root_node.key)

    self.assertEqual(root_node.key, test_node.key)
    self.assertEqual(root_node.container, test_node.container)

  def testInitLookupOneFail(self):
    badKey1 = 'earwax'
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)

    test_node = data_dict.Element(key=badKey1)
    self.assertIs(test_node.key, None)

  def testInitLookupManySucess(self):
    NUMBER = 10
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA).key for unused in range(NUMBER)]

    self.assertEqual(len(child_nodes_keys), NUMBER)

    test_lookup = data_dict.Element(key=child_nodes_keys)
    self.assertEqual(len(test_lookup.keys), NUMBER)
    self.assertEqual(len(test_lookup.containers), NUMBER)

    NUMBER = 3
    child_nodes_keys = child_nodes_keys[:NUMBER]
    test_lookup = data_dict.Element(key=child_nodes_keys)
    self.assertEqual(len(test_lookup.keys), NUMBER)
    self.assertEqual(len(test_lookup.containers), NUMBER)

  def testInitLookupManyFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA).key for unused in range(10)]

    child_nodes_keys[0] = None

    test_lookup = data_dict.Element(key=child_nodes_keys)
    self.assertEqual(len(test_lookup.keys), 9)
    self.assertEqual(len(test_lookup.containers), 9)

    child_nodes_keys[0] = child_nodes_keys[1]
    test_lookup = data_dict.Element(key=child_nodes_keys)
    self.assertEqual(len(test_lookup.keys), 9)
    self.assertEqual(len(test_lookup.containers), 9)

  def testInitLookupLimitedSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_dict.Element(key=root_node.key, active=True, contType=data_dict.ContentType.ROOT)

    self.assertEqual(root_node.key, test_node.key)
    self.assertEqual(root_node.container, test_node.container)

  def testInitLookupLimitedListSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_dict.Element(key=root_node.key, active=True, contType=[data_dict.ContentType.ROOT, data_dict.ContentType.AREA])

    self.assertEqual(root_node.key, test_node.key)
    self.assertEqual(root_node.container, test_node.container)

  def testInitLookupLimitedFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_dict.Element(key=root_node.key, contType=data_dict.ContentType.AREA)

    self.assertNotEqual(root_node.key, test_node.key)
    self.assertNotEqual(root_node.container, test_node.container)

    test_node = data_dict.Element(key=root_node.key, active=False)

    self.assertNotEqual(root_node.key, test_node.key)
    self.assertNotEqual(root_node.container, test_node.container)

  def testInitLookupLimitedListFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL=None, USER_ID='0', USER_IS_ADMIN='0', overwrite = True)
    test_node = data_dict.Element(key=root_node.key, contType=[data_dict.ContentType.AREA, data_dict.ContentType.CRAG])

    self.assertNotEqual(root_node.key, test_node.key)
    self.assertNotEqual(root_node.container, test_node.container)

  def testInitLookupManyLimitedSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA).key for unused in range(10)]

    test_lookup = data_dict.Element(key=child_nodes_keys, active=False, contType=data_dict.ContentType.AREA)
    self.assertEqual(len(test_lookup.keys), 10)
    self.assertEqual(len(test_lookup.containers), 10)

  def testInitLookupManyLimitedListSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA).key for unused in range(10)]

    test_lookup = data_dict.Element(key=child_nodes_keys, active=False, contType=[data_dict.ContentType.AREA, data_dict.ContentType.CRAG])
    self.assertEqual(len(test_lookup.keys), 10)
    self.assertEqual(len(test_lookup.containers), 10)

  def testInitLookupManyLimitedFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA).key for unused in range(10)]

    test_lookup = data_dict.Element(key=child_nodes_keys, contType=data_dict.ContentType.CRAG)
    self.assertEqual(len(test_lookup.keys), 0)
    self.assertEqual(len(test_lookup.containers), 0)

    test_lookup = data_dict.Element(key=child_nodes_keys, active=True)
    self.assertEqual(len(test_lookup.keys), 0)
    self.assertEqual(len(test_lookup.containers), 0)

  def testInitLookupManyLimitedListFail(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA).key for unused in range(10)]

    test_lookup = data_dict.Element(key=child_nodes_keys, contType=[data_dict.ContentType.ROOT, data_dict.ContentType.CRAG])
    self.assertEqual(len(test_lookup.keys), 0)
    self.assertEqual(len(test_lookup.containers), 0)

  def testInitLookupManyLimitedListPartialSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_nodes_keys = [data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA).key for unused in range(10)]
    child_nodes_keys.append(data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.CRAG).key)
    child_nodes_keys.append(data_dict.Element(menuParent=root_node, active=True, contType=data_dict.ContentType.AREA).key)

    test_lookup = data_dict.Element(key=child_nodes_keys, contType=data_dict.ContentType.CRAG)
    self.assertEqual(len(test_lookup.keys), 1)
    self.assertEqual(len(test_lookup.containers), 1)

    test_lookup = data_dict.Element(key=child_nodes_keys, active=True)
    self.assertEqual(len(test_lookup.keys), 1)
    self.assertEqual(len(test_lookup.containers), 1)

  def testAddAttribSucess(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    root_node = data_dict.Element(contType=data_dict.ContentType.ROOT)
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='0', overwrite = True)
    child_node = data_dict.Element(menuParent=root_node, contType=data_dict.ContentType.AREA)

    child_node.addAttrib(data_dict.AttribName(text="test name"))
    child_node.addAttrib(data_dict.AttribDescription(text="test description"))

    self.assertEqual(1, data_dict.AttribName.query(ancestor=root_node.key).count(10))
    self.assertEqual(1, data_dict.AttribName.query(ancestor=child_node.key).count(10))

    self.assertEqual(2, len(child_node.container.attributes))

    atribs_name = data_dict.AttribName.query(ancestor=child_node.key).fetch(10)
    self.assertEqual(1, len(atribs_name))
    self.assertIn(atribs_name[0].key, child_node.container.attributes)



if __name__ == '__main__':
    unittest.main()

