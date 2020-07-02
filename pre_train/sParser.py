# import jieba
import re, json, argparse
# import regex as re2
import jieba
import jieba.posseg
import time
import ahocorasick
from pyhanlp import HanLP
import sys
sys.path.append("..")
# from utils import tuple_in_tuple, find_all_sub_list
from knowledgebase import Knowledge_base, concepts


# parse result类
class Parse_result(object):
    def __init__(self, contents):
        self.contents = contents
        self.pos_tags = [i.pos_tag for i in self.contents]
        self.words = [i.value for i in self.contents]
        self.parse_str = "|".join(self.pos_tags)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = ""
        # s += "words: %s" % (self.words)
        # s += ", pos_tags: %s" % (self.pos_tags)
        s += "\"content: %s\"" % (self.contents)
        return s


# 单词类 value为字面， pos_tag为词性
class Word(object):
    def __init__(self, value, pos_tag, pos_tag2=None):
        self.value = value
        self.pos_tag = pos_tag
        self.core_word = self.value
        if pos_tag2:
            self.pos_tag2 = pos_tag2

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = ""
        s += "word: %s" % (self.value)
        s += ", pos_tag: %s" % (self.pos_tag)
        # s += ", parse_str: %s" % (self.parse_str)
        return s


# Special pattern和Phrase类 特殊短语
class Special_pattern(object):
    def __init__(self, phrase_type, pos_tag, core_word_index, features, freq, meaning, symbol=None, examples=None):
        self.phrase_type = phrase_type
        self.pos_tag = self.phrase_type
        self.core_word_index = core_word_index
        self.features = json.loads(features)
        self.freq = float(freq)
        self.meaning = meaning
        self.symbol = symbol
        if examples:
            self.examples = json.loads(examples)
        else:
            self.examples = None

    def __str__(self):
        return self.__repr__()

    # def __setitem__(self, k, v):
    #     self.k = v

    def __repr__(self):
        s = ""
        s += "features: %s" % (self.features)
        s += ", phrase_type: %s" % (self.phrase_type)
        s += ", freq: %s" % (self.freq)
        s += ", meaning: %s" % (self.meaning)
        s += ", symbol: %s" % (self.symbol)
        s += ", examples: %s" % (self.examples)
        return s


# Special pattern的实例，有具体的词语内容
class Special_phrase(object):
    def __init__(self, phrase_pattern, contents):
        self.contents = contents
        self.phrase_type = phrase_pattern.phrase_type
        self.features = phrase_pattern.features
        self.pos_tag = self.phrase_type
        self.core_word_index = phrase_pattern.core_word_index
        self.freq = phrase_pattern.freq
        self.meaning = phrase_pattern.meaning
        self.words = [content.value for content in self.contents]
        self.value = "".join(self.words)
        if self.core_word_index == '-':
            self.core_word = self.value
        else:
            self.core_word = self.words[int(self.core_word_index)]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = ""
        # s += "words: %s" % (self.words)
        s += "phrase_type: %s" % (self.phrase_type)
        s += ", freq: %s" % (self.freq)
        s += ", meaning: %s" % (self.meaning)
        s += ", features: %s" % (self.features)
        s += ", contents: %s" % (self.contents)
        return s


# sub sentence  pre是临时存储用的，只有字符串，可以根据标点符号给出type
class Sub_sentence_pattern(object):
    def __init__(self, parse_str, freq, ss_type, meaning):
        self.parse_str = parse_str
        self.freq = float(freq)
        self.ss_type = ss_type
        self.meaning = meaning


class Sub_sentence(object):
    def __init__(self, ss_pattern, contents):
        self.parse_str = ss_pattern.parse_str
        self.freq = ss_pattern.freq
        self.ss_type = ss_pattern.ss_type
        self.meaning = ss_pattern.meaning
        self.contents = contents

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = "\n"
        s += "parse_str: %s,\n" % (self.parse_str)
        s += "ss_type: %s,\n" % (self.ss_type)
        s += "freq: %s,\n" % (self.freq)
        s += "meaning: %s,\n" % (self.meaning)

