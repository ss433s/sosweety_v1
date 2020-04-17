import sys
import json
import ahocorasick
sys.path.append("..")

database_version = './fake_database_empty'
# database_version = './fake_database'


###################
# 定义和读取知识库
###################
class Concept(object):
    def __init__(self, concept_id, word, methods, properties):
        self.concept_id = concept_id
        self.word = word
        self.methods = methods
        self.properties = properties


class Method(object):
    def __init__(self, method_id, word, code='-'):
        self.method_id = method_id
        self.word = word
        self.code = code


class Fact(object):
    def __init__(self, fact_id, concept1=None, restriction1=None,
                                concept2=None, restriction2=None,
                                relation=None, relation_restriction=None,
                                time=None, location=None,
                                confidence=None):
        self.fact_id = fact_id
        self.concept1 = concept1
        self.restriction1 = restriction1
        self.concept2 = concept2
        self.restriction2 = restriction2
        self.relation = relation
        self.relation_restriction = relation_restriction
        self.time = time
        self.location = location
        self.confidence = confidence


# 读取concept表 concepts为字典 key为concept_id 值是Concept类
with open(database_version + '/Concept_table') as concept_table_file:
    concepts = {}
    lines = concept_table_file.readlines()
    del(lines[0])
    for line in lines:
        line = line.strip().split('\t')
        if len(line) > 1:
            concept = Concept(int(line[0]), line[1], json.loads(line[2]), json.loads(line[3]))
            concepts[concept.concept_id] = concept

# 读取method表 methods为字典 key为method_id 值是method类
with open(database_version + '/Method_table') as method_table_file:
    methods = {}
    lines = method_table_file.readlines()
    del(lines[0])
    for line in lines:
        line = line.strip().split()
        if len(line) > 1:
            method = Method(int(line[0]), line[1], line[2])
            methods[method.method_id] = method

# 读取fact表 facts为字典 key为fact_id 值是fact类
with open(database_version + '/Fact_table') as fact_table_file:
    facts = {}
    lines = fact_table_file.readlines()
    del(lines[0])
    for line in lines:
        line = line.strip().split()
        if len(line) > 1:
            fact_id = int(line[0])
            fact = Fact(fact_id)
            for i in range(1, 9):
                if line[i] != '-':
                    if i == 1:
                        fact.concept1 = line[i]
                    if i == 2:
                        fact.restriction1 = line[i]
                    if i == 3:
                        fact.concept2 = line[i]
                    if i == 4:
                        fact.restriction2 = line[i]
                    if i == 5:
                        fact.relation = line[i]
                    if i == 6:
                        fact.relation_restriction = line[i]
                    if i == 7:
                        fact.time = line[i]
                    if i == 8:
                        fact.location = line[i]
                    if i == 9:
                        fact.confidence = line[i]
            facts[fact_id] = fact

# 读取Word表（词对应各种内部储存的表） 构建word2id dict
# word 对应的是[id, type, freq, confidence]的列表
with open(database_version + '/Word_table') as word_table_file:
    word2id_dict = {}
    lines = word_table_file.readlines()
    del(lines[0])
    for line in lines:
        line = json.loads(line)
        if len(line) > 1:
            if line[0] in word2id_dict:
                word2id_dict[line[0]].append([int(line[1]), line[2], int(line[3]), float(line[4])])
            else:
                word2id_dict[line[0]] = [[int(line[1]), line[2], int(line[3]), float(line[4])]]


# 读取concept relation 表 构建concept_relation 字典  key为concept1_id 值为 [concept2_id, type]
with open(database_version + '/Concept_relation_table') as concept_relation_table_file:
    concept_relations = {}
    lines = concept_relation_table_file.readlines()
    del(lines[0])
    for line in lines:
        line = line.strip().split()
        if len(line) > 1:
            if line[0] in concept_relations:
                concept_relations[int(line[0])].append([int(line[1]), int(line[2])])
            else:
                concept_relations[int(line[0])] = [[int(line[1]), int(line[2])]]


