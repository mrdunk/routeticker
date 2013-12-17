import unittest
from google.appengine.ext import testbed
from protorpc import messages

import data_dict


class DataListTestCase(unittest.TestCase):

  def setUp(self):
    # First, create an instance of the Testbed class.
    self.testbed = testbed.Testbed()
    # Then activate the testbed, which prepares the service stubs for use.
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testBooleanProperty(self):
    # Playing with fieldclasses.
    # https://developers.google.com/appengine/docs/python/tools/protorpc/messages/fieldclasses
    class Test(messages.Message):
        test = messages.BooleanField(1)
        test2 = messages.BooleanField(2, default=True)

    testInstance = Test()
    self.assertIs(testInstance.test, None)

    testInstance.test = True
    self.assertEqual(testInstance.test, True)

    testInstance.test = False
    self.assertEqual(testInstance.test, False)

    with self.assertRaises(messages.ValidationError):
        testInstance.test = "fish"

    self.assertEqual(testInstance.test2, True)

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

