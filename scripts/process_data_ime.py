import json
from xml.dom.minidom import parse
import xml.dom.minidom
import os
import re
from pytorch_pretrained_bert.tokenization import BertTokenizer


tokenizer = BertTokenizer.from_pretrained("bert-base-chinese", do_lower_case=True)

stop={"'",'"',',','.','?','/','[',']','{','}','+','=','*','&','(',')','，','。','？',
      '“','”','’','‘','、','？','！','【','】','《','》','（','）','・','&quot;','——',
      '-','———',':','：','!','@','#','$','%','&',';','……','；','—','±'}
ime_words={'伯', '吓', '拉', '殷', '菲', '凿', '熟', '看', '别', '喷', '打', '核', '约', '雀', '俩', '的', '格', '没', '择',
           '不', '嚼', '暴', '炮', '强', '奇', '脏', '好', '乘', '更', '号', '把', '省', '淋', '脚', '种', '几', '还', '一',
           '蹬', '作', '呱', '喝', '劈', '间', '笼', '凉', '秤', '泡', '壳', '趟', '颤', '占', '肚', '落', '荷', '冲', '搂',
           '发', '拓', '晕', '宿', '曾', '泊', '咖', '咔', '钻', '塞', '曝', '仔', '咧', '撩', '嘎'}
data_path="/hdfs/ipgsp/t-hasu/ppdata/zh-CN/"
ime_path="/hdfs/ipgsp/t-hasu/ppdata/Merge/"
output_path="/hdfs/ipgsp/t-hasu/ppdata/data-ime-3M/"
if not os.path.exists(output_path):
    os.mkdir(output_path)
phones=set()
train=[]
test_story=[]
test_news=[]
test_chat=[]
max_length_cut=64
words=set()
words_train=set()
test_set=set([p[11:-4] for p in os.listdir(data_path+"TestCase/Story")])
train_set=set(os.listdir(data_path+"Annotation"))
ime_set=test_set-train_set
print(train_set)
assert not train_set-test_set

dct={}


def get_test(path,test):
    for word in os.listdir(path):
        print("Test set processing...", word)
        DOMTree = xml.dom.minidom.parse(path+word)
        collection = DOMTree.documentElement
        cases = collection.getElementsByTagName("case")
        dct[re.search('_.*\.',word).group()[1:-1]] = cases[0].getAttribute('pron_polyword')
        for case in cases:
            js_data = {}
            js_data['text'] = tokenizer.tokenize(case.getElementsByTagName("input")[0].childNodes[0].data)
            js_data['position'] = -1
            js_data['char'] = case.getAttribute('pron_polyword')
            if js_data['char'] not in ime_words:
                break
            for i,w in enumerate(js_data['text']):
                if w==js_data['char']:
                    js_data['position']=i
            # cut the text if too long
            if js_data['position'] > max_length_cut:
                # print(js_data['position'])
                js_data['text'] = js_data['text'][js_data['position'] - max_length_cut:]
                js_data['position'] = max_length_cut
            #assert js_data['position'] != -1
            #assert js_data['text'][js_data['position']] == case.getAttribute('pron_polyword')
            if js_data['position']==-1:
                print(js_data['char'])
            js_data['phone'] = [[js_data['position'], js_data['char'] + case.getElementsByTagName("part")[0].childNodes[0].data]]
            phones.add(js_data['phone'][-1][1])
            words.add(js_data['char'])
            #js_data['text']=' '.join(js_data['text'])
            test.append(js_data)


def get_train(path, word):
    DOMTree = xml.dom.minidom.parse(path)
    char = dct[word]
    words_train.add(char)
    collection = DOMTree.documentElement
    sis = collection.getElementsByTagName("si")
    for si in sis:
        js_data = {}
        js_data['text'] = ""
        js_data['position'] = -1
        js_data['char'] = char
        pho='_'

        # get the pronunciation
        for i,w in enumerate(si.getElementsByTagName("w")):
            js_data['text']+=w.getAttribute('v')
            if w.getAttribute('v') == char:
                pho=js_data['char'] + w.getAttribute('p')
        if pho=='_': # wrong case
            print(js_data['text'])
            continue
        # get the position
        js_data['text'] = tokenizer.tokenize(js_data['text'])
        for i,w in enumerate(js_data['text']):
            if w==char:
                js_data['position']=i
        # cut the text if too long
        if js_data['position'] > max_length_cut:
            js_data['text'] = js_data['text'][js_data['position'] - max_length_cut:]
            js_data['position'] = max_length_cut
        js_data['phone'] = [[js_data['position'], pho]]
        #assert js_data['position'] > -1
        #assert js_data['text'][js_data['position']] == char

        phones.add(js_data['phone'][-1][1])
        #js_data['text'] = ' '.join(js_data['text'])
        train.append(js_data)

def get_train_ime(path,ime_words,ime_len=18000000):
    with open(path,encoding='utf8') as f:
        for i,line in enumerate(f):
            if i%1000000==0:
                print(i)
            if i>=ime_len:
                break
            if i%4 == 0:
                js_data = {}
                js_data['text'] = tokenizer.tokenize(line)
                js_data['position'] = -1
                js_data['char'] = '_'
                js_data['phone'] = []
            if i%4==1:
                phones_list=line.strip().split('\t')
                texts_list=js_data['text']
                if len(phones_list)!=len(texts_list):
                    print(texts_list,phones_list)
                    continue
                for j in range(len(texts_list)):
                    if j<62 and texts_list[j] in ime_words:
                        words_train.add(texts_list[j])
                        js_data['phone'].append([j,texts_list[j]+phones_list[j]])
                        phones.add(texts_list[j]+phones_list[j])
                        js_data['position'] = j
            if i%4==2:
                if js_data['phone']:
                    train.append(js_data)


# test
get_test(data_path+'TestCase/Story/',test_story)
get_test(data_path+'TestCase/News/',test_news)
get_test(data_path+'TestCase/ChitChat/',test_chat)
print(dct)
#ime_words={dct[w] for w in ime_set}

print(len(phones),sorted(list(phones)))
phones_test=phones.copy()

#IME
for txt in os.listdir(ime_path)[0:1]:
    print(txt)
    get_train_ime(ime_path+txt,ime_words)
print(len(phones),sorted(list(phones)))
phones_ime=phones.copy()


#print(sorted(list(phones_train-phones_test)))
print(sorted(list(phones_ime-phones_test)))

#print(words-words_train)
print(len(train),len(test_story),len(test_news),len(test_chat))

#save
with open(output_path+"/train.json",'w',encoding='utf8') as f:
    f.write(json.dumps(train, ensure_ascii=False))

with open(output_path+"/test_story.json",'w',encoding='utf8') as f:
    f.write(json.dumps(test_story, ensure_ascii=False))
with open(output_path+"/test_news.json",'w',encoding='utf8') as f:
    f.write(json.dumps(test_news, ensure_ascii=False))
with open(output_path+"/test_chat.json",'w',encoding='utf8') as f:
    f.write(json.dumps(test_chat, ensure_ascii=False))

info={"words_test":sorted(list(words)),
      #"words_prepared":sorted(list(dct[w] for w in train_set)),
      "words_ime":sorted(list(ime_words)),
      "phones":sorted(list(phones))}
with open(output_path+"/info.json",'w',encoding='utf8') as f:
    f.write(json.dumps(info, ensure_ascii=False))
