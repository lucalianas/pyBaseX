import os, unittest, sys
from lxml.etree import fromstring, Element, SubElement
from collections import Counter

from pybasex import BaseXClient
from pybasex.utils import get_logger

BASEX_URL = os.getenv('BASEX_BASE_URL')


class TestBaseXClient(unittest.TestCase):

    def __init__(self, label):
        super(TestBaseXClient, self).__init__(label)

    def _build_documents(self, pool_size):
        documents = []
        for x in xrange(0, pool_size):
            tree = Element('tree')
            tree.set('id', '%s' % (x+1))
            leaf = SubElement(tree, 'leaf')
            leaf.set('even', '%s' % (x % 2))
            documents.append(tree)
        return documents

    def setUp(self):
        if BASEX_URL is None:
            sys.exit('ERROR: no base URL for BaseX database provided')

    def test_database(self):
        db_name = 'test_basex'
        with BaseXClient(BASEX_URL, default_database=db_name,
                         logger=get_logger('test', silent=True)) as bx_client:
            bx_client.create_database()
            dbs = bx_client.get_databases()
            self.assertIn(db_name, dbs.keys())
            bx_client.delete_database()
            dbs = bx_client.get_databases()
            self.assertEqual(len(dbs), 0)

    def test_document(self):
        db_name = 'test_basex'
        doc_id = 'test_document_001'
        str_doc = '<tree><leaf id=\'1\'/><leaf id=\'2\'/><leaf id=\'3\'/></tree>'
        with BaseXClient(BASEX_URL, default_database=db_name,
                         logger=get_logger('test', silent=True)) as bx_client:
            bx_client.create_database()
            bx_client.add_document(fromstring(str_doc), doc_id)
            resources = bx_client.get_resources()
            self.assertIn(doc_id, resources.keys())
            doc = bx_client.get_document(doc_id)
            self.assertEqual(doc.tag, 'tree')
            for ch in doc.getchildren():
                self.assertEqual(ch.tag, 'leaf')
            bx_client.delete_database()
            dbs = bx_client.get_databases()
            self.assertEqual(len(dbs), 0)

    def test_xpath(self):
        db_name = 'test_basex'
        doc_id_pattern = 'test_document_%03d'
        ct = Counter()
        with BaseXClient(BASEX_URL, default_database=db_name,
                         logger=get_logger('test', silent=True)) as bx_client:
            bx_client.create_database()
            for doc in self._build_documents(20):
                bx_client.add_document(doc, doc_id_pattern % int(doc.get('id')))
                if int(doc.find('leaf').get('even')):
                    ct['even'] += 1
                else:
                    ct['odd'] += 1
            results = bx_client.execute_query('/tree//leaf[@even="1"]/ancestor-or-self::leaf')
            self.assertEqual(len(results.getchildren()), ct['even'])
            for ch in results.getchildren():
                self.assertEqual(ch.tag, 'leaf')
            results = bx_client.execute_query('/tree//leaf[@even="0"]/ancestor-or-self::leaf')
            self.assertEqual(len(results.getchildren()), ct['odd'])
            for ch in results.getchildren():
                self.assertEqual(ch.tag, 'leaf')
            bx_client.delete_database()


def suite():
    tests_suite = unittest.TestSuite()
    tests_suite.addTest(TestBaseXClient('test_database'))
    tests_suite.addTest(TestBaseXClient('test_document'))
    tests_suite.addTest(TestBaseXClient('test_xpath'))
    return tests_suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())