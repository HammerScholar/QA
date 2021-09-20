from pymongo import MongoClient
import traceback
import re

pattern = ['大于等于(-?\d+)(\.\d+)?', '大于(-?\d+)(\.\d+)?', '小于等于(-?\d+)(\.\d+)?', '小于(-?\d+)(\.\d+)?', 
    '>=(-?\d+)(\.\d+)?', '>(-?\d+)(\.\d+)?', '<=(-?\d+)(\.\d+)?', '<(-?\d+)(\.\d+)?', '在(-?\d+)(\.\d+)?到(-?\d+)(\.\d+)?', '介于(-?\d+)(\.\d+)?和(-?\d+)(\.\d+)?',
    '(-?\d+)(\.\d+)?<<(-?\d+)(\.\d+)?', '(-?\d+)(\.\d+)?<=<(-?\d+)(\.\d+)?', '(-?\d+)(\.\d+)?<<=(-?\d+)(\.\d+)?', '(-?\d+)(\.\d+)?<=<=(-?\d+)(\.\d+)?', '介于(-?\d+)(\.\d+)?到(-?\d+)(\.\d+)?',
    '最[高大]']

class searchJournal():
    def __init__(self, dict):
        # 槽值字典
        self.slot_dic = {
            'journal_name': dict['journal_name'], # 全称或简称
            'journal_category': dict['journal_category'],  # 期刊方向
            'ifs': dict['ifs'],  # IF
            'h_index': dict['h_index'],  # h_index
            'fenqu': dict['fenqu'], # fenqu
            'CCF': dict['ccf'],
            'deadline_from': dict['deadline_from'], # 截稿日期时间段
            'deadline_to': dict['deadline_to'],
            'publisher': dict['publisher']
        }
        if self.slot_dic['journal_name'] is not None:
            self.slot_dic['journal_name'] = self.slot_dic['journal_name'].upper()
        if self.slot_dic['fenqu'] is not None: # 防止SCI1区歧义
            self.slot_dic['journal_name'] = None
        if self.slot_dic['CCF'] is not None:
            self.slot_dic['CCF'] = self.slot_dic['CCF'].upper()

        self.compare = None # if的比较表达式
        self.sort = None # 找最大的if or h_index
        if self.slot_dic['ifs'] is not None:
            self.slot_dic['ifs'] = self.slot_dic['ifs'].upper().replace('影响因子', '').replace('IF', '').replace(' ', '')
            if re.match(pattern[0], self.slot_dic['ifs']):
                self.compare = {'$gte': float(self.slot_dic['ifs'][4:])}
            elif re.match(pattern[1], self.slot_dic['ifs']):
                self.compare = {'$gt': float(self.slot_dic['ifs'][2:])}
            elif re.match(pattern[2], self.slot_dic['ifs']):
                self.compare = {'$lte': float(self.slot_dic['ifs'][4:])}
            elif re.match(pattern[3], self.slot_dic['ifs']):
                self.compare = {'$lt': float(self.slot_dic['ifs'][2:])}
            elif re.match(pattern[4], self.slot_dic['ifs']):
                self.compare = {'$gte': float(self.slot_dic['ifs'][2:])}
            elif re.match(pattern[5], self.slot_dic['ifs']):
                self.compare = {'$gt': float(self.slot_dic['ifs'][1:])}        
            elif re.match(pattern[6], self.slot_dic['ifs']):
                self.compare = {'$lte': float(self.slot_dic['ifs'][2:])}
            elif re.match(pattern[7], self.slot_dic['ifs']):
                self.compare = {'$lt': float(self.slot_dic['ifs'][1:])}
            elif re.match(pattern[8], self.slot_dic['ifs']):
                x = self.slot_dic['ifs'][1:].split('到')
                self.compare = {'$gt': float(x[0]), '$lt': float(x[1])}
            elif re.match(pattern[9], self.slot_dic['ifs']):
                x = self.slot_dic['ifs'][2:].split('和')
                self.compare = {'$gt': float(x[0]), '$lt': float(x[1])}
            elif re.match(pattern[10], self.slot_dic['ifs']):
                x = self.slot_dic['ifs'].split('<<')
                self.compare = {'$gt': float(x[0]), '$lt': float(x[1])}
            elif re.match(pattern[11], self.slot_dic['ifs']):
                x = self.slot_dic['ifs'].split('<=<')
                self.compare = {'$gt': float(x[0]), '$lt': float(x[1])}
            elif re.match(pattern[12], self.slot_dic['ifs']):
                x = self.slot_dic['ifs'].split('<<=')
                self.compare = {'$gt': float(x[0]), '$lt': float(x[1])}
            elif re.match(pattern[13], self.slot_dic['ifs']):
                x = self.slot_dic['ifs'].split('<=<=')
                self.compare = {'$gt': float(x[0]), '$lt': float(x[1])}
            elif re.match(pattern[14], self.slot_dic['ifs']):
                x = self.slot_dic['ifs'][2:].split('到')
                self.compare = {'$gt': float(x[0]), '$lt': float(x[1])}
            elif re.match(pattern[15], self.slot_dic['ifs']):
                self.sort = 'IF'
        
        self.h_index = None # h_index的比较表达式
        if self.slot_dic['h_index'] is not None:
            self.slot_dic['h_index'] = self.slot_dic['h_index'].upper().replace('H', '').replace('5', '').replace('-', '').replace('指数', '').replace(' ', '')
            if re.match(pattern[0], self.slot_dic['h_index']):
                self.h_index = {'$gte': float(self.slot_dic['h_index'][4:])}
            elif re.match(pattern[1], self.slot_dic['h_index']):
                self.h_index = {'$gt': float(self.slot_dic['h_index'][2:])}
            elif re.match(pattern[4], self.slot_dic['h_index']):
                self.h_index = {'$gte': float(self.slot_dic['h_index'][2:])}
            elif re.match(pattern[5], self.slot_dic['h_index']):
                self.h_index = {'$gt': float(self.slot_dic['h_index'][1:])}
            elif re.match(pattern[15], self.slot_dic['h_index']):
                self.sort = 'h_index'


    # 槽值是否为空
    def isEmpty(self):
        if self.slot_dic['journal_name'] is None and self.slot_dic['journal_category'] is None and self.slot_dic['ifs'] is None and self.slot_dic['h_index'] is None and self.slot_dic['fenqu'] is None \
            and self.slot_dic['CCF'] is None and self.slot_dic['deadline_from'] is None and self.slot_dic['deadline_to'] is None and self.slot_dic['publisher'] is None:
            return True
        return False

    def search(self):
        try:
            # slot为空
            if self.isEmpty():
                return []
                
            # 检索query
            myquery = {'type': 'journal'}
            if self.slot_dic['journal_category'] is not None:
                myquery['$or'] = [{'large_area': {'$regex': self.slot_dic['journal_category']}}, {'small_area': {'$regex': self.slot_dic['journal_category']}}]
            if self.slot_dic['journal_name'] is not None:
                if self.slot_dic['journal_name'] == 'IEEE':
                    myquery['name'] = {'$regex': '^IEEE', '$options': 'i'}
                else:
                     myquery['$or'] = [{'name': {'$regex': '^'+self.slot_dic['journal_name']+'$', '$options': 'i'}},
                        {'acronym': {'$regex': '^'+self.slot_dic['journal_name']+'$', '$options': 'i'}}]
            if self.compare is not None:
                myquery['IF'] = self.compare
            if self.h_index is not None:
                myquery['h_index'] = self.h_index  
            if self.slot_dic['fenqu'] is not None:
                myquery['fenqu'] = self.slot_dic['fenqu']
            if self.slot_dic['CCF'] is not None:
                myquery['CCF'] = self.slot_dic['CCF']
            if self.slot_dic['publisher'] is not None:
                myquery['Publisher'] = {'$regex': '^'+self.slot_dic['publisher']+'$', '$options': 'i'}
            if self.slot_dic['deadline_from'] is not None and self.slot_dic['deadline_to'] is not None :
                dict = {'$gte': self.slot_dic['deadline_from'], '$lte': self.slot_dic['deadline_to']}
                myquery['Deadline'] = dict
            # 限制返回字段
            projection = {'_id': 0}
            # 查询
            print('query', myquery)
            result = self.find_detail(myquery, projection, self.sort)

            return result
        except:
            traceback.print_exc()

    # 按query select
    @staticmethod
    def find_detail(query, projection, sort):
        try:
            url = 'mongodb://root:HammerScholarRoot0@hammerscholar-pub.mongodb.zhangbei.rds.aliyuncs.com:3717,hammerscholarsecondary-pub.mongodb.zhangbei.rds.aliyuncs.com:3717/admin?replicaSet=mgset-505729903'
            # connect to mongodb
            client = MongoClient(url)
            db = client.HammerScholar
            detail = db.detail

            # find and order
            if sort is None:
                result = [doc for doc in detail.find(query, projection).sort([('IF', -1)])]
            else:
                result = [doc for doc in detail.find(query, projection).sort([(sort, -1)]).limit(1)]

            return result
        except:
            traceback.print_exc()


if __name__ == '__main__':
    dict = {'journal_category': '计算机', 'ifs': '影响因子大于10'}
    sc = searchJournal(dict)
    print(sc.slot_dic)
    sc.search()