#         def iter_one_level(contents):
#             has_phrase = False
#             value_list = []
#             phrase_list = []
#             for item in contents:
#                 value_list.append(item.value)
#                 if not isinstance(item, Word):
#                     has_phrase = True
#                     phrase_list.append(item)
#             print('     '.join(value_list))
#             return has_phrase, phrase_list, value_list

#         level_maxtrix = {}
#         level = 0
#         seq = 0
#         matrix_x = 0
#         matrix_y = 0
#         has_phrase = True
#         contents = self.contents
#         bottom_level_x = [i for i in range(len(contents))]
#         level_maxtrix.append(bottom_level_x)
#         while has_phrase:
#             this_level_x = level_maxtrix[level]
#             for i in range(len(contents)):
#                 item = contents[i]
#                 if not isinstance(item, Word):
#                     this_level_x[i] += len(contents)/2 - 0.5
#                     if i < len(contents):
#                         for j in range(i+1, len(contents)):
#                             this_level_x[j] += len(item)

#             this_level_has_phrase, this_level_phrase_list, this_level_value_list = iter_one_level(contents)
#             level_maxtrix[level] = this_level_value_list
#             level += 1
#             if this_level_has_phrase:
#                 for contents in this_level_phrase_list:

        level_list = []
        has_phrase = True
        contents_list = [self.contents]
        while has_phrase:
            this_level_value_list = []
            next_level_content_list = []
            has_not_phrase_list = []
            for contents in contents_list:
                contents_has_not_phrase = all([isinstance(item, Word) for item in contents])
                has_not_phrase_list.append(contents_has_not_phrase)
                this_level_value_list += [item.value for item in contents]
                for item in contents:
                    if not isinstance(item, Word):
                        next_level_content_list.append(item.contents)
            level_list.append(this_level_value_list)
            contents_list = next_level_content_list
            has_phrase = not all(has_not_phrase_list)

        s += "contents: \n"
        for level in range(len(level_list)-1, -1, -1):
            s += json.dumps(level_list[level], ensure_ascii=False) + '\n'
        return s


class Pre_sub_sentence(object):
    def __init__(self, value, ss_type=None, raw_parse_result=None):
        self.value = value
        self.ss_type = ss_type
        self.raw_parse_result = raw_parse_result


# ###########################各种函数######################

###################
# 分句
# to do 引号破折号等，引号纠错
###################
def seg2sentence(paragraph):
    sentences = re.split('(。|！|\!|\.|？|\?)', paragraph)
    new_sents = []
    for i in range(int(len(sentences) / 2)):
        if 2 * i + 1 < len(sentences):
            sent = sentences[2 * i] + sentences[2 * i + 1]
        else:
            sent = sentences[2 * i]
        new_sents.append(sent)
    return new_sents


def cut_sent(para):
    para = re.sub('([。！？\?])([^”’])', r"\1\n\2", para)  # 单字符断句符
    para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)  # 英文省略号
    para = re.sub('(\…{2})([^”’])', r"\1\n\2", para)  # 中文省略号
    para = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', para)
    # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
    para = para.rstrip()  # 段尾如果有多余的\n就去掉它
    # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
    return para.split("\n")


###################
# 拆分子句
# to do 引号破折号等，引号纠错 小数点处理
###################
'''
带逗号的版本
def seg2sub_sentence(sentence):
    sub_sentences = re.split('(，|,|;|；)', sentence)
    new_sub_sents = []
    for i in range(int(len(sub_sentences) / 2) + 1):
        if 2 * i + 1 < len(sub_sentences):
            sub_sent = sub_sentences[2 * i] + sub_sentences[2 * i + 1]
        else:
            sub_sent = sub_sentences[2 * i]
        new_sub_sents.append(sub_sent)
    return new_sub_sents
'''


def seg2sub_sentence(sentence):
    sub_sentences = re.split('(，|,|;|；)', sentence)
    new_sub_sents = []
    for i in range(len(sub_sentences)):
        if i % 2 == 0:
            sub_sent = Pre_sub_sentence(sub_sentences[i])
        else:
            sub_sent = Word(sub_sentences[i], 'PU')
        new_sub_sents.append(sub_sent)
    return new_sub_sents


