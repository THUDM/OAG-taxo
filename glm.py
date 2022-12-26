import torch
from pytorch_pretrained_bert import BertTokenizer, BertModel, BertForMaskedLM
import logging
import matplotlib.pyplot as plt
from torch.nn import functional as F
from retrival.client import ESClient
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import random


class Log:
    def __init__(self, file_path):
        self.file_path = file_path
        self.f = open(file_path, 'w+')

    def log(self, s):
        self.f.write(s)


def cut_dataset(train, valid, test, dataset):
    size = len(dataset)
    train_key = random.sample(dataset.keys(), round(train * size))
    train_d = {k: v for k, v in dataset.items() if k in train_key}
    dataset = {k: v for k, v in dataset.items() if k not in train_key}
    valid_key = random.sample(dataset.keys(), round((valid * size)))
    valid_d = {k: v for k, v in dataset.items() if k in valid_key}
    test_d = {k: v for k, v in dataset.items() if k not in valid_key}
    return train_d, valid_d, test_d


def metric(parent, candidate):
    """
    todo: design metric for candidate select
    """
    return 0


def main():
    es = ESClient()
    log = Log('./log/naive train.log')
    id2term = {}
    i = 0
    with open('./computer_science.terms') as f:
        line = f.readline()
        while line:
            res_ = line.split('\t')
            id2term[int(res_[0])] = res_[1].replace('\n', '')
            line = f.readline()

    concept = {}

    with open('./computer_science.taxo') as f:
        line = f.readline()
        while line:
            res_ = line.split('\t')

            parent = id2term[int(res_[0])]
            child = id2term[int(res_[1])]
            if child in concept.keys():
                concept[child].append(parent)
            else:
                concept[child] = [parent]
            line = f.readline()

    train, valid, test = cut_dataset(0.7, 0.15, 0.15, id2term)

    tokenizer = AutoTokenizer.from_pretrained("BAAI/glm-2b", trust_remote_code=True)
    model = AutoModelForSeq2SeqLM.from_pretrained("BAAI/glm-2b", trust_remote_code=True)
    model = model.half().cuda()
    model.eval()

    for epoch in range(200):
        for sid, sub_term in train.items():
            if sub_term not in concept:
                continue
            abstracts = ""
            res = es.search(key_words=sub_term)
            for i in res:
                abstracts += i['abstract'] + ' '
            qa = sub_term + " is a subclass of [MASK]"
            whole = abstracts + qa
            for parent in concept[sub_term]:
                inputs = tokenizer(
                    whole, return_tensors="pt", padding=True)
                inputs = tokenizer.build_inputs_for_generation(inputs, targets=[parent], max_gen_length=10)
                outputs = model(**inputs)
                loss = outputs.loss
                logits = outputs.logits
                loss.backward()
        log.log('train epoch {} end'.format(epoch))
        with torch.no_grad():
            for sid, sub_term in valid.items():
                if sub_term not in concept:
                    continue
                abstracts = ""
                res = es.search(key_words=sub_term)
                for i in res:
                    abstracts += i['abstract'] + ' '
                qa = sub_term + " is a subclass of [MASK]"
                whole = abstracts + qa
                inputs = tokenizer(
                        whole, return_tensors="pt", padding=True)
                inputs = tokenizer.build_inputs_for_generation(inputs, max_gen_length=512)
                outputs = model.generate(**inputs, max_length=512, eos_token_id=tokenizer.eop_token_id)
                candidate = tokenizer.decode(outputs[0].tolist())
                begin_token = '<|startofpiece|>'
                end_token = '<|endofpiece|>'
                candidate = candidate[candidate.find(begin_token) + len(begin_token): candidate.find(end_token)]
                res = metric(parent, candidate)
        log.log('valid epoch {} end'.format(epoch))


if __name__ == "__main__()":
    main()
