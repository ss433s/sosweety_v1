import json
import sys, os
sys.path.append("..")
# import pandas as pd
# import numpy as np
# from sParser import hanlp_parse
# from knowledgebase import Concept, Method

# 用于init kb的文件列表, 通常包括spo file和kb relation file(有少量错误)
# 关于数据太大的问题，可以尝试取交集
# 或者只保留下一步需要用到的数据的方法
spo_prefix = 'data/spo_and_pattern'
spo_files = ['nsubj_pr_stat', 'dobj_pr_stat', 'amod_pr_stat']

kb_prefix = 'data/kb_relations'
kb_files = ['pedia_relation', 'pkubase', 'wiki_relation']

# 百度信息抽取比赛实体列表
baidu_ie_entity_file = '/data/corpus/baidu_ie_competition/known_entities'

# 当前路径和项目root路径
this_file_path = os.path.split(os.path.realpath(__file__))[0]
# 可以根据需求改变../..
root_path = os.path.abspath(os.path.join(os.getcwd(), "../.."))

# concept_words = {}
# method_words = {}

concept_set = set()
method_set = set()

# 读取spo file中的concept和method
for spo_file in spo_files:
    spo_file_path = os.path.join(root_path, spo_prefix, spo_file)
    with open(spo_file_path) as spo_file_handler:
        line = spo_file_handler.readline()
        while line:
            line_list = line.strip().split('\t')
            words = line_list[0].split('|')

            # 确定concept和method， 未来可能变动很大
            if 'amod' in spo_file:
                concept_word = words[1]
            else:
                concept_word = words[0]
            if 'nsubj' in spo_file or 'dobj' in spo_file:
                method_word = words[1]

            # method_words[method_word] = 1
            # concept_words[concept_word] = 1
            concept_set.add(concept_word)
            method_set.add(method_word)

            line = spo_file_handler.readline()

# 读取kb file中的concept
for kb_file in kb_files:
    kb_file_path = os.path.join(root_path, kb_prefix, kb_file)
    with open(kb_file_path) as kb_file_handler:
        line = kb_file_handler.readline()
        while line:
            words = line.strip().split('\t')
            concept_set.add(words[0])
            if len(words) > 1:
                concept_set.add(words[1])

            line = kb_file_handler.readline()

print(len(concept_set))

'''
# 写入文件
update_list = [['Concept', concepts], ['Method', methods]]
for file_pre, file_list in update_list:
    file_name = '../data/fake_database/' + file_pre + '_table'
    # with open(file_name, 'r') as f:
    #     line1 = f.readline()
    with open(file_name, 'w') as f:
        heads = []
        for k, _ in vars(file_list[0]).items():
            heads.append(k)
        heads_str = '#' + '\t'.join(heads)
        f.write(heads_str + '\n')
        for i in file_list:
            value_list = []
            for k, v in vars(i).items():
                if v is not None:
                    if isinstance(v, str):
                        value_list.append(v)
                    else:
                        value_list.append(json.dumps(v, ensure_ascii=False))
                else:
                    value_list.append('-')
            f.write('\t'.join(value_list) + '\n')

with open('../data/fake_database/Word_table', 'w') as f:
    f.write('# word  concept_id  Type    freq   Confidence\n')
    for concept in concepts:
        tmp_list = [concept.word, concept.concept_id, 'concept', 0, 0.9]
        f.write(json.dumps(tmp_list, ensure_ascii=False) + '\n')
    for method in methods:
        tmp_list = [method.word, method.method_id, 'method', 0, 0.9]
        f.write(json.dumps(tmp_list, ensure_ascii=False) + '\n')
'''