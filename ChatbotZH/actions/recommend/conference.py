from typing import Any, Dict, List, Text
import json
from pymongo import MongoClient
import traceback
from actions.dateUtils import date_treat
from actions import translate
from actions.param import base_path
from actions.Database.Mongo import MongoDB

# 判断中英文
def judgeLanguage(text):
    en = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM -_,./~"
    for i in text:
        if i in en:
            continue
        else:
            return 1  # 中文

    return 0  # 英文


# 方向中英文映射
def getCategory(ch):
    fw = open(base_path + 'category.json', 'r', encoding='UTF-8')
    task = json.load(fw)
    fw.close()

    if ch in task.keys():
        return task[ch]
    else:
        return None


class searchConference:
    def __init__(self, dict):
        # 槽值字典
        self.slot_dic = {
            'conference': dict['name'],  # 会议名
            'location': dict['location'],  # 地点
            'category': dict['category'],  # 类别
            'extended': dict['extended'],  # 是否延期
            'CCF': dict['ccf'],  # ccf等级
            'CORE': dict['core'],  # core等级
            'QUALIS': dict['qualis'],  # qualis等级
            'deadline_from': dict['deadline_from'], # 截稿日期时间段
            'deadline_to': dict['deadline_to'],
            'notice_from': dict['notice_from'],  # 通知日期时间段
            'notice_to': dict['notice_to'],
            'begin_from': dict['begin_from'],  # 举行日期时间段
            'begin_to': dict['begin_to']
        }

        # 地点 ch to en
        if self.slot_dic['location'] is not None and judgeLanguage(self.slot_dic['location']) == 1:
            self.slot_dic['location'] = translate.translateBaidu(self.slot_dic['location'])

        # 方向 ch to en
        if self.slot_dic['category'] is not None:
            if judgeLanguage(self.slot_dic['category']) == 1:
                self.slot_dic['category'] = getCategory(self.slot_dic['category'])
            elif self.slot_dic['category'] == 'CV':
                self.slot_dic['category'] = 'COMPUTER VISION'
            elif self.slot_dic['category'] == 'OS':
                self.slot_dic['category'] = 'OPERATING SYSTEMS'
            elif 'NATURAL LANGUAGE PROCESS' in self.slot_dic['category']:
                self.slot_dic['category'] = 'NLP'
        
        # 统一格式
        if self.slot_dic['conference'] is not None:
            self.slot_dic['conference'] = self.slot_dic['conference'].upper()
        if self.slot_dic['location'] is not None:
            self.slot_dic['location'] = self.slot_dic['location'].title()
        if self.slot_dic['category'] is not None:
            self.slot_dic['category'] = self.slot_dic['category'].upper()
        if self.slot_dic['extended'] is not None:
            self.slot_dic['extended'] = 'Extended'
        if self.slot_dic['CCF'] is not None:
            self.slot_dic['CCF'] = self.slot_dic['CCF'].lower()
        if self.slot_dic['CORE'] is not None:
            self.slot_dic['CORE'] = self.slot_dic['CORE'].lower()
        if self.slot_dic['QUALIS'] is not None:
            self.slot_dic['QUALIS'] = self.slot_dic['QUALIS'].lower()

    # 槽值是否为空
    def isEmpty(self):
        if self.slot_dic['deadline_from'] is None and self.slot_dic['deadline_to'] is None and self.slot_dic[
            'conference'] is None and self.slot_dic['location'] is None and self.slot_dic['category'] is None and \
                self.slot_dic['CCF'] is None and self.slot_dic['CORE'] is None and self.slot_dic['QUALIS'] is None and \
                    self.slot_dic['notice_from'] is None and self.slot_dic['notice_to'] is None and \
                        self.slot_dic['begin_from'] is None and self.slot_dic['begin_to'] is None:
            return True
        return False

    # 从数据库检索
    def search(self):
        # slot为空
        if self.isEmpty():
            return []
        # 检索query
        myquery = {'type': 'conf'}
        if self.slot_dic['conference'] is not None:
            myquery['acronym'] = self.slot_dic['conference']
        if self.slot_dic['location'] is not None:
            dict = {'$regex': self.slot_dic['location']}  # 正则匹配 包含关系
            myquery['Location'] = dict
        if self.slot_dic['category'] is not None:
            if self.slot_dic['category'] == 'AI':
                myquery['$or'] = [{'Categories': {'$regex': 'AI'}}, {'Categories': {'$regex': 'NLP'}}, {'Categories': {'$regex': 'COMPUTER VISION'}}]
            else:
                dict = {'$regex': self.slot_dic['category']}  # 正则匹配 包含关系
                myquery['Categories'] = dict
        if self.slot_dic['extended'] is not None:
            myquery['Extended'] = 'Extended'
        if self.slot_dic['CCF'] is not None:
            x = self.slot_dic['CCF'].split(',')
            ccf = []
            for i in x:
                ccf.append(i)
            if len(ccf) > 0:
                dict = {'$in': []}
                dict['$in'].extend(ccf)
                myquery['CCF'] = dict
        if self.slot_dic['CORE'] is not None:
            x = self.slot_dic['CORE'].split(',')
            core = []
            for i in x:
                core.append(i)
            if len(core) > 0:
                dict = {'$in': []}
                dict['$in'].extend(core)
                myquery['CORE'] = dict
        if self.slot_dic['QUALIS'] is not None:
            x = self.slot_dic['QUALIS'].split(',')
            qualis = []
            for i in x:
                qualis.append(i)
            if len(qualis) > 0:
                dict = {'$in': []}
                dict['$in'].extend(qualis)
                myquery['QUALIS'] = dict
        if self.slot_dic['deadline_from'] is not None and self.slot_dic['deadline_to'] is not None:
            dict = {'$gte': self.slot_dic['deadline_from'], '$lte': self.slot_dic['deadline_to']}
            myquery['Deadline'] = dict
        if self.slot_dic['notice_from'] is not None and self.slot_dic['notice_to'] is not None:
            dict = {'$gte': self.slot_dic['notice_from'], '$lte': self.slot_dic['notice_to']}
            myquery['Notice'] = dict
        if self.slot_dic['begin_from'] is not None and self.slot_dic['begin_to'] is not None:
            dict = {'$gte': self.slot_dic['begin_from'], '$lte': self.slot_dic['begin_to']}
            myquery['Begin'] = dict
        # 限制返回字段
        projection = {'_id': 0}
        # 查询
        print('query', myquery)
        mongo = MongoDB()
        result = mongo.find_conference(myquery, projection)
        # result = self.find_detail(myquery, projection)
        # 调整
        begin = -1
        end = -1
        confs = []
        confnull = []
        confnames = []
        for i in result:
            # 必须做的调整
            i['name'] = i['name'].replace('|', ' ')
            # 重新排序
            if i['CCF'] is None:
                confnull.append(i)
            else:
                confs.append(i)
        confs.extend(confnull)
        conf = []
        for i in confs:
            if i['acronym'] in confnames:
                continue
            else:
                confnames.append(i['acronym'])
                conf.append(i)

        return conf

    # 按query select eg: projection必须有CCF和Viewed
    @staticmethod
    def find_detail(query, projection):
        try:
            url = 'mongodb://root:HammerScholarRoot0@hammerscholar-pub.mongodb.zhangbei.rds.aliyuncs.com:3717,hammerscholarsecondary-pub.mongodb.zhangbei.rds.aliyuncs.com:3717/admin?replicaSet=mgset-505729903'
            # connect to mongodb
            client = MongoClient(url)
            db = client.HammerScholar
            detail = db.detail

            # find and order 1.CCF 2.Viewed 3.Begin
            result = [doc for doc in detail.find(query, projection).sort([("CCF", 1), ("year", -1), ("Viewed", -1)])]

            return result
        except:
            traceback.print_exc()


if __name__ == '__main__':
    dict = {'dateYear_from': None, 'dateYear_to': None, 'dateMonth_from': None, 'dateMonth_to': None,
            'dateDay_from': None, 'dateDay_to': None, 'name': None, 'location': None,
            'category': 'NLP', 'deadline': None, 'notice': None, 'extended': None,
            'ccf': None, 'core': None, 'qualis': None}
    sc = searchConference(dict)
    print(sc.slot_dic)
    sc.search()