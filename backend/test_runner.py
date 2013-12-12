""" Based on: http://martinsikora.com/unit-testing-gae-apps-in-python """
import os
import sys
import fnmatch
import unittest
import webapp2
import importlib
from time import clock
 
class RunUnitTests(webapp2.RequestHandler):
 
    def get(self):        
        self.response.headers['Content-Type'] = 'text/plain'
 
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        testCases = self._findTestCases()
        #print testCases
 
        for testCase in testCases:
            suite.addTests(loader.loadTestsFromName(testCase))
 
        startTime = clock()
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        stopTime = clock()
 
        self.response.out.write(('Test cases (%d):\n' % len(testCases)) + '\n'.join(map(repr, testCases)) + '\n\n')
        self._printTestResultsGroup(result, 'errors')
        self._printTestResultsGroup(result, 'failures')
 
        self.response.out.write('Total tests: %d\n' % result.testsRun)
        self.response.out.write('Status: %s (%s ms)\n' % ('OK' if result.wasSuccessful() else 'FAILED', (stopTime - startTime) * 1000))
 
    def _findTestCases(self):
        testCases = []
        for root, dirnames, filenames in os.walk('.'):
            for filename in fnmatch.filter(filenames, '*_test.py'):
                classPath = os.path.splitext(os.path.join(root, filename)[2:])[0].replace('/', '.')
                testCases.append(classPath)
 
        return testCases        
 
    def _printTestResultsGroup(self, result, name):
        list = getattr(result, name)
        if len(list):
            self.response.out.write("%s (%d):\n" % (name.capitalize(), len(list)))
            for item in list:
                self.response.out.write('%s\n' % item[0])
            self.response.out.write('\n')

application = webapp2.WSGIApplication([
    ('/test', RunUnitTests),
], debug=True)

