import unittest
from google.appengine.ext import testbed
from protorpc import messages

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
#        test = data_dict.StringProperty()
#        test2 = data_dict.StringProperty(default="haggis, neeps and tatties")
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

    # WTF? http://stackoverflow.com/questions/20648366/strange-interaction-between-setitem-and-get
    #testInstance.test3 = ["one great thing", "deserves another", "and another"]
    #with self.assertRaises(TypeError):
    #    (testInstance.test3[0]) = 1


class DataListTestCase(unittest.TestCase):

  def setUp(self):
    # First, create an instance of the Testbed class.
    self.testbed = testbed.Testbed()
    # Then activate the testbed, which prepares the service stubs for use.
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testElement(self):
    self.testbed.setup_env(USER_EMAIL='usermail@gmail.com', USER_ID='1', USER_IS_ADMIN='1', overwrite = True)
    rootNode = data_dict.Element(contType=data_dict.ContentType.ROOT)

    self.assertEqual(data_dict.gContainer[data_dict.root_key].contType, data_dict.ContentType.ROOT)
    self.assertEqual(data_dict.gContainer[data_dict.root_key].active, True)
    self.assertEqual(data_dict.gContainer[data_dict.root_key].menuParent, None)
    self.assertEqual(data_dict.gContainer[data_dict.root_key].menuChildren, [])
    self.assertEqual(len(data_dict.gContainer[data_dict.root_key].attributes), 1)

    attribKey = data_dict.gContainer[data_dict.root_key].attributes[0]
    self.assertEqual(data_dict.gContainer[attribKey].text, 'root')


if __name__ == '__main__':
    unittest.main()

