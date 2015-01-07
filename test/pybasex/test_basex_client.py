import os, unittest, sys
from lxml.etree import fromstring, Element, SubElement, _Element
from collections import Counter

from pybasex import BaseXClient
from pybasex.utils import get_logger
import pybasex.errors as pbx_errors


class TestBaseXClient(unittest.TestCase):

    def __init__(self, label):
        super(TestBaseXClient, self).__init__(label)
        self.db_name = 'test_basex'
        self.basex_url = os.getenv('BASEX_BASE_URL')
        self.basex_user = os.getenv('BASEX_USER')
        self.basex_passwd = os.getenv('BASEX_PASSWD')

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
        if self.basex_url is None:
            sys.exit('ERROR: no base URL for BaseX database provided')

    def test_connect(self):
        c = BaseXClient(self.basex_url, self.db_name, self.basex_user,
                        self.basex_passwd)
        with self.assertRaises(pbx_errors.ConnectionClosedError):
            c.get_databases()
        self.assertFalse(c.connected)
        c.connect()
        self.assertTrue(c.connected)
        c.disconnect()
        self.assertFalse(c.connected)

    def test_context_manager(self):
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
                         logger=get_logger('test', silent=True)) as bx_client:
            self.assertTrue(bx_client.connected)
        self.assertFalse(bx_client.connected)

    def test_connection_error(self):
        with BaseXClient('http://localhost:0', logger=get_logger('test', silent=True)) as bx_client:
            with self.assertRaises(pbx_errors.ConnectionError):
                bx_client.get_databases()

    def test_create_database(self):
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
                         logger=get_logger('test', silent=True)) as bx_client:
            bx_client.create_database()
            dbs = bx_client.get_databases()
            self.assertIn(self.db_name, dbs.keys())
            with self.assertRaises(pbx_errors.OverwriteError):
                bx_client.create_database()
            bx_client.delete_database()

    def test_delete_database(self):
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
                         logger=get_logger('test', silent=True)) as bx_client:
            with self.assertRaises(pbx_errors.UnknownDatabaseError):
                bx_client.delete_database('test_fake')
            bx_client.create_database()
            bx_client.delete_database()

    def test_add_document(self):
        doc_id = 'test_document_001'
        str_doc = '<tree><leaf id=\'1\'/><leaf id=\'2\'/><leaf id=\'3\'/></tree>'
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
                         logger=get_logger('test', silent=True)) as bx_client:
            bx_client.create_database()
            bx_client.add_document(fromstring(str_doc), doc_id)
            res = bx_client.get_resources()
            self.assertIn(doc_id, res.keys())
            with self.assertRaises(pbx_errors.OverwriteError):
                bx_client.add_document(fromstring(str_doc), doc_id)
            with self.assertRaises(pbx_errors.UnknownDatabaseError):
                bx_client.add_document(fromstring(str_doc), doc_id,
                                       database='test_fake')
            bx_client.delete_database()

    def test_get_document(self):
        doc_id = 'test_document_001'
        str_doc = '<tree><leaf id=\'1\'/><leaf id=\'2\'/><leaf id=\'3\'/></tree>'
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
                         logger=get_logger('test', silent=True)) as bx_client:
            bx_client.create_database()
            bx_client.add_document(fromstring(str_doc), doc_id)
            doc = bx_client.get_document(doc_id)
            self.assertIsInstance(doc, _Element)
            self.assertEqual(doc.tag, 'tree')
            for ch in doc.getchildren():
                self.assertEqual(ch.tag, 'leaf')
            doc = bx_client.get_document('test_document_002')
            self.assertIsNone(doc)
            with self.assertRaises(pbx_errors.UnknownDatabaseError):
                bx_client.get_document(doc_id, database='test_fake')
            bx_client.delete_database()

    def test_delete_document(self):
        doc_id = 'test_document_001'
        str_doc = '<tree><leaf id=\'1\'/><leaf id=\'2\'/><leaf id=\'3\'/></tree>'
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
                         logger=get_logger('test', silent=True)) as bx_client:
            bx_client.create_database()
            bx_client.add_document(fromstring(str_doc), doc_id)
            doc = bx_client.get_document(doc_id)
            self.assertIsNotNone(doc)
            bx_client.delete_document(doc_id)
            doc = bx_client.get_document(doc_id)
            self.assertIsNone(doc)
            with self.assertRaises(pbx_errors.UnknownDatabaseError):
                bx_client.delete_document(doc_id, database='test_fake')
            bx_client.delete_database()

    def test_xpath(self):
        doc_id_pattern = 'test_document_%03d'
        ct = Counter()
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
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
            with self.assertRaises(pbx_errors.QueryError):
                bx_client.execute_query('/tree//leaf[@even="0"]/ancstr-or-self::leaf')
            with self.assertRaises(pbx_errors.UnknownDatabaseError):
                bx_client.execute_query('/tree//leaf[@even="0"]/ancestor-or-self::leaf',
                                        database='test_fake')
            bx_client.delete_database()


def suite():
    tests_suite = unittest.TestSuite()
    tests_suite.addTest(TestBaseXClient('test_connect'))
    tests_suite.addTest(TestBaseXClient('test_context_manager'))
    tests_suite.addTest(TestBaseXClient('test_connection_error'))
    tests_suite.addTest(TestBaseXClient('test_create_database'))
    tests_suite.addTest(TestBaseXClient('test_delete_database'))
    tests_suite.addTest(TestBaseXClient('test_add_document'))
    tests_suite.addTest(TestBaseXClient('test_get_document'))
    tests_suite.addTest(TestBaseXClient('test_delete_document'))
    tests_suite.addTest(TestBaseXClient('test_xpath'))
    return tests_suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())