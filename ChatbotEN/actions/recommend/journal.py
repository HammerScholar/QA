from pymongo import MongoClient
import traceback
import re

pattern = ['>=(-?\d+)(\.\d+)?', '>(-?\d+)(\.\d+)?', '<=(-?\d+)(\.\d+)?', '<(-?\d+)(\.\d+)?', 
    'ishigherthan(-?\d+)(\.\d+)?', 'islowerthan(-?\d+)(\.\d+)?', 'isbetween(-?\d+)(\.\d+)?and(-?\d+)(\.\d+)?']

class searchJournal():
    def __init__(self, dict):
        # 槽值字典
        self.slot_dic = {
            'journal_name': dict['journal_name'],
            'journal_category': dict['journal_category'],  # 期刊方向
            'ifs': dict['ifs'],  # IF
            'h_index': dict['h_index'],  # h_index
            'CCF': dict['ccf'],
            'deadline_from': dict['deadline_from'], # 截稿日期时间段
            'deadline_to': dict['deadline_to'],
            'publisher': dict['publisher']
        }

        if self.slot_dic['journal_category'] is not None:
            if self.slot_dic['journal_category'].upper() == 'AI':
                self.slot_dic['journal_category'] = 'ARTIFICIAL INTELLIGENCE'
            elif self.slot_dic['journal_category'].upper() == 'CS':
                self.slot_dic['journal_category'] = 'COMPUTER SCIENCE'
        if self.slot_dic['CCF'] is not None:
            self.slot_dic['CCF'] = self.slot_dic['CCF'].upper()

        self.compare = None
        if self.slot_dic['ifs'] is not None:
            self.slot_dic['ifs'] = self.slot_dic['ifs'].lower().replace('if', '').replace(' ', '')
            print(self.slot_dic['ifs'])
            if re.match(pattern[0], self.slot_dic['ifs']):
                self.compare = {'$gte': float(self.slot_dic['ifs'][2:])}
            elif re.match(pattern[1], self.slot_dic['ifs']):
                self.compare = {'$gt': float(self.slot_dic['ifs'][1:])}
            elif re.match(pattern[2], self.slot_dic['ifs']):
                self.compare = {'$lte': float(self.slot_dic['ifs'][2:])}
            elif re.match(pattern[3], self.slot_dic['ifs']):
                self.compare = {'$lt': float(self.slot_dic['ifs'][1:])}
            elif re.match(pattern[4], self.slot_dic['ifs']):
                self.compare = {'$gt': float(self.slot_dic['ifs'][12:])}
            elif re.match(pattern[5], self.slot_dic['ifs']):
                self.compare = {'$lt': float(self.slot_dic['ifs'][11:])}
            elif re.match(pattern[6], self.slot_dic['ifs']):
                x = self.slot_dic['ifs'].split('and')
                self.compare = {'$gt': float(x[0][9:]), '$lt': float(x[1])}
        
        self.h_index = None
        if self.slot_dic['h_index'] is not None:
            self.slot_dic['h_index'] = self.slot_dic['h_index'].lower().replace('h', '').replace(' ', '').replace('-', '').replace('_', '').replace('index', '')
            if re.match(pattern[0], self.slot_dic['h_index']):
                self.h_index = {'$gte': float(self.slot_dic['h_index'][2:])}
            elif re.match(pattern[1], self.slot_dic['h_index']):
                self.h_index = {'$gt': float(self.slot_dic['h_index'][1:])}
            elif re.match(pattern[2], self.slot_dic['h_index']):
                self.h_index = {'$lte': float(self.slot_dic['h_index'][2:])}
            elif re.match(pattern[3], self.slot_dic['h_index']):
                self.h_index = {'$lt': float(self.slot_dic['h_index'][1:])}
            elif re.match(pattern[4], self.slot_dic['h_index']):
                self.h_index = {'$gt': float(self.slot_dic['h_index'][12:])}
            elif re.match(pattern[5], self.slot_dic['h_index']):
                self.h_index = {'$lt': float(self.slot_dic['h_index'][11:])}
            elif re.match(pattern[6], self.slot_dic['h_index']):
                x = self.slot_dic['h_index'].split('and')
                self.h_index = {'$gt': float(x[0][9:]), '$lt': float(x[1])}


    # 槽值是否为空
    def isEmpty(self):
        if self.slot_dic['journal_name'] is None and self.slot_dic['journal_category'] is None and self.slot_dic['ifs'] is None and self.slot_dic['h_index'] is None \
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
            if self.slot_dic['journal_name'] is not None:
                if self.slot_dic['journal_name'] == 'IEEE':
                    myquery['name'] = {'$regex': '^IEEE'}
                else:
                    myquery['$or'] = [{'name': {'$regex': '^'+self.slot_dic['journal_name']+'$', '$options': 'i'}},
                        {'acronym': {'$regex': '^'+self.slot_dic['journal_name']+'$', '$options': 'i'}}]
            if self.slot_dic['journal_category'] is not None:
                myquery['small_area'] = {'$regex': self.slot_dic['journal_category'], '$options': 'i'}
            if self.compare is not None:
                myquery['IF'] = self.compare
            if self.h_index is not None:
                myquery['h_index'] = self.h_index
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
            result = self.find_detail(myquery, projection)

            return result
        except:
            traceback.print_exc()

    # 按query select
    @staticmethod
    def find_detail(query, projection):
        try:
            url = 'mongodb://root:HammerScholarRoot0@hammerscholar-pub.mongodb.zhangbei.rds.aliyuncs.com:3717,hammerscholarsecondary-pub.mongodb.zhangbei.rds.aliyuncs.com:3717/admin?replicaSet=mgset-505729903'
            # connect to mongodb
            client = MongoClient(url)
            db = client.HammerScholar
            detail = db.detail

            # find and order
            result = [doc for doc in detail.find(query, projection).sort([('IF', -1)])]

            return result
        except:
            traceback.print_exc()


if __name__ == '__main__':
    dict = {'journal_category': '计算机', 'ifs': '影响因子大于10'}
    sc = searchJournal(dict)
    print(sc.slot_dic)
    sc.search()
