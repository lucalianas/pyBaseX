import os, unittest, sys
from lxml.etree import fromstring

from pybasex import BaseXClient

BASEX_URL = os.getenv('BASEX_BASE_URL')


class TestBaseXClient(unittest.TestCase):

    def __init__(self, label):
        super(TestBaseXClient, self).__init__(label)

    def setUp(self):
        if BASEX_URL is None:
            sys.exit('ERROR: no base URL for BaseX database provided')

    def test_database(self):
        db_name = 'test_basex'
        with BaseXClient(BASEX_URL, default_database=db_name) as bx_client:
            bx_client.create_database()
            dbs = bx_client.get_databases()
            self.assertIn(db_name, dbs.keys())
            bx_client.delete_database()
            dbs = bx_client.get_databases()
            self.assertEqual(len(dbs), 0)

    def test_document(self):
        db_name = 'test_basex'
        doc_id = 'test_document_001'
        str_doc = '<root><leaf id=\'1\'/><leaf id=\'2\'/><leaf id=\'3\'/></root>'
        with BaseXClient(BASEX_URL, default_database=db_name) as bx_client:
            bx_client.create_database()
            bx_client.add_document(fromstring(str_doc), doc_id)
            resources = bx_client.get_resources()
            self.assertIn(doc_id, resources.keys())
            doc = bx_client.get_document(doc_id)
            self.assertEqual(doc.tag, 'root')
            for ch in doc.getchildren():
                self.assertEqual(ch.tag, 'leaf')
            bx_client.delete_database()
            dbs = bx_client.get_databases()
            self.assertEqual(len(dbs), 0)


def suite():
    tests_suite = unittest.TestSuite()
    tests_suite.addTest(TestBaseXClient('test_database'))
    tests_suite.addTest(TestBaseXClient('test_document'))
    return tests_suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())