###################
# 词组检测
# 构建所有可能的词组组合
###################
# 先检测特殊短语
def check_special_phrase(parse_result, final_results, mode='default', N=0, start_time=None):
    # print('next')
    not_done = []
    # 自身就在ss_pattern中
    final_results_str = [str(final_result) for final_result in final_results]

    matched_ss_pattern = check_ss_pattern(parse_result)
    if len(matched_ss_pattern) > 0:
        for ss_pattern in matched_ss_pattern:
            ss = Sub_sentence(ss_pattern, parse_result.contents)
            if str(ss) not in final_results_str:
                final_results.append(ss)
                final_results_str.append(str(ss))

    # 替换phrase后在ss_pattern中
    for i in range(len(phrase_patterns)):
        phrase_pattern = phrase_patterns[i]
        # if i % 10 == 0:
        #     print(i, N)
        new_parse_results = find_single_special_pattern(parse_result, phrase_pattern)
        not_done.append(len(new_parse_results) == 0)
        for new_parse_result in new_parse_results:
            matched_ss_pattern = check_ss_pattern(new_parse_result)
            if len(matched_ss_pattern) > 0:
                for ss_pattern in matched_ss_pattern:
                    ss = Sub_sentence(ss_pattern, new_parse_result.contents)
                    if str(ss) not in final_results_str:
                        final_results.append(ss)
                        final_results_str.append(str(ss))

                # 初始化时开启这句，找到就退出循环
                if mode == 'init':
                    break

            if mode == 'init' and len(final_results) > 0:
                break
            # if N < 5:
            if start_time is not None and time.time() - start_time < 60:
                check_special_phrase(new_parse_result, final_results, mode, N + 1, start_time)

            # 不给start time就无限找下去
            if start_time is None:
                check_special_phrase(new_parse_result, final_results, mode, N + 1, start_time)
    if all(not_done):
        return


# 检测一个special phrase pattern 在一份parse result中的所有位置
def find_single_special_pattern(parse_result, special_pattern):

    def match_one_feature(parse_result_content, feature):
        result = False
        if list(feature.keys())[0] == 'concept':
            rst = KB.word_belong_to_concept(parse_result_content.value, feature['concept'])
            if len(rst) > 0:
                result = True
        if list(feature.keys())[0] == 'word':
            if parse_result_content.value == feature['word']:
                result = True
        if list(feature.keys())[0] == 'pos_tag':
            if parse_result_content.pos_tag == feature['pos_tag']:
                result = True

        # 正则符合，需谨慎
        if list(feature.keys())[0] == 'special_symbol':
            if feature['special_symbol'] == '*':
                result = True

        return result

    new_parse_results = []
    first_feature = special_pattern.features[0]

    # for j in range(len(parse_result.pos_tags) - len(special_pattern.features) + 1):
    #     if match_one_feature(parse_result.contents[j], first_feature):
    #         i = 1
    #         while len(parse_result.contents) > j + i and len(special_pattern.features) > i:
    #             if match_one_feature(parse_result.contents[j + i], special_pattern.features[i]):
    #                 i += 1
    #                 continue
    #             else:
    #                 break

    #         if i == len(special_pattern.features):
    #             new_parse_result_contents = parse_result.contents[0:j]
    #             contents = parse_result.contents[j: j + i]
    #             special_phrase = Special_phrase(special_pattern, contents)
    #             new_parse_result_contents.append(special_phrase)
    #             if j + i < len(parse_result.contents):
    #                 new_parse_result_contents += parse_result.contents[j + i: len(parse_result.contents)]
    #             new_parse_result = Parse_result(new_parse_result_contents)
    #             new_parse_results.append(new_parse_result)
    # return new_parse_results

    # 目前限制很多，只识别*且*至少一个,且*前后必须有非*
    for j in range(len(parse_result.pos_tags) - len(special_pattern.features) + 1):
        if match_one_feature(parse_result.contents[j], first_feature):
            pattern_contain_special = False
            for feature in special_pattern.features:
                if 'special_symbol' in feature:
                    pattern_contain_special = True
                    break

            # 有*
            if pattern_contain_special:
                full_match = False
                i = 1
                while len(parse_result.contents) > j + i and len(special_pattern.features) > i:
                    current_feature = special_pattern.features[i]
                    if match_one_feature(parse_result.contents[j + i], current_feature):
                        if 'special_symbol' in current_feature and current_feature['special_symbol'] == '*':
                            next_feature = special_pattern.features[i+1]
                            if match_one_feature(parse_result.contents[j + i + 1], next_feature):
                                i += 2
                                full_match = True
                                break
                            else:
                                for k in range(1, len(parse_result.contents) - j - i):
                                    if match_one_feature(parse_result.contents[j + i + k], next_feature):
                                        i += k + 1
                                        full_match = True
                                        break
                                if full_match:
                                    break
                        i += 1
                    else:
                        break
            # 没有*
            else:
                i = 1
                while len(parse_result.contents) > j + i and len(special_pattern.features) > i:
                    if match_one_feature(parse_result.contents[j + i], special_pattern.features[i]):
                        i += 1
                        # continue
                    else:
                        break
                full_match = i == len(special_pattern.features)

            if full_match:
                new_parse_result_contents = parse_result.contents[0:j]
                contents = parse_result.contents[j: j + i]
                special_phrase = Special_phrase(special_pattern, contents)
                new_parse_result_contents.append(special_phrase)
                if j + i < len(parse_result.contents):
                    new_parse_result_contents += parse_result.contents[j + i: len(parse_result.contents)]
                new_parse_result = Parse_result(new_parse_result_contents)
                new_parse_results.append(new_parse_result)
    return new_parse_results


