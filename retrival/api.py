from flask import Flask, request
from flask_restful import Resource, Api
from bson import ObjectId
from fuzzywuzzy import fuzz
from datetime import datetime
from client import ESClient, MongoDBClient106, MongoDBClientKexie

app = Flask(__name__)
api = Api(app)


class SearchPaperTitleES(Resource):
    def get(self, title):
        es_client = ESClient()
        # client = MongoDBClientKexie()
        client = MongoDBClient106()
        aminer_pub_col = client.aminer_pub_col
        result = es_client.search(title.lower())
        if len(result) == 0:
            return result
        ids_list = [ObjectId(x["_id"]) for x in result]
        r_mongo = list(aminer_pub_col.find({"_id": {"$in": ids_list}}))
        id_to_authors = {str(x["_id"]): x["authors"] for x in r_mongo}
        result_new = []
        for r in result:
            cur_id = r["_id"]
            if cur_id in id_to_authors:
                r["authors"] = ", ".join([x.get("name", "") for x in id_to_authors[cur_id]])
            result_new.append(r)
        return result_new


class SearchLabeledTitleES(Resource):
    def get(self, title):
        es_client = ESClient()
        title = title.lower()
        result = es_client.search(title, index="labeled_paper_trace_2022")
        for rr in result:
            cur_cand_title = rr["_source"]["title"]
            cur_sim = fuzz.ratio(cur_cand_title, title)
            if cur_sim >= 90:
                return [rr]


class InsertOneItem(Resource):
    def post(self):
        item = request.json
        client = MongoDBClient106()
        label_col = client.paper_source_trace_col
        now = datetime.now()
        item["ts"] = now
        try:
            label_col.insert_one(item)
            return True
        except:
            return False


class InsertOneItemToES(Resource):
    def post(self):
        item = request.json
        es_client = ESClient()
        es_client.add_document(item, index="labeled_paper_trace_2022")
        return True


class CountLabelCount(Resource):
    def get(self, username):
        client = MongoDBClient106()
        label_col = client.paper_source_trace_col
        num = label_col.find({"annotator": username}).count()
        return num


class ExtractPaperRefs(Resource):
    def get(self, pid):
        client = MongoDBClientKexie()
        pub_relation_col = client.pub_relation_col
        aminer_pub_col = client.aminer_pub_col
        refs = list(pub_relation_col.find({"ref": ObjectId(pid)}))
        if len(refs) == 0:
            return []
        ref_ids = [x["cited"] for x in refs]
        ref_papers = list(aminer_pub_col.find({"_id": {"$in": ref_ids}}))
        ref_papers_clean = []
        for paper in ref_papers:
            paper_new = {"_id": str(paper["_id"]), "title": paper["title"]}
            paper_new["authors"] = ", ".join([x.get("name", "") for x in paper.get("authors", [])])
            paper_new["year"] = paper["year"]
            ref_papers_clean.append(paper_new)
        return ref_papers_clean


api.add_resource(SearchPaperTitleES, "/search_cs_title_es/<title>")
api.add_resource(SearchLabeledTitleES, "/search_labeled_title_es/<title>")
api.add_resource(InsertOneItem, "/insert_one_item")
api.add_resource(InsertOneItemToES, "/insert_one_item_to_es")
api.add_resource(CountLabelCount, "/count_label_count/<username>")
api.add_resource(ExtractPaperRefs, "/extract_paper_refs/<pid>")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=20222)
