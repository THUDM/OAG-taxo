import os.path
from os.path import join
import time

import bson
import requests
from tqdm import tqdm
from bson import ObjectId
from collections import defaultdict as dd
import json
from datetime import datetime
import pandas as pd
from fuzzywuzzy import fuzz
from client import MongoDBClientKexie, ESClient, MongoDBClient106
from get_paper_id import get_paper_id_from_title
import utils
import settings

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')  # include timestamp


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


def extract_paper_citation_graph_before_2017():
    scp_dir = "/home/zfj/scp/"
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

            # if i > 3000:
            #     break

    paper_list_filter = []
    for paper in tqdm(papers):
        cur_year = paper.get("year", 2022)
        if cur_year < 2017:
            paper_list_filter.append(paper)

    logger.info("number of papers after filtering %d", len(paper_list_filter))
    utils.dump_json(paper_list_filter, settings.DATA_PRED_DIR, "dblp_papers_before_2017.json")


def extract_authors_with_more_papers():
    paper_list = utils.load_json(settings.DATA_PRED_DIR, "dblp_papers_before_2017.json")
    aid_to_pids = dd(set)

    for paper in tqdm(paper_list):
        pid = paper["_id"]
        cur_authors = paper.get("authors", [])
        for a in cur_authors:
            if "_id" not in a:
                continue
            aid = a["_id"]
            aid_to_pids[aid].add(pid)

    aids_filter = []
    for aid in tqdm(aid_to_pids):
        if len(aid) >= 5:
            aids_filter.append(aid)

    logger.info("number of aids %d", len(aids_filter))
    utils.dump_json(aids_filter, settings.DATA_PRED_DIR, "author_aids_with_more_papers.json")


def extract_authors_with_gs_links():
    aids_list = utils.load_json(settings.DATA_PRED_DIR, "author_aids_with_more_papers.json")
    aids_list = sorted(aids_list)
    client = MongoDBClientKexie()
    person_col = client.aminer_person_col

    batch_size = 100
    chunks = [aids_list[j: j + batch_size] for j in range(0, len(aids_list), batch_size)]

    aid_to_gs = {}
    projection = {"links": 1}
    for chunk in tqdm(chunks):
        cur_aids = [ObjectId(x) for x in chunk]
        cur_persons = person_col.find({"_id": {"$in": cur_aids}}, projection=projection)
        cur_persons = list(cur_persons)
        for person in cur_persons:
            cur_aid = str(person["_id"])
            cur_links = person.get("links", {})
            cur_gs = cur_links.get("gs", {})
            cur_gs_url = cur_gs.get("url")
            if cur_gs_url is not None and len(cur_gs_url) > 10:
                aid_to_gs[cur_aid] = cur_gs_url

    logger.info("number of persons with gs %d", len(aid_to_gs))
    utils.dump_json(aid_to_gs, settings.DATA_PRED_DIR, "aid_to_gs.json")


def extract_authors_with_gs_links_2():
    aid_to_gs = utils.load_json(settings.DATA_PRED_DIR, "aid_to_gs.json")

    aid_to_gs_label = {}
    with open(join(settings.DATA_PRED_DIR, "aminer_google.csv")) as rf:
        for i, line in enumerate(rf):
            if i == 0:
                continue
            items = line.strip().split(",")
            if "scholar" in items[1]:
                aid_to_gs_label[items[0]] = items[1]
    logger.info("number of labeled pairs %d", len(aid_to_gs_label))

    aids_list = utils.load_json(settings.DATA_PRED_DIR, "author_aids_with_more_papers.json")
    for aid in tqdm(aids_list):
        if aid not in aid_to_gs and aid in aid_to_gs_label:
            aid_to_gs[aid] = aid_to_gs_label[aid]

    logger.info("number of persons with gs %d", len(aid_to_gs))
    utils.dump_json(aid_to_gs, settings.DATA_PRED_DIR, "aid_to_gs_2.json")


def build_cs_paper_es_index_dblpv13():
    scp_dir = "/home/zfj/scp/"
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

    es_client = ESClient()

    for paper in tqdm(papers):
        if not es_client.check_id_exists(paper["_id"]):
            es_client.add_document(paper)

    logger.info("dblp v13 papers index built")