# check_sub_sentence  返回所有匹配到的ss_pattern
def check_ss_pattern(parse_result):
    result = []
    for ss_pattern in ss_patterns:
        if parse_result.parse_str == ss_pattern.parse_str:
            result.append(ss_pattern)
    return result


###################
# 检测已知实体  其实是检测可以合并的实体 目前看0320
# todo  到底有没有用？什么时候用 重分词再做？
# 返回当前分词条件下可以组合出的实体合并后的全部parse_result
# 与kb中的checkout_words 功能有重叠
###################
def check_known_concepts(parse_result):
    # 构建所有实体的actree
    actree = ahocorasick.Automaton()
    for i in concepts:
        concept = concepts[i]
        word = concept.word
        actree.add_word(word, word)
    actree.make_automaton()

    sentence = ''.join([item.value for item in parse_result.contents])
    matched_concepts = actree.iter(sentence)

    new_parse_results = []
    for i in range(len(parse_result.contents)):
        item = parse_result.contents[i]
        for matched_concept in matched_concepts:
            word = matched_concept[1]

            # 组合后是否还是concept
            if len(item.value) < len(word) and item.value == word[0:len(item.value)] and i+1 < len(parse_result.contents):
                all_value = item.value
                for j in range(i + 1, len(parse_result.contents)):
                    next_item = parse_result.contents[i+j]
                    all_value += next_item.value
                    if all_value == word:
                        new_parse_result_contents = parse_result.contents[0:i]
                        concept_word = Word(word, 'NN')
                        new_parse_result_contents.append(concept_word)
                        if j + i + 1 < len(parse_result.contents):
                            new_parse_result_contents += parse_result.contents[j + i + 1: len(parse_result.contents)]
                        new_parse_result = Parse_result(new_parse_result_contents)
                        new_parse_results.append(new_parse_result)
                        break
                    elif len(all_value) > len(word):
                        break

    return new_parse_results


###################
# 重分词
# 检测已知实体
# todo  重分词时识别所有潜在实体
###################
def check_known_concepts2(parse_result):
    # 构建所有实体的actree
    actree = ahocorasick.Automaton()
    for i in concepts:
        concept = concepts[i]
        word = concept.word
        actree.add_word(word, word)
    actree.make_automaton()

    sentence = ''.join([item.value for item in parse_result.contents])
    matched_concepts = actree.iter(sentence)

    return matched_concepts


