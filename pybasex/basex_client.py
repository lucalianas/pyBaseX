import requests
from functools import wraps
from uuid import uuid4

import errors as pbx_errors
import utils as pbx_utils
import utils.xml_utils as pbx_xml_utils
from fragments import build_query_fragment


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

    def _check_url(self, database):
        # check for invalid BaseX URL
        _ = self.get_databases()
        # URL is a valid one, database does not exist
        raise pbx_errors.UnknownDatabaseError('Database "%s" does not exist' % database)

    def _check_response_code(self, response, not_found_callback=None, not_found_params=None,
                             bad_request_excp=None, bad_request_msg=None):
        if response.status_code == requests.codes.unauthorized:
            if not self.user or not self.password:
                msg = 'Authentication required, provide username and password'
            else:
                msg = 'Access denied for user "%s" with password "%s"' % (self.user, self.password)
            raise pbx_errors.AuthenticationError(msg)
        if response.status_code == requests.codes.not_found:
            if not_found_callback:
                not_found_callback(*not_found_params or None)
        if response.status_code == requests.codes.bad:
            raise bad_request_excp(bad_request_msg + response.text.replace('\n', ' '))
        return response

    def _check_response_tag(self, response_xml):
        if not response_xml.tag.startswith('{http://basex.org/rest}database'):
            self._handle_wrong_url()

    def _wrap_results(self, res_text):
        res_text = '<results>{0}</results>'.format(res_text)
        return pbx_xml_utils.str_to_xml(res_text)

    def _rollback(self, doc_ids, database=None):
        for d_id in doc_ids:
            self.delete_document(d_id, database)

    def _get_document_id(self):
        return uuid4().hex

    # --- objects creation methods
    @errors_handler
    def create_database(self, database=None):
        db = self._resolve_database(database)
        self.logger.debug('Creating database "%s"' % db)
        if db not in self.get_databases():
            response = self._check_response_code(
                response=self.session.put(self._build_url(db)),
                not_found_callback=self._handle_wrong_url
            )
        else:
            raise pbx_errors.OverwriteError('Database "%s" already exists' % db)
        self.logger.info('RESPONSE (status code %d): %s', response.status_code, response.text)

    def _save_document(self, xml_doc, document_id, database):
        response = self._check_response_code(
            response=self.session.put(
                self._build_url(database, document_id), xml_doc
            )
        )
        return response

    @errors_handler
    def add_document(self, xml_doc, document_id=None, database=None):
        document_id = document_id or self._get_document_id()
        db = self._resolve_database(database)
        if document_id in self.get_resources(db):
            raise pbx_errors.OverwriteError('A document with ID "%s" already exists in database "%s"' %
                                            (document_id, db))
        xml_doc = pbx_xml_utils.xml_to_str(xml_doc)
        self.logger.debug('Saving document %s' % xml_doc)
        response = self._save_document(xml_doc, document_id, db)
        self.logger.info('RESPONSE (status code %d): %s', response.status_code, response.text)
        return document_id

    @errors_handler
    def add_documents(self, documents, database=None, skip_duplicated=False):
        db = self._resolve_database(database)
        saved_ids = list()
        duplicated_ids = list()
        if isinstance(documents, list) or isinstance(documents, set):
            documents = {self._get_document_id(): doc for doc in documents}
        elif isinstance(documents, dict):
            pass
        else:
            raise TypeError('%s is not a valid type for "documents" field' % type(documents))
        known_ids = self.get_resources(db)
        for doc_id in documents.keys():
            if doc_id in known_ids:
                duplicated_ids.append(doc_id)
        if skip_duplicated:
            for dupl_id in duplicated_ids:
                documents.pop(dupl_id)
        else:
            if len(duplicated_ids) > 0:
                raise pbx_errors.OverwriteError('IDs %r already used in database %s' %
                                                (duplicated_ids, db))
        self.logger.info('Saving %d documents to database %s', len(documents), db)
        try:
            for doc_id, doc in documents.iteritems():
                response = self._save_document(pbx_xml_utils.xml_to_str(doc), doc_id, db)
                saved_ids.append(doc_id)
                self.logger.debug('RESPONSE (status code %d): %s', response.status_code, response.text)
        except Exception, e:
            self.logger.critical('An error occurred, performing rollback')
            self._rollback(saved_ids, db)
            raise e
        self.logger.info('%d documents saved, %d duplicated found',
                         len(saved_ids), len(duplicated_ids))
        return saved_ids, duplicated_ids

    # --- objects retrieval methods
    @errors_handler
    def get_databases(self):
        response = self._check_response_code(
            response=self.session.get(self.url),
            not_found_callback=self._handle_wrong_url
        )
        results = pbx_xml_utils.str_to_xml(response.text)
        self._check_response_tag(results)
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
        response = self._check_response_code(
            response=self.session.get(self._build_url(db)),
            not_found_callback=self._check_url,
            not_found_params=(db,)
        )
        results = pbx_xml_utils.str_to_xml(response.text)
        self._check_response_tag(results)
        res_map = {}
        for ch in results.getchildren():
            res_map[ch.text] = {
                'type': ch.get('type'),
                'content-type': ch.get('content-type'),
                'size': ch.get('size')
            }
        return res_map

    @errors_handler
    def get_document(self, document_id, database=None):
        db = self._resolve_database(database)
        response = self._check_response_code(
            response=self.session.get(self._build_url(db, document_id)),
            not_found_callback=self._check_url,
            not_found_params=(db,)
        )
        result = pbx_xml_utils.str_to_xml(response.text)
        if result.tag.startswith('{http://basex.org/rest}database') and int(result.get('resources')) == 0:
            self.logger.info('There is not document with ID "%s" in database "%s"' % (document_id, db))
            return None
        else:
            return result

    @errors_handler
    def get_documents(self, database=None):
        db = self._resolve_database(database)
        res = self.get_resources(db)
        docs = {doc_id: self.get_document(doc_id, db) for doc_id in res.keys()}
        return docs

    # --- objects deletion methods
    @errors_handler
    def delete_database(self, database=None):
        db = self._resolve_database(database)
        response = self._check_response_code(
            response=self.session.delete(self._build_url(db)),
            not_found_callback=self._check_url,
            not_found_params=(db,)
        )

    @errors_handler
    def delete_document(self, document_id, database=None):
        db = self._resolve_database(database)
        response = self._check_response_code(
            response=self.session.delete(self._build_url(db, document_id)),
            not_found_callback=self._check_url,
            not_found_params=(db,)
        )

    # --- commands\queries execution methods
    @errors_handler
    def execute_query(self, query, database=None):
        db = self._resolve_database(database)
        q_frag = build_query_fragment(query)
        response = self._check_response_code(
            response=self.session.post(self._build_url(db),
                                       pbx_utils.xml_utils.xml_to_str(q_frag)),
            not_found_callback=self._check_url,
            not_found_params=(db,),
            bad_request_excp=pbx_errors.QueryError,
            bad_request_msg='Query error: '
        )
        return self._wrap_results(response.text)
