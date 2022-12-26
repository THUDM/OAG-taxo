import torch
from pytorch_pretrained_bert import BertTokenizer, BertModel, BertForMaskedLM
import logging
import matplotlib.pyplot as plt
from transformers import *
from torch.nn import functional as F
from retrival.client import ESClient

es = ESClient()

term2id = {}
i = 0
with open('./computer_science.terms') as f:
    line = f.readline()
    while line:
        res_ = line.split('\t')
        term2id[int(res_[0])] = res_[1].replace('\n', '')
        line = f.readline()

concept = {}

with open('./computer_science.taxo') as f:
    line = f.readline()
    while line:
        res_ = line.split('\t')

        parent = term2id[int(res_[0])]
        child = term2id[int(res_[1])]
        if child in concept.keys():
            concept[child].append(parent)
        else:
            concept[child] = [parent]
        line = f.readline()

tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertForMaskedLM.from_pretrained("bert-base-uncased")
inputs = tokenizer.encode_plus(text, return_tensors = "pt")

with torch.no_grad():
    logits = model(**inputs).logits
softmax = F.softmax(logits, -1)
mask_token_index = (inputs.input_ids == tokenizer.mask_token_id)[0].nonzero(as_tuple=True)[0]

predicted_token_id = logits[0, mask_token_index]
print(predicted_token_id)
print(predicted_token_id.shape)
values, indices = torch.topk(predicted_token_id, k=7, dim=-1)
print(indices)
for i in indices:
    print(i)
    x = tokenizer.decode(i)
    print(x)
exit(0)

abstracts = ""
test_concept = "giant lock"
res = es.search(key_words=test_concept)
for i in res:
    abstracts += i['abstract'] + ' '
print(abstracts)
qa = test_concept + " is a subclass of [MASK]"


term2id = {}
i = 0
with open('./computer_science.terms') as f:
    line = f.readline()
    while line:
        res_ = line.split('\t')
        term2id[int(res_[0])] = res_[1].replace('\n', '')
        line = f.readline()

concept = {}

with open('./computer_science.taxo') as f:
    line = f.readline()
    while line:
        res_ = line.split('\t')

        parent = term2id[int(res_[0])]
        child = term2id[int(res_[1])]
        if child in concept.keys():
            concept[child].append(parent)
        else:
            concept[child] = [parent]
        line = f.readline()

text = "The capital of France, " + tokenizer.mask_token + ", contains the Eiffel Tower."
input = tokenizer.encode_plus(text, return_tensors="pt")
mask_index = torch.where(input["input_ids"][0] == tokenizer.mask_token_id)
output = model(**input)
logits = output.pooler_output
softmax = F.softmax(logits, dim=-1)
mask_word = softmax[0, mask_index, :]
top_10 = torch.topk(mask_word, 10, dim=1)[1][0]
for token in top_10:
    word = tokenizer.decode([token])
    new_sentence = text.replace(tokenizer.mask_token, word)
    print(new_sentence)