###################
# 算分 以及 主谓宾计算
###################

# 读取主谓宾统计文件
with open('./datasets/nsubj_pr_stat') as nsubj_file:
    nsubj_dict = {}
    lines = nsubj_file.readlines()
    for line in lines:
        line = line.strip().split('\t')
        nsubj_dict[line[0]] = int(line[1])

with open('./datasets/dobj_pr_stat') as dobj_file:
    dobj_dict = {}
    lines = dobj_file.readlines()
    for line in lines:
        line = line.strip().split('\t')
        dobj_dict[line[0]] = int(line[1])

with open('./datasets/amod_pr_stat') as amod_file:
    amod_dict = {}
    lines = amod_file.readlines()
    for line in lines:
        line = line.strip().split('\t')
        amod_dict[line[0]] = int(line[1])


def cal_score(structure, score=0):
    score += structure.freq
    for item in structure.contents:
        if isinstance(item, Special_phrase):
            score = cal_score(item, score)

    # 主谓宾分数计算
    if structure.meaning != '-':
        relations = structure.meaning.split(',')
        for relation in relations:
            relation = relation.split(':')
            if relation[0] == 'subj':
                if relation[1] != '?' and relation[2] != '?':
                    subj = structure.contents[int(relation[1])].core_word
                    verb = structure.contents[int(relation[2])].core_word
                    nsubj = subj + '|' + verb
                    if nsubj in nsubj_dict:
                        score = score * nsubj_dict[nsubj]
            if relation[0] == 'dobj':
                if relation[1] != '?' and relation[2] != '?':
                    verb = structure.contents[int(relation[1])].core_word
                    obj = structure.contents[int(relation[2])].core_word
                    dobj = obj + '|' + verb
                    if dobj in dobj_dict:
                        score = score * dobj_dict[dobj]
    return score


###################
# Parataxis
###################
def parataxis_finder():
    return


###################
# extract k point
###################
def extract_kpoints(sub_sentence):
    k_points = []
    if sub_sentence.meaning != '-':
        pass
    return k_points


###################
# hanlp parse
###################
def hanlp_parse(text):
    ha2stanford_dict = {}
    with open('datasets/ha2stanford') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip().split('\t')
            ha2stanford_dict[line[0]] = line[1]
    ha_parse_result = HanLP.parseDependency(text)
    # print(ha_parse_result)
    words = []
    for i in ha_parse_result.word:
        word = Word(i.LEMMA, ha2stanford_dict[i.CPOSTAG], i.CPOSTAG)
        words.append(word)
    parse_result = Parse_result(words)
    return parse_result


###################
# jieba parse
###################
def jieba_parse(text):
    parse_result = jieba.posseg.cut(text)
    words = []
    pos_tags = []
    for word, flag in parse_result:
        words.append(word)
        pos_tags.append(flag)
    clean_text = "".join(words)
    return words, pos_tags, clean_text


###################
# stanford parse
###################
def stanford_simplify(pos_tags):  # stanford 的postag 是列表，列表元素是（词，词性）的元组
    stanford_simplify_dict = {}
    with open('datasets/stanford_simplify') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip().split('\t')
            stanford_simplify_dict[line[0]] = line[1]
    result = []
    for word, pos_tag in pos_tags:
        result.append((word, stanford_simplify_dict[pos_tag]))
    return result


def stanford_parse(text):
    return


###################
# 读取短语库和句式库
###################
# old version
# with open('./datasets/new_test_file') as pattern_file:
#     phrase_patterns = []
#     lines = pattern_file.readlines()
#     del(lines[0])
#     for line in lines:
#         line = line.strip().split('\t')
#         phrase_pattern = Special_pattern(line[0], line[1], line[2], line[3], line[4])
#         phrase_patterns.append(phrase_pattern)

with open('./datasets/new_test_file2') as pattern_file:
    phrase_patterns = []
    lines = pattern_file.readlines()
    del(lines[0])
    for line in lines:
        line = line.strip().split('\t')
        phrase_pattern = Special_pattern(line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7])
        phrase_patterns.append(phrase_pattern)