def save_labeled_papers_with_sources():
    # df = pd.read_table(open("/Users/zfj/workspace/code/misc/TencentDocDownload/Tracing the source of publications---02:22:2022:21:50:08.xlsx", "rb"))
    # print(df)
    client = MongoDBClient106()
    paper_trace_col = client.paper_source_trace_col
    es_client = ESClient()
    with open("/Users/zfj/workspace/code/misc/TencentDocDownload/Tracing the source of publications---02:22:2022:21:50:08.csv") as rf:
        for i, line in enumerate(rf):
            if i == 0:
                continue
            items = line.strip().split(",")
            if len(items) < 5:
                continue
            print(items)
            cur_item = {"_id": items[0]}
            cur_item["title"] = items[1]
            refs_src = items[2].split(";")
            for ref in refs_src:
                if len(ref) != 24:
                    continue
            cur_item["refs_trace"] = refs_src
            cur_item["annotator"] = items[3]
            try:
                paper_trace_col.insert_one(cur_item)
                es_client.add_document(cur_item, index="labeled_paper_trace_2022")
            except:
                pass


def cal_user_label_count():
    client = MongoDBClient106()
    paper_source_col = client.paper_source_trace_col

    user_to_cnt = dd(int)
    for paper in tqdm(paper_source_col.find()):
        cur_user = paper["annotator"]
        user_to_cnt[cur_user] += 1

    items = sorted(user_to_cnt.items(), key=lambda x: x[1], reverse=True)
    for item in items:
        print(item)


def cal_user_label_count_today():
    client = MongoDBClient106()
    paper_source_col = client.paper_source_trace_col

    now = datetime.now()
    # now = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # dt = now.replace(minute=0, hour=0, second=0, microsecond=0)
    dt1 = datetime(2022, 3, 4)
    dt2 = datetime(2022, 3, 5)

    # now = now.date()
    # print(dt)

    remove_set = {"gengyla", "zqy20", "zfj17", "zhuyifan", "zwd", "sophiezheng@sjtu.edu.cn", "xiaoyiji18", "honghy17",
                  "ch-zhang15", "zx-du20", "cb21", "htl", "cyk20", "zd21", "yzy18"}

    user_to_cnt = dd(int)
    for paper in tqdm(paper_source_col.find({"ts": {"$gte": dt1, "$lt": dt2}})):
        cur_user = paper["annotator"]
        if cur_user not in remove_set:
            user_to_cnt[cur_user] += 1

    items = sorted(user_to_cnt.items(), key=lambda x: x[1], reverse=True)
    for item in items:
        print(item)


def get_paper_refs(pid):
    result = requests.get("http://166.111.5.162:20222/extract_paper_refs/" + pid)
    r = json.loads(result.text)
    for rr in r:
        print(rr)


