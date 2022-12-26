from os.path import join

from elasticsearch import Elasticsearch
import bson
import requests
from tqdm import tqdm

import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')  # include timestamp


class ESClient(object):
    def __init__(self):
        self.es = Elasticsearch(hosts=['166.111.7.106'], port=9200, timeout=60,
                                http_auth=('nekol', 'kegGER123'))
        self.es = Elasticsearch(hosts=['166.111.7.106'], port=9200, timeout=60,
                                http_auth=('ayw19', 'plzupdatepasswd'))
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

        self.es.indices.put_mapping(index='cs_paper_full', doc_type='cs_paper_full', body=cur_prop)
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


es = ESClient()
scp_dir = "./"
# paper_list = utils.load_json(scp_dir, "dblpv13.json")
papers = []
parse_err_cnt = 0
with open(join(scp_dir, "dblpv13.json"), "r", encoding="utf-8") as myFile:
    for i, chunk in enumerate(each_chunk(myFile, separator='}')):
        if i % 10000 == 0:
            logger.info("reading papers %d, parse err cnt %d", i, parse_err_cnt)
        if "\n    \"_id\" :" in chunk:
            if i > 1:
                paper_temp = paper.strip('[').strip(',').strip('\n').replace("NumberInt(", "").replace(')', '')
                try:
                    paper_temp = json.loads(paper_temp)
                    papers.append(paper_temp)
                except:
                    print(paper_temp)
                    print("-------------------------")
                    parse_err_cnt += 1
            paper = ''
            paper += chunk
        else:
            paper += chunk

        # if i > 30000:
        #     break


for paper in tqdm(papers):
    if not es.check_id_exists(paper["_id"]):
        es.add_document(paper)

logger.info("dblp v13 papers index built")