with open('./datasets/ss_pattern') as ss_file:
    ss_patterns = []
    lines = ss_file.readlines()
    del(lines[0])
    for line in lines:
        line = line.strip().split()
        if len(line) > 1:
            ss_pattern = Sub_sentence_pattern(line[0], line[1], line[2], line[3])
            ss_patterns.append(ss_pattern)


KB = Knowledge_base()


###################
# sParser类 通用parser
###################
class sParser(object):
    def __init__(self, KB, mode='default', current_environment=None):
        self.mode = mode
        self.KB = KB
        self.current_environment = current_environment

    def parse(self, text):

        result = {}
        result['parse_results'] = []
        result['k_points'] = []

        # 1，判定文本类型。对话/新闻稿/公告 等。可自动发现，自动学习
        # to do

        # 2，分句。
        # to do 优化分句
        sentences = cut_sent(text)

        # 3，逐句parse
        for sentence in sentences:
            # 分句的句号处理 可以直接进行分类
            # to do
            sentence = re.sub('([。！？\?])', '', sentence)
            sub_sentences = seg2sub_sentence(sentence)

            for sub_sentence in sub_sentences:
                # print(sub_sentence.value)
                if isinstance(sub_sentence, Pre_sub_sentence):
                    print(sub_sentence.value)
                    # if self.mode == 'special1':  # 专门处理百度信息抽取预处理好的语料

                    parse_result = hanlp_parse(sub_sentence.value)
                    sub_sentence.raw_parse_result = parse_result

                    all_results = []
                    check_special_phrase(parse_result, all_results)

                    # 返回所有results
                    if self.mode == 'default':
                        ss_result = all_results
                    # 返回最高分result
                    if self.mode == 'learning':
                        final_result_score = 0
                        ss_result = []
                        for parse_result in all_results:
                            score = cal_score(parse_result)
                            if score > final_result_score:
                                ss_result = parse_result
                        if ss_result == []:
                            result['parse_results'].append(sub_sentence)  # 无解析结果返回原始的 Pre_sub_sentence
                        else:
                            result['parse_results'].append(ss_result)  # 有解析结果返回Sub_sentence
                else:
                    result['parse_results'].append(sub_sentence)

        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c",
                        "--corpus",
                        default="./init_data/train.txt",
                        help="corpus file folder for training",
                        required=False)
    args = parser.parse_args()

    # parse_result = hanlp_parse('纵横中文网。')
    # check_known_concepts(parse_result)

    text = '北京（中国的首都）是北京。'
    text = '宝马和奔驰联合开发无人驾驶技术'

    parser = sParser(KB, mode='learning')
    rst = parser.parse(text)
    print(rst)

'''
    # ################## old version #############
    ###################
    # 读取待处理语料，格式为每行一个数据，每个数据可以是多句话组成
    ###################
    try:
        corpus = open(args.corpus, 'r', encoding='utf-8')
    except Exception:
        corpus = open(args.corpus, 'r', encoding='gbk')

    line = corpus.readline()
    while line:
        line = line.strip()

        parser.parse(line)
        # 语料分句
        # sentences = seg2sentence(line)
        sentences = cut_sent(line)
        # CRFnewSegment_new = HanLP.newSegment("crf")
        # s = CRFnewSegment_new.seg2sentence(line)
        # print(line)
        # print(sentences)

        # 对句子进行parse
        # parse_result, clean_text, stanford_pos = hanlp_parse(line)
        # print(parse_result, clean_text, stanford_pos)
        # check_xps(parse_result)

        # 拆分子句
        for sentence in sentences:
            sentence = re.sub('([。！？\?])', '', sentence)
            sub_sentences = seg2sub_sentence(sentence)

            # parse
            # print(sub_sentences)
            # parse_result = hanlp_parse(line)

            # # find_single_special_pattern(parse_result, phrase_patterns[0])

            # final_results = []
            # check_special_phrase(parse_result, final_results)
            # print(len(final_results))
            # break
        # break
        line = corpus.readline()
    corpus.close()
'''
