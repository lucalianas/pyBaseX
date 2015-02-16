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

    def tearDown(self):
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
                         logger=get_logger('test', silent=True)) as bx_client:
            try:
                bx_client.delete_database()
            except pbx_errors.UnknownDatabaseError:
                # avoid errors if database was already deleted
                pass

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
        with BaseXClient('http://localhost:1', logger=get_logger('test', silent=True)) as bx_client:
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
            _id = bx_client.add_document(fromstring(str_doc))
            res = bx_client.get_resources()
            self.assertIn(_id, res.keys())
            _id = bx_client.add_document(fromstring(str_doc), doc_id)
            self.assertEqual(_id, doc_id)
            res = bx_client.get_resources()
            self.assertIn(_id, res.keys())
            with self.assertRaises(pbx_errors.OverwriteError):
                bx_client.add_document(fromstring(str_doc), doc_id)
            with self.assertRaises(pbx_errors.UnknownDatabaseError):
                bx_client.add_document(fromstring(str_doc), doc_id,
                                       database='test_fake')

    def test_add_documents(self):
        doc_id_template = 'test_document_%03d'
        str_doc_template = '<tree id=\'%d\'><leaf id=\'1\'/><leaf id=\'2\'/><leaf id=\'3\'/></tree>'
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
                         logger=get_logger('test', silent=True)) as bx_client:
            bx_client.create_database()
            docs = list()
            for x in xrange(0, 10):
                docs.append(fromstring(str_doc_template % x))
            ids, dupl = bx_client.add_documents(docs)
            self.assertEqual(len(ids), 10)
            self.assertEqual(len(dupl), 0)
            ids, dupl = bx_client.add_documents(set(docs))
            self.assertEqual(len(ids), 10)
            self.assertEqual(len(dupl), 0)
            self.assertEqual(len(bx_client.get_resources()), 20)
            docs = {doc_id_template % x: fromstring(str_doc_template % x)
                    for x in xrange(0, 10)}
            ids, dupl = bx_client.add_documents(docs)
            self.assertEqual(len(ids), 10)
            self.assertEqual(len(dupl), 0)
            self.assertEqual(sorted(ids), sorted(docs.keys()))
            self.assertEqual(len(bx_client.get_resources()), 30)
            for x in xrange(20, 30):
                docs[doc_id_template % x] = fromstring(str_doc_template % x)
            with self.assertRaises(pbx_errors.OverwriteError):
                bx_client.add_documents(docs)
            self.assertEqual(len(bx_client.get_resources()), 30)
            ids, dupl = bx_client.add_documents(docs, skip_duplicated=True)
            self.assertEqual(len(ids), 10)
            self.assertEqual(len(dupl), 10)
            self.assertEqual(len(bx_client.get_resources()), 40)

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

    def test_get_documents(self):
        str_doc = '<tree><leaf id=\'1\'/><leaf id=\'2\'/><leaf id=\'3\'/></tree>'
        with BaseXClient(self.basex_url, default_database=self.db_name,
                         user=self.basex_user, password=self.basex_passwd,
                         logger=get_logger('test', silent=True)) as bx_client:
            bx_client.create_database()
            docs = [fromstring(str_doc) for x in xrange(0, 10)]
            _, _ = bx_client.add_documents(docs)
            docs = bx_client.get_documents()
            self.assertEqual(sorted(docs.keys()), sorted(bx_client.get_resources().keys()))

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


def suite():
    tests_suite = unittest.TestSuite()
    tests_suite.addTest(TestBaseXClient('test_connect'))
    tests_suite.addTest(TestBaseXClient('test_context_manager'))
    tests_suite.addTest(TestBaseXClient('test_connection_error'))
    tests_suite.addTest(TestBaseXClient('test_create_database'))
    tests_suite.addTest(TestBaseXClient('test_delete_database'))
    tests_suite.addTest(TestBaseXClient('test_add_document'))
    tests_suite.addTest(TestBaseXClient('test_add_documents'))
    tests_suite.addTest(TestBaseXClient('test_get_document'))
    tests_suite.addTest(TestBaseXClient('test_get_documents'))
    tests_suite.addTest(TestBaseXClient('test_delete_document'))
    tests_suite.addTest(TestBaseXClient('test_xpath'))
    return tests_suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())