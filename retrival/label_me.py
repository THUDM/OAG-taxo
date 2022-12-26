import requests
import json
import bson


def input_obj_id():
    while True:
        pid = input("输入您找到的论文对应的aminer ID：")
        if bson.objectid.ObjectId.is_valid(pid):
            break
        else:
            print("ID 格式错误")
    return pid


def run():
    user_id = input("输入你的用户名: ")
    rec_user = input("输入你的推荐人，若无直接回车")
    r0 = requests.get("http://166.111.5.162:20222/count_label_count/" + user_id)
    print("您目前已标注条数为：", r0.text)
    while True:
        # one trial
        title = input("输入一篇论文的题目: ")
        r1 = requests.get("http://166.111.5.162:20222/search_labeled_title_es/" + title)
        # print(r1)
        r1 = json.loads(r1.text)
        if r1 is not None and len(r1) > 0:
            print(title, "已经被标注过了，请您尝试另一篇论文")
            continue
        else:
            pid = input_obj_id()
            pids_src = []
            print("下面请依次输入启发目标论文的重要文献的aminer ID，若所有重要参考文献都输入完毕，最后一次请输入#")
            ii = 0
            while True:
                cur_ref_pid = input("输入您找到的论文对应的aminer ID，若无剩余则输入#：")
                if ii == 0:
                    if not bson.objectid.ObjectId.is_valid(cur_ref_pid):
                        print("输入ID格式错误，请重新输入")
                        continue
                if cur_ref_pid == "#":
                    break
                elif not bson.objectid.ObjectId.is_valid(cur_ref_pid):
                    print("输入ID格式错误，请重新输入")
                    continue
                pids_src.append(cur_ref_pid)
                ii += 1
            cur_item = {"_id": pid}
            cur_item["title"] = title
            cur_item["refs_trace"] = pids_src
            cur_item["annotator"] = user_id
            cur_item["ref_user"] = rec_user
            try:
                r2 = requests.post("http://166.111.5.162:20222/insert_one_item", json=cur_item)
                r3 = requests.post("http://166.111.5.162:20222/insert_one_item_to_es", json=cur_item)
            except:
                print("插入数据异常")

            r0 = requests.get("http://166.111.5.162:20222/count_label_count/" + user_id)
            print("您目前已标注条数为：", r0.text, "\n\n")


if __name__ == "__main__":
    run()
