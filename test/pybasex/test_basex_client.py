import os, unittest, sys

from pybasex import BaseXClient

BASEX_URL = os.getenv('BASEX_BASE_URL')


class TestBaseXClient(unittest.TestCase):

    def __init__(self, label):
        super(TestBaseXClient, self).__init__(label)

    def setUp(self):
        if BASEX_URL is None:
            sys.exit('ERROR: no base URL for BaseX database provided')

    def test_create_database(self):
        db_name = 'test_basex'
        with BaseXClient(BASEX_URL, default_database=db_name) as bx_client:
            bx_client.create_database()
            dbs = bx_client.get_databases()
            self.assertEqual(dbs.keys(), [db_name])
            bx_client.delete_database()
            dbs = bx_client.get_databases()
            self.assertEqual(len(dbs), 0)


def suite():
    tests_suite = unittest.TestSuite()
    tests_suite.addTest(TestBaseXClient('test_create_database'))
    return tests_suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())