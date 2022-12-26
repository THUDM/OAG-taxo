import elasticsearch.exceptions
from pymongo import MongoClient
# from elasticsearch5 import Elasticsearch, exceptions
from elasticsearch import Elasticsearch

"""
class MongoDBClientKexie(object):
    def __init__(self, host=settings.MONGO_HOST_kexie, port=settings.MONGO_PORT_kexie,
                 db_name=settings.MONGO_DBNAME_kexie, user=settings.MONGO_USERNAME_kexie,
                 password=settings.MONGO_PASSWORD_kexie):
        self.client = MongoClient(host, port, unicode_decode_error_handler='ignore')
        self.db = self.client.get_database(db_name, codec_options=options)
        if password is not None:
            self.db.authenticate(user, password)
        self.aminer_pub_col = self.db["publication_dupl"]
        self.aminer_person_col = self.db["person"]
        self.pub_relation_col = self.db["pub_relation"]"""


"""class MongoDBClient106(object):
    def __init__(self, host=settings.MONGO_HOST_106, port=settings.MONGO_PORT_106, db_name=settings.MONGO_DBNAME_106,
                 user=settings.MONGO_USERNAME_106, password=settings.MONGO_PASSWORD_106):
        # self.client = MongoClient(host, port, unicode_decode_error_handler='ignore')
        self.client = MongoClient("{}:{}".format(host, port), username=user, password=password, authSource=db_name, authMechanism="SCRAM-SHA-1")
        self.db = self.client.get_database(db_name, codec_options=options)
        # if password is not None:
        #     self.db.authenticate(user, password)
        self.paper_source_trace_col = self.db["paper_source_trace_2022"]
        self.aminer_pub_col = self.db["publication_dupl"]

"""
class ESClient(object):
    def __init__(self):
        self.es = Elasticsearch(hosts=['166.111.7.106'], port=9200, timeout=60,
                                http_auth=('nekol', 'kegGER123'))
        self.index = 'cs_paper_full'
        self.initialize()

    @staticmethod
    def lower(string):
        if not string:
            return ''
        else:
            return string.lower()

    def initialize(self):
        cur_prop = {'properties': {'title': {'type': 'text'}}}
        try:
            self.es.indices.create("cs_paper_full")
        except:
            pass

        self.es.indices.put_mapping(index='cs_paper_full',doc_type='cs_paper_full', body=cur_prop)
        print("set up mapping...")

    def add_document(self, document: dict, index='cs_paper_full'):
        data = {'title': self.lower(document.get('title')), 'abstract': self.lower(document.get('abstract'))}
        self.es.create(index=index, doc_type=index, id=str(document.get('_id')), body=data)

    def delete_document(self, index, _id):
        result = self.es.delete(index=index, doc_type=index, id=_id)
        if result.get('result') != 'deleted':
            print("deletion failed!")

    def check_id_exists(self, pid: str, index='cs_paper_full'):
        return self.es.exists(index, id=pid)

    def search(self, key_words: str, index='cs_paper_full'):
        dsl = {'query': {'match': {"title": key_words}}}
        result = self.es.search(index=index, doc_type=index, body=dsl)
        return result.get('hits').get('hits')


def each_chunk(stream, separator):
    buffer = ''
    while True:  # until EOF
        chunk = stream.read(4096)  # I propose 4096 or so
        if not chunk:  # EOF?
            yield buffer
            break
        buffer += chunk
        while True:  # until no separator is found
            try:
                part, buffer = buffer.split(separator, 1)

            except ValueError:
                break
            else:
                yield part+'}'


if __name__ == "__main__":
    pass
