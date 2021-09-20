from pymongo import MongoClient
import traceback
import pypinyin


class searchPaper():
    def __init__(self, dict):
        # 槽值字典
        self.slot_dic = {
            'author': dict['author'],  # 作者
            'begin_from': dict['begin_from'],  # 起始时间
            'begin_to': dict['begin_to'],  # 结束时间
            'year': None,
            'conference': dict['name'],  # 会议名
            'journal': dict['journal_name'], # 期刊名
            'source': None
        }
        # 将year 逗号分割的字符串转换成list
        if self.slot_dic['begin_from'] is not None:
            try:
                start = int(self.slot_dic['begin_from'][:4])
                end = int(self.slot_dic['begin_to'][:4])
                self.slot_dic['year'] = str(start)
                for i in range(start + 1, end + 1):
                    self.slot_dic['year'] = self.slot_dic['year'] + ',' + str(i)
                self.slot_dic['year'] = self.slot_dic['year'].split(',')
            except:
                self.slot_dic['year'] = None
        # 会议名默认大写
        if self.slot_dic['journal'] is not None:
            self.slot_dic['source'] = [self.slot_dic['journal'].upper()]
        if self.slot_dic['conference'] is not None:
            self.slot_dic['source'] = self.slot_dic['conference'].upper().split(',')
        # 名字变拼音
        if self.slot_dic['author'] is not None:
            self.slot_dic['author'] = self.hp(self.slot_dic['author'])

    # 槽值是否为空
    def isEmpty(self):
        if self.slot_dic['author'] is None and self.slot_dic['year'] is None and self.slot_dic['conference'] is None:
            return True
        return False

    def search(self):
        # slot为空
        if self.isEmpty():
            return []
        # 检索query
        myquery = {}
        if self.slot_dic['author'] is not None:
            myquery['authors.name'] = self.slot_dic['author']
        if self.slot_dic['source'] is not None:
            myquery['venue'] = {'$in': self.slot_dic['source']}
        if self.slot_dic['year'] is not None:
            myquery['year'] = {'$in': self.slot_dic['year']}
            # 限制返回字段
        projection = {'_id': 0, 'authors.name': 1, 'type': 1, 'title': 1, 'year': 1, 'venue': 1,
                      'abstract': 1, 'code_url': 1, 'url': 1, 'blog_urls': 1}
        # 查询
        print('query', myquery)
        result = self.find_detail(myquery, projection)

        return result

    # 按query select
    @staticmethod
    def find_detail(query, projection):
        try:
            url = 'mongodb://root:HammerScholarRoot0@hammerscholar-pub.mongodb.zhangbei.rds.aliyuncs.com:3717,hammerscholarsecondary-pub.mongodb.zhangbei.rds.aliyuncs.com:3717/admin?replicaSet=mgset-505729903'
            # connect to mongodb
            client = MongoClient(url)
            db = client.HammerScholar
            paper = db.papers

            # find and order
            result = [doc for doc in paper.find(query, projection).sort([('year', -1)]).limit(50)]

            return result
        except:
            traceback.print_exc()

    @staticmethod
    # 不带声调的(style=pypinyin.NORMAL)
    def hp(word):
        names = pypinyin.pinyin(word, style=pypinyin.NORMAL)
        lastname = names[0][0].title()

        b = []
        for i in names[1:]:
            b.extend(i)
        firstname = ''.join(b).title()

        return firstname + ' ' + lastname


if __name__ == '__main__':
    dict = {'author': None, 'year': '2006', 'conference': 'CVPR', 'topic': None}
    sc = searchPaper(dict)
    print(sc.slot_dic)
    sc.search()