def find_diff_pids():
    pids = """5f91548b91e011126509bd5a	Self-supervised Graph Learning for Recommendation	5e3d353b3a55ac4de4104f40;5e4672c93a55ac14f595d8b5	yangz21
5cf48a48da56291d582ab75a	Neural Graph Collaborative Filtering	5b67b45517c44aac1c860876;599c798d601a182cd264a97a	yangz21
61850e9691e01121084ca0ce	Self-supervised Learning for Large-scale Item Recommendations	5e4672c93a55ac14f595d8b5;5d79a81b47c8f76646d446a9	yangz21
5ea2b8c391e01167f5a89e2d	Supervised Contrastive Learning	53e99924b7602d970215faff;58d83051d649053542fe9c5b;5e4672c93a55ac14f595d8b5	yangz21
5ede0553e06a4c1b26a83ebf	When Does Self-Supervision Help Graph Convolutional Networks?	58437722ac44360f1082efeb;5ce3afa5ced107d4c65f74da	yangz21
5f9a9af391e0114d7e7813ed	Graph Contrastive Learning with Adaptive Augmentation	5e3a92413a55ac054d0cdbf7;5ee3526a91e011cb3bff72d6	yangz21
5f3cf98391e011c89f2f178c	Sˆ3-Rec: Self-Supervised Learning for Sequential Recommendation with Mutual Information Maximization	5bbacbad17c44aecc4eb00ee;5e5e18a793d709897ce23d3f	yangz21
60c1b1ca91e0112cf43c21f5	Socially-Aware Self-Supervised Tri-Training for Recommendation	5f91548b91e011126509bd5a;53e9bdfdb7602d9704aacecf	yangz21
61dcf5495244ab9dcb1fb68d	Supervised Contrastive Learning for Recommendation	5f91548b91e011126509bd5a	yangz21
6006a8e291e0111a1b6a21e2	Self-Supervised Multi-Channel Hypergraph Convolutional Network for Social Recommendation	5f03f3b611dc830562231fd0;5edf5dd891e011bc656debcf	yangz21
5f7af09591e011983cc81efc	 Hard Negative Mixing for Contrastive Learning	5dcd263a3a55ac58039516c5;5cede0e6da562983788c532a	yangz21
5e67655391e011e0d179111e	Adaptive Offline Quintuplet Loss for Image-Text Matching	5e63725891e011ae97a69b8b	yangz21
5f88146591e0118ce8f040a7	Are all negatives created equal in contrastive instance discrimination?	58437725ac44360f1082fa21;599c7983601a182cd2646713	yangz21
5f7c528491e0117ac2a78bae	Conditional Negative Sampling for Contrastive Learning of Visual  Representations	5dcd263a3a55ac58039516c5;5d1eb9bbda562961f0af6875	yangz21
5ecf8d1a91e01149f850f3ca	Contrastive Learning for Debiased Candidate Generation in Large-Scale Recommender Systems	5ce3aed1ced107d4c65ecae7;5b67b4b417c44aac1c867919	yangz21
5f7fdd328de39f0828397b38	Contrastive Learning with Adversarial Examples	5a73cbcc17c44a0b3035f399;5550417845ce0a409eb3b9b3	yangz21
5f842b5891e01129be18ffbd	Contrastive Learning with Hard Negative Samples	5f7af09591e011983cc81efc	yangz21
5efdaf7b91e01191d3d28242	Debiased Contrastive Learning	5cede10dda562983788edd28;5e4672c93a55ac14f595d8b5	yangz21
61136afa5244ab9dcbd3a9ce	Instance-wise Hard Negative Example Generation for Contrastive Learning in Unpaired Image-to-Image Translation	5f23f9c091e01144966d0ac2	yangz21
5aed14d617c44a44381591f1	Mining on Manifolds: Metric Learning without Labels	57a4e91aac44365e35c97bf2	yangz21
5cf48a2cda56291d5828e868	MixMatch: A Holistic Approach to Semi-Supervised Learning	5a260c8417c44a4ba8a31511	yangz21
5a260c8417c44a4ba8a31511	mixup: BEYOND EMPIRICAL RISK MINIMIZATION	53e99822b7602d9702040e8f;53e9aeb7b7602d97038dc893	yangz21
5d9c5e4d3a55ac916a95fbd8	Negative Sampling in Variational Autoencoders	5c2c7a9217c44a4e7cf31307	yangz21
5dcd26313a55ac5803951499	Negative Sampling in Semi-supervised Learning	599c7965601a182cd2638d24;5cf48a2cda56291d5828e868	yangz21
5ec7a32791e0118397f3ec20	Understanding Negative Sampling in Graph Representation Learning		yangz21
5ce2d0bbced107d4c63af0a4	Robust Negative Sampling for Network Embedding		yangz21
5b67b46b17c44aac1c862052	GNEG: Graph-based Negative Sampling for Word2vec		yangz21
600832419e795ed227f530f4	Negative Data Augmentation	5a4aef9e17c44a2190f7a8fa	yangz21
599c7967601a182cd2639a14	No Fuss Distance Metric Learning using Proxies	53e99924b7602d970215faff	yangz21
5bdc315017c44a1f58a05bba	Noise Contrastive Estimation and Negative Sampling for Conditional Models: Consistency and Statistical Efficiency	53e9aebcb7602d97038e4188;53e9aa09b7602d9703377fec	yangz21
60d1419c91e011c16f0cb393	Novelty Detection via Contrastive Learning with Negative Data Augmentation	5cede0f7da562983788d6a60;5ef96b048806af6ef277203d	yangz21
5ecf8d2391e01149f850f483	On Mutual Information in Contrastive Learning for Visual Representations	5e4672c93a55ac14f595d8b5;5dcd263a3a55ac58039516c5	yangz21
599c7959601a182cd2633b3e	On Sampling Strategies for Neural Network-based Collaborative Filtering	53e9bd98b7602d9704a3f3ec;573696ce6e3b12023e5ce889	yangz21
60b1959091e0115374595704	Rethinking InfoNCE: How Many Negative Samples Do You Need?	599c796d601a182cd263c833	yangz21
602a4b5191e011a1a44cbe3b	Semantically-Conditioned Negative Samples for Efficient Contrastive Learning	5d343abd275ded87f9774e65;	yangz21
599c795d601a182cd2635171	Smart Mining for Deep Metric Learning	58d83051d649053542fe9c5b;573696086e3b12023e51c1cc	yangz21
5c8d0b1f4895d9cbc63529e3	The Impact of Negative Samples on Learning to Rank		yangz21
5736960c6e3b12023e51fc97	Online Batch Selection for Faster Training of Neural Networks 		yangz21
57a4e91aac44365e35c98023	Training Region-based Object Detectors with Online Hard Example Mining	5736960c6e3b12023e51fc97	yangz21
5a260c8117c44a4ba8a30b08	Focal Loss for Dense Object Detection	57a4e91aac44365e35c98023	yangz21
5c7575e4f56def9798a3f477	Adversarial Deep Learning Models with Multiple Adversaries		yangz21
5fdc912691e01104c91811d1	Understanding the Behaviour of Contrastive Loss		yangz21
6062fc5f91e0118c891f1a1d	SelfGNN: Self-supervised Graph Neural Networks without explicit negative sampling		yangz21
6076c5d791e0113d7257444c	Probing Negative Sampling Strategies to Learn Graph Representations via Unsupervised Contrastive Learning		yangz21
608a8aea91e011b76ccd55fd	A Note on Connecting Barlow Twins with Negative-Sample-Free Contrastive Learning		yangz21
60c1bcfc91e0112cf43c228b	Incremental False Negative Detection for Contrastive Learning		yangz21
60e438fddfae54001623c00a	Self-Contrastive Learning with Hard Negative Sampling for Self-supervised Point Cloud Learning		yangz21
60ff9e095244ab9dcb02272b	The Impact of Negative Sampling on Contrastive Structured World Models	5e5e18bf93d709897ce2d2a0	yangz21
60b99d63e4510cd7c8eff21f	DGCN: Diversified Recommendation with Graph Convolutional Networks		yangz21
6125b0125244ab9dcb38b2a9	Jointly Learnable Data Augmentations for Self-Supervised GNNs		yangz21"""
    items = [x for x in pids.split("\n")]
    # print(pids)
    client = MongoDBClient106()
    paper_trace_col = client.paper_source_trace_col
    es_client = ESClient()
    cnt = 0
    for item in items:
        item = item.strip().split("\t")
        print(item)
        assert len(item) == 4
        sids = item[2].strip().split(";")
        if len(sids) == 1 and not bson.objectid.ObjectId.is_valid(sids[0]):
            es_client.delete_document(index="labeled_paper_trace_2022", _id=item[0])
            continue
        r = paper_trace_col.find_one({"_id": item[0]})
        # print("r", item[0], r)
        # if r["annotator"] != "htl":
        #     print(r)
        if r is None:
            cur_item = {"_id": item[0]}
            cur_item["title"] = item[1]
            cur_item["refs_trace"] = item[2].strip().split(";")
            cur_item["annotator"] = item[3]
            cur_item["ts"] = datetime.now()
            cur_item["ref_user"] = ""
            paper_trace_col.insert_one(cur_item)
            es_client.add_document(cur_item, index="labeled_paper_trace_2022")
            cnt += 1
        else:
            print(item[0], "exists")
    print("cnt", cnt)
    raise

    r = list(paper_trace_col.find({"_id": {"$in": pids}}))
    # print("r", r)
    pids_inserted = {x["_id"] for x in r}
    pids_remain = [x for x in pids if x not in pids_inserted]
    for pid in pids_remain:
        print(pid)


def find_paper_pdfs():
    client_106 = MongoDBClient106()
    client_online = MongoDBClientKexie()
    paper_source_col = client_106.paper_source_trace_col
    aminer_pub_col = client_online.aminer_pub_col
    paper_wo_pdf_cnt = 0
    out_dir = join(settings.DATA_TRACE_DIR, "paper-pdf")
    os.makedirs(out_dir, exist_ok=True)
    pdfBaseUrl = "https://cz5waila03cyo0tux1owpyofgoryrooa.oss-cn-beijing.aliyuncs.com"
    for paper in tqdm(paper_source_col.find()):
        cur_paper_db = aminer_pub_col.find_one({"_id": ObjectId(paper["_id"])})
        cur_pdf_url = cur_paper_db.get("pdf", "")
        if cur_pdf_url is None or len(cur_pdf_url) <= 4:
            paper_wo_pdf_cnt += 1
            print(paper["_id"], paper["title"])
        else:
            # print(cur_pdf_url)
            if cur_pdf_url.endswith(".pdf") and cur_pdf_url.startswith("http"):
                pass
            elif cur_pdf_url.endswith(".pdf") and cur_pdf_url.startswith("//"):
                cur_pdf_url = "https:" + cur_pdf_url
                # print(cur_pdf_url)
            elif cur_pdf_url.endswith(".md5"):
                md5String = cur_pdf_url[0: 32]
                cur_pdf_url = "{}/{}/{}/{}/{}.pdf".format(pdfBaseUrl, md5String[0:2], md5String[2:4], md5String[4:6], md5String)
                # print(cur_pdf_url)
                pass
            else:
                print(paper["_id"], paper["title"])
            # else:
            #     raise
            cur_fname = "{}.pdf".format(paper["_id"])
            if os.path.isfile(join(out_dir, cur_fname)):
                continue
            # res = requests.get(cur_pdf_url)
            # with open(join(out_dir, cur_fname), "wb") as wf:
            #     wf.write(res.content)
            # time.sleep(30)
            # raise
    print("miss cnt", paper_wo_pdf_cnt)


