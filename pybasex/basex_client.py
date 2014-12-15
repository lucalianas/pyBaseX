import requests
from functools import wraps

import errors as pbx_errors
import utils as pbx_utils
import utils.xml_utils as pbx_xml_utils


class BaseXClient(object):

    def __init__(self, url, default_database=None,
                 user=None, password=None, logger=None):
        self.url = url
        self.default_database = default_database
        self.user = user
        self.password = password
        self.logger = logger or pbx_utils.get_logger('basex_client')
        self.session = None

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return None

    def connect(self):
        self.logger.debug('Creating session')
        self.session = requests.Session()
        if self.user and self.password:
            self.session.auth = (self.user, self.password)

    def disconnect(self):
        self.logger.debug('Closing session')
        if self.session:
            self.session.close()
        self.session = None

    def errors_handler(f):
        @wraps(f)
        def wrapper(inst, *args, **kwargs):
            inst._check_connection()
            try:
                return f(inst, *args, **kwargs)
            except requests.ConnectionError, ce:
                inst.logger.exception(ce)
                raise pbx_errors.ConnectionError('Unable to connect to "%s"' % inst.url)
        return wrapper

    @property
    def connected(self):
        return not(self.session is None)

    def _check_connection(self):
        if not self.connected:
            raise pbx_errors.ConnectionClosedError('Connection closed')

    def _build_url(self, database, item=None):
        url = '/'.join([self.url, database])
        if item:
            url = '/'.join([url, item])
        return url

    def _resolve_database(self, database_name=None):
        db = database_name or self.default_database
        if db is None:
            raise pbx_errors.ConfigurationError('Missing default database')
        return db

    def _handle_wrong_url(self):
        msg = 'Unable to complete the request, "%s" is not a valid BaseX REST URL' % self.url
        self.logger.error(msg)
        raise pbx_errors.InvalidURLError(msg)

    # --- objects creation methods
    @errors_handler
    def create_database(self, database=None, overwrite=False):
        db = self._resolve_database(database)
        self.logger.info('Creating database "%s", overwrite is set to "%s"' % (db, overwrite))
        if overwrite:
            response = self.session.put(self._build_url(db))
        else:
            if db not in self.get_databases():
                response = self.session.put(self._build_url(db))
            else:
                raise pbx_errors.OverwriteError('Database "%s" already exists and overwrite disabled' % db)
        if response.status_code == requests.codes.not_found:
            self._handle_wrong_url()

    # --- objects retrieval methods
    @errors_handler
    def get_databases(self):
        response = self.session.get(self.url)
        if response.status_code == requests.codes.not_found:
            self._handle_wrong_url()
        results = pbx_xml_utils.str_to_xml(response.text)
        dbs_map = {}
        for ch in results.getchildren():
            dbs_map[ch.text] = {
                'size': ch.get('size'),
                'resources': ch.get('resources')
            }
        return dbs_map

    @errors_handler
    def get_resources(self, database=None):
        db = self._resolve_database(database)
        response = self.session.get(self._build_url(db))
        if response.status_code == requests.codes.not_found:
            # check for wrong URL
            _ = self.get_databases()
            raise pbx_errors.UnknownDatabaseError('Database "%s" does not exist' % db)
        results = pbx_xml_utils.str_to_xml(response.text)
        res_map = {}
        for ch in results.getchildren():
            res_map[ch.text] = {
                'type': ch.get('type'),
                'content-type': ch.get('content-type'),
                'size': ch.get('size')
            }
        return res_map

    # --- objects deletion methods
    @errors_handler
    def delete_database(self, database=None):
        db = self._resolve_database(database)
        response = self.session.delete(self._build_url(db))
        if response.status_code == requests.codes.not_found:
            # check for wrong URL
            _ = self.get_databases()
            raise pbx_errors.UnknownDatabaseError('Database "%s" does not exist' % db)