class Knowledge_base(object):

    # 为了换sql版本 不存只封装函数和查询能力
    # def __init__(self):
    #     self.concepts = concepts
    #     self.methods = methods
    #     self.facts = facts
    #     self.word2id_dict = word2id_dict
    #     self.concept_relations = concept_relations

    # 查询concept word
    def get_concept_word(self, concept_id):
        word = concepts[concept_id].word
        return word

    # 查询一个词的所有对应id
    def get_word_ids(self, word):
        try:
            word_ids = word2id_dict[word]
            return word_ids
        except Exception:
            return []

    # 查询一个concept id 所属于的concept
    def get_concept_relations(self, concept_id):
        try:
            single_concept_relations = concept_relations[concept_id]
            return single_concept_relations
        except Exception:
            return []

    # 判定一个词语是否属于某种concept，不递归，多义词返回concept_id
    def word_belong_to_concept(self, word, concept_id):
        result = []
        if word in word2id_dict:
            word_ids = word2id_dict[word]
            for concept1_id, word1_type, freq, confidence in word_ids:
                if word1_type == 'concept' and concept1_id in concept_relations:
                    concept2s = concept_relations[concept1_id]
                    for concept2_id, word2_type, _, _ in concept2s:
                        if word2_type == 'concept' and concept2_id == concept_id:
                            result.append([concept1_id, freq, confidence])
        return result

    # 检查所有词表,返回一段文字的匹配词列表
    def checkout_words(self, text):
        word_set = set()
        matched_words = []
        for word in word2id_dict:
            word_set.add(word)

        actree = ahocorasick.Automaton()
        for word in word_set:
            actree.add_word(word, word)
        actree.make_automaton()
        rst = actree.iter(text)
        for actree_word in rst:
            matched_words.append(actree_word[1])
        return matched_words

    # fake database version
    def merge(self, k_points):
        update_list = []
        for k_point in k_points:
            if k_point.k_type == 'concept':
                if not ['Concept', concepts] in update_list:
                    update_list.append(['Concept', concepts])
                if 'concept_id' in k_point.content:
                    concept_id = k_point.content['concept_id']
                    if 'methods' in k_point.content:
                        tmp = concepts[concept_id].methods + k_point.content['methods']
                        concepts[concept_id].methods = list(set(tmp))
                    if 'properties' in k_point.content:
                        tmp = concepts[concept_id].properties + k_point.content['properties']
                        concepts[concept_id].properties = list(set(tmp))
                else:
                    concept_id = len(concepts.keys())
                    concepts[concept_id] = Concept(concept_id, k_point.content['word'], [], [])
                    # concepts[concept_id]['word']
                    if 'methods' in k_point.content:
                        concepts[concept_id].methods = k_point.content['methods']
                    if 'properties' in k_point.content:
                        concepts[concept_id].properties = k_point.content['properties']

            if k_point.k_type == 'method':
                if not ['Method', methods] in update_list:
                    update_list.append(['Method', methods])
                if 'method_id' in k_point.content:
                    continue
                else:
                    method_id = len(methods.keys())
                    methods[method_id] = Method(method_id, k_point.content['word'], [])

            # 需外部控制传入fact的各种限制，先保证concept和method都存在再导入fact
            # 先导入，在归纳学习时再做合并
            if k_point.k_type == 'fact':
                if not ['Fact', facts] in update_list:
                    update_list.append(['Fact', facts])
                fact = k_point.content['fact']
                facts[fact.fact_id] = fact

        for file_pre, file_dict in update_list:
            file_name = database_version + '/' + file_pre + '_table'
            # with open(file_name, 'r') as f:
            #     line1 = f.readline()
            with open(file_name, 'w') as f:
                heads = []
                for k, _ in vars(file_dict[0]).items():
                    heads.append(k)
                heads_str = '#' + '\t'.join(heads)
                f.write(heads_str + '\n')
                for i in file_dict:
                    value_list = []
                    for k, v in vars(file_dict[i]).items():
                        if v is not None:
                            if isinstance(v, str):
                                value_list.append(v)
                            else:
                                value_list.append(json.dumps(v, ensure_ascii=False))
                        else:
                            value_list.append('-')
                    f.write('\t'.join(value_list) + '\n')
        return


class K_point(object):
    # type 包括 concept， method， fact， word等
    # content 格式为字典
    # content 包括id的话，为更新属性, 不包含为新增
    # fact 需先处理concept入库问题  必须先传入concept 再生出fact 然后传入fact
    def __init__(self, k_type, content):
        self.k_type = k_type
        self.content = content


# test
if __name__ == '__main__':
    KB = Knowledge_base()
    rst = KB.word_belong_to_concept("北京大学", 0)
    k_point = K_point('concept', {'concept_id': 2, 'properties': [5]})
    # k_point = K_point('concept', {'word': '南京', 'methods': [0]})
    fact = Fact(1)
    # k_point = K_point('fact', {'fact': fact})
    KB.merge([k_point])
    # print(facts)
    # print(rst)