def parse_text_paper_source():
    xl_file = pd.ExcelFile("~/Downloads/计算机论文打卡共享阅读列表.xlsx")
    # print(xl_file.sheet_names)
    df = xl_file.parse(xl_file.sheet_names[0])
    client = MongoDBClient106()
    paper_source_col = client.paper_source_trace_col
    items_remain = []
    for i, row in df.iterrows():
        if i <= 2:
            continue
        # print(row.ix[0])
        cur_title = row.ix[0].lower()
        cur_venue = row.ix[1]
        cur_source_papers = row.ix[3]
        user = row.ix[4]
        cur_source_papers = cur_source_papers.strip().split("###")
        print(cur_title)
        print(cur_venue)
        print(cur_source_papers)
        print(user)

        pid_hit = get_paper_id_from_title(cur_title)
        print("pid_hit", pid_hit)

        if pid_hit is not None:
            r_db = paper_source_col.find_one({"_id": pid_hit})
            if r_db is None:
                print("here")
                sids = []
                for s_title in cur_source_papers:
                    s_title = s_title.lower()
                    cur_sid = get_paper_id_from_title(s_title)
                    if cur_sid is not None:
                        sids.append(cur_sid)
                if len(sids) > 0:
                    # print("sids", sids)
                    cur_item = {"_id": pid_hit}
                    cur_item["title"] = cur_title
                    cur_item["refs_trace"] = sids
                    cur_item["annotator"] = user
                    print("cur_item", cur_item)
                    try:
                        r2 = requests.post("http://166.111.5.162:20222/insert_one_item", json=cur_item)
                        r3 = requests.post("http://166.111.5.162:20222/insert_one_item_to_es", json=cur_item)
                    except:
                        print("插入数据异常")
                else:
                    items_remain.append((cur_title, cur_venue, cur_source_papers, user))
            else:
                print(cur_title, "inserted")
        else:
            items_remain.append((cur_title, cur_venue, cur_source_papers, user))

        time.sleep(30)
        # raise
        print("\n\n")

    print("items remain:")
    for item in items_remain:
        print(item)


if __name__ == "__main__":
    # extract_paper_citation_graph_before_2017()
    # extract_authors_with_more_papers()
    # extract_authors_with_gs_links()
    # extract_authors_with_gs_links_2()
    # build_cs_paper_es_index_dblpv13()
    # save_labeled_papers_with_sources()
    # cal_user_label_count()
    cal_user_label_count_today()
    # get_paper_refs("60a2401291e0115ec77b9cd9")
    # find_diff_pids()
    # find_paper_pdfs()
    # parse_text_paper_source()
    logger.info("done")
