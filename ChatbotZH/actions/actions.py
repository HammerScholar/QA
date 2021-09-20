# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
from logging import disable
from re import I
from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import ActionExecuted, AllSlotsReset, SlotSet, EventType, ActiveLoop, ConversationPaused
from rasa_sdk.executor import CollectingDispatcher
from actions.slots import set_dict, key_fulls, mergeSlot, copySlot, hasTime, getType
from actions.recommend.conference import searchConference
from actions.recommend.paper import searchPaper
from actions.recommend.journal import searchJournal
from actions.select import c_select
from actions.select.c_select import updateDict
from actions.dateUtils.date_treat import current_year, next_year

class ActionRecommend(Action):

    def name(self) -> Text:
         return "action_recommend"

    def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        slot = self.slotFunc(tracker.slots, tracker.latest_message['text'])
        slot_copys = None
        slot['name'] = None
        slot['journal_name'] = None
        # 根据type分别去查人、会议、论文、期刊
        type = slot['type']
        print("\nrecommend is ", tracker.latest_message['text'], "\nslots is ", slot, '\ntype is ', type)
        if type is None:
            dispatcher.utter_message(response='utter_default')
        elif type == '会议':
            slot['name'] = None
            sc = searchConference(slot)
            answerList = sc.search()
            if answerList is not None:
                print("共找到" + str(len(answerList)) + "个会议信息")
                self.adjustAnswer(answerList, dispatcher, type)
                if len(answerList) > 0:
                    # 保存槽值备份
                    slot_copys = copySlot(slot)
            else:
                dispatcher.utter_message('没有找到符合条件的会议唉')
        elif type == '论文':
            sc = searchPaper(slot)
            answerList = sc.search()
            if answerList is not None:
                print("共找到" + str(len(answerList)) + "个论文信息")
                self.adjustAnswer(answerList, dispatcher, type)
                if len(answerList) > 0:
                    # 保存槽值备份
                    slot_copys = copySlot(slot)
            else:
                dispatcher.utter_message('没有找到符合条件的论文唉')
        elif type == '期刊':
            sc = searchJournal(slot)
            answerList = sc.search()
            if answerList is not None:
                print("共找到" + str(len(answerList)) + "个期刊信息")
                self.adjustAnswer(answerList, dispatcher, type)
                if len(answerList) > 0:
                    # 保存槽值备份
                    slot_copys = copySlot(slot)
            else:
                dispatcher.utter_message('没有找到符合条件的期刊唉')
        else:
            dispatcher.utter_message(response='utter_default')

        slot_copys = copySlot(slot)
        # 重置槽值，并保存copy
        return [AllSlotsReset(), SlotSet('recommend_copy', slot_copys)]

    # 把tracker.slot中的槽值，处理成服务器用的槽值dict
    @staticmethod
    def slotFunc(slot, question) -> Dict[Text, Any]:
        # 解析slot
        mySlot = set_dict(slot)
        lastSlot = slot['recommend_copy']

        #判断是否继承上一轮对话的槽值，从而实现多轮
        if mySlot['type'] is None or '其中' in question:
            mySlot = mergeSlot(lastSlot, mySlot)
            
        return mySlot

    # 调整返回格式
    # conf|简称;全称;网址;地点;方向;截稿日期;通知日期;会议开始时间;结束时间;是否延期;CCF;CORE;QUALIS;查阅次数
    @staticmethod
    def adjustAnswer(answerList, dispatcher: CollectingDispatcher, type):
        ActionRecommend.natural_answer(answerList, dispatcher, type)
        if type == '会议':
            if len(answerList) > 0:
                text = 'conf'
                if len(answerList) > 100:
                    answerList = answerList[:100]
                for i in answerList:
                    i = updateDict(i)
                    data = [i['acronym'], i['name'], i['Link'], i['Location'], i['Categories'], i['Deadline'], i['Notice'], i['Begin'], i['End'], i['Extended'], i['CCF'], i['CORE'], i['QUALIS'], i['Viewed']]
                    text = text + '|' + ';'.join(data)
                dispatcher.utter_message(text)
            else:
                dispatcher.utter_message('text|没有找到符合条件的会议唉')
        elif type == '论文':
            if len(answerList) > 0:
                text = 'paper'
                if len(answerList) > 50:
                    answerList = answerList[:50]
                for i in answerList:
                    i = paper_addition(i)
                    # author name
                    names = []
                    for j in i['authors']:
                        names.append(j['name'])
                    # blog urls
                    blog_urls = i['blog_urls']
                    i = updateDict(i)
                    data = [i['title'], '#'.join(names), i['type'], i['venue'], i['year'], i['url'], i['code_url'], '#'.join(blog_urls), i['abstract']]
                    text = text + '|' + ';'.join(data)
                dispatcher.utter_message(text)
            else:
                dispatcher.utter_message('text|没有找到相应的论文唉')
        elif type == '期刊':
            if len(answerList) > 0:
                text = 'journal'
                if len(answerList) > 100:
                    answerList = answerList[:100]                    
                for i in answerList:
                    if i['small_area'] is not None:
                        i['small_area'] = i['small_area'].replace(';', '#')
                        if len(i['small_area']) > 0 and i['small_area'][-1] == '#':
                            i['small_area'] = i['small_area'][:-1]
                    i = updateDict(i)
                    data = [i['name'], i['acronym'], i['ISSN'], i['E_ISSN'], i['IF'], i['self_citing'], i['h_index'], i['website'], i['submit'], i['OA'], i['large_area'], i['small_area'], i['speed'], i['rate'], i['fenqu']]
                    text = text + '|' + ';'.join(data)
                dispatcher.utter_message(text)

            else:
                dispatcher.utter_message('text|没有找到相应的期刊唉')
        
    # 自然语言回答
    @staticmethod
    def natural_answer(answerList, dispatcher: CollectingDispatcher, type):
        
        if len(answerList) == 0:
            return None
        if len(answerList) == 1:
            answer = '只找到1个符合条件的' + type + '，它是'
        elif len(answerList) == 2:
            answer = '共找到2个符合条件的' + type + '，它们分别是'
        elif len(answerList) == 3 and type != '论文':
            answer = '共找到3个符合条件的' + type + '，它们分别是'
        else:
            if type == '论文':
                answer = '共找到' + str(len(answerList)) + '个符合条件的' + type + '，其中最近的有'
            else:
                answer = '共找到' + str(len(answerList)) + '个符合条件的' + type + '，其中比较重要的有'

        result = []
        if type == '会议':
            length = 3 if len(answerList) > 3 else len(answerList)
            before = None
            for i in range(0, length):
                h = answerList[i]
                if h['CCF'] is not None:
                    if before is None or before != h['CCF']:
                        a = h['CCF'].upper() + '类会议' + h['acronym']
                        before = h['CCF']
                    else:
                        a = h['acronym']
                else:
                    a = h['acronym']
                result.append(a)
        elif type == '论文':
            length = 2 if len(answerList) > 2 else len(answerList)
            before = None
            for i in range(0, length):
                h = answerList[i]
                if h['venue'] is not None:
                    if h['year'] is not None:
                        if  before is None or before != h['venue'] + h['year']:
                            a = h['venue'] + h['year'] + '的' + h['title']
                            before = h['venue'] + h['year']
                        else:
                            a = h['title']
                    else:
                        if  before is None or before != h['venue']:
                            a = h['venue'] + '的' + h['title']
                            before = h['venue']
                        else:
                            a = h['title']
                else:
                    a = h['title']
                result.append(a)
        elif type == '期刊':
            length = 3 if len(answerList) > 3 else len(answerList)
            for i in range(0, length):
                h = answerList[i]
                a = h['name']
                if h['IF'] is not None:
                    a = a + '(IF=' + str(h['IF']) + ')'
                result.append(a)
        
        # 选择，或和
        if len(result) == 1:
            answer = answer + result[0]
        elif len(result) == 2:
            answer = answer + result[0] + '和' + result[1]
        elif len(result) == 3:
            answer = answer + result[0] + '，' + result[1] + '和' + result[2]
        
        dispatcher.utter_message('text|' + answer)


# 把mongo返回字段补全
def paper_addition(dict):
    if not 'title' in dict.keys():
        dict['title'] = None
    if not 'authors' in dict.keys():
        dict['authors'] = []
    if not 'type' in dict.keys():
        dict['type'] = None
    if not 'venue' in dict.keys():
        dict['venue'] = None
    if not 'url' in dict.keys():
        dict['url'] = None
    if not 'code_url' in dict.keys():
        dict['code_url'] = None
    if not 'blog_urls' in dict.keys():
        dict['blog_urls'] = []
    if not 'abstract' in dict.keys():
        dict['abstract'] = None
    
    return dict


class ActionSelect(Action):

    def name(self) -> Text:
         return "action_select"

    def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]: 

        # 获取服务器对应的槽值
        deadline = tracker.slots['conf_deadline']
        notice = tracker.slots['conf_notice']
        tracker.slots['conf_category'] = None
        flag = ('if' in tracker.latest_message['text'].lower()) or ('issn' in tracker.latest_message['text'].lower()) or ('sci分区' in tracker.latest_message['text'].lower())
        slot = self.slotFunc(tracker.slots, flag)

        # 只保留需要的槽值
        slot = {'name': slot['name'], 'location': None, 'category': None, 'extended': None, 'ccf': None, 'core': None, 'qualis': None, 
                'deadline_from': None, 'deadline_to': None, 'notice_from': None, 'notice_to': None, 'begin_from': slot['begin_from'], 'begin_to': slot['begin_to'],
                'type': None, 'journal_category': None, 'ifs': None, 'journal_name': slot['journal_name'], 'author': None, 'h_index': None, 'fenqu': None, 'publisher': None
                }

        # 分类问题
        number = self.classification(slot, tracker.latest_message['text'], deadline, notice)
        print("\nselect:", tracker.latest_message['text'], "\nslots:", slot, '\nnumber:', number)
        # 特定的规则 问ieee系列
        if slot['journal_name'] is not None and slot['journal_name'].upper() == 'IEEE':
            answer = c_select.journal_IEEE(slot, dispatcher)
        elif number == 0:
            # 如果一个规则都没有匹配到
            if tracker.slots['conf_name'] is None and tracker.slots['journal_name'] is None:
                # 如果现在问的问题中没有会议或期刊
                answer = None
            else:
                answer = c_select.conference_journal(slot, dispatcher)
        elif number == 1:
            answer = c_select.conference_deadline(slot)
        elif number == 2:
            answer = c_select.conference_notice(slot)
        elif number == 3:
            answer = c_select.conference_begin(slot)
        elif number == 4:
            answer = c_select.conference_location(slot)
        elif number == 5:
            answer = c_select.homepage(slot)
        elif number == 6:
            answer = c_select.conference_abstract_due(slot)
        elif number == 7:
            answer = c_select.conference_degree(slot)
        elif number == 8:
            answer = c_select.categories(slot)
        elif number == 9:
            answer = c_select.journal_IF(slot)
        elif number == 10:
            slot['name'] = None
            answer = c_select.journal_ISSN(slot)
        elif number == 11:
            slot['name'] = None
            answer = c_select.journal_EISSN(slot)
        elif number == 12:
            answer = c_select.journal_self_citing(slot)
        elif number == 13:
            answer = c_select.journal_h_index(slot)
        elif number == 14:
            answer = c_select.journal_speed(slot)
        elif number == 15:
            answer = c_select.journal_rate(slot)
        elif number == 16:
            answer = c_select.submit_website(slot)
        elif number == 17:
            answer = c_select.journal_fenqu(slot)
        elif number == 18:
            answer = c_select.journal_publisher(slot)
        elif number == 19:
            answer = c_select.journal_experience(slot)
        elif number == 20:
            answer = c_select.fullName(slot)
        elif number == 21:
            answer = c_select.Acronym(slot)
        

        if answer is None:
            dispatcher.utter_message(response='utter_default')
            slot_copys = None
        else:
            dispatcher.utter_message(answer)
            # 保存槽值备份
            slot_copys = copySlot(slot)

        # 重置槽值，并保存copy
        return [AllSlotsReset(), SlotSet('select_copy', slot_copys)]

    # 把tracker.slot中的槽值，处理成服务器用的槽值dict
    @staticmethod
    def slotFunc(slot, flag) -> Dict[Text, Any]:
        # 解析slot
        slot['conf_deadline'] = None
        slot['conf_notice'] = None
        mySlot = set_dict(slot)
        lastSlot = slot['select_copy']

        if lastSlot is not None:
            # 只问期刊
            if flag:
                if mySlot['journal_name'] is None:
                    mySlot = mergeSlot(lastSlot, mySlot)
                else:
                    pass
            else:
                if mySlot['name'] is None and mySlot['journal_name'] is None:
                    mySlot = mergeSlot(lastSlot, mySlot)
        else:
            pass
            
        # 如果未指明时间，默认今年到明年
        if mySlot['begin_from'] is None:
            mySlot['begin_from'] = str(current_year) + '-01-01'
            mySlot['begin_to'] = str(next_year) + '-12-31'
        
        return mySlot
    
    # 根据槽值和问题来分类
    # 会议：2通知时间 3举行时间 4举行地点 6摘要截稿时间 
    # 会议+期刊：1截稿时间 5.官网 7级别 8.领域 16.投稿网站 20.全称 21.简称
    # 期刊：9.IF 10.ISSN 11.E-ISSN 12.自引率 13.h-index 14.审稿速度 15.录用比例 17.SCI分区 18.发布商 19.投稿经验
    @staticmethod
    def classification(slot, question, deadline, notice) -> int:
        question = question.lower()
        conclusion = 0
        if '摘要' in question and deadline is not None:
            conclusion = 6
        elif deadline  is not None:
            conclusion = 1
        elif notice  is not None:
            conclusion = 2
        else:
            for i in ['时间', '时候', '哪年', '何年', '哪天', '几月', '何时', '日期']:
                if i in question:
                    conclusion = 3
            for i in ['哪里', '何地', '地点', '地方', '国家', '城市']:
                if i in question:
                    conclusion = 4
            for i in ['官网', '网站', '网址']:
                if i in question:
                    conclusion = 5
            for i in ['等级', '级别', 'ccf', 'core', 'qualis']:
                if i in question:
                    conclusion = 7
            for i in ['领域', '方向', '相关', '范畴', '分类']:
                if i in question:
                    conclusion = 8
            for i in ['影响因子', 'if']:
                if i in question:
                    conclusion = 9
            for i in ['issn']:
                if i in question:
                    conclusion = 10
            for i in ['eissn', 'e_issn', 'e-issn']:
                if i in question:
                    conclusion = 11
            for i in ['自引率', '自引用']:
                if i in question:
                    conclusion = 12
            for i in ['h-index', 'h_index', 'h指标', 'h指数', 'h-指数', 'h5']:
                if i in question:
                    conclusion = 13
            for i in ['审稿速度', '审稿快慢', '审稿']:
                if i in question:
                    conclusion = 14
            for i in ['录用比例', '难易', '难不难', '难吗', '难嘛', '录用', '好中']:
                if i in question:
                    conclusion = 15
            for i in ['分区', '几区', '什么区', 'sci分区']:
                if i in question:
                    conclusion = 17
            for i in ['出版', '发布商']:
                if i in question:
                    conclusion = 18
            if '投稿' in question: # 在哪里投稿
                conclusion = 16
            if '投稿' in question and '经验' in question: # 投稿经验
                conclusion = 19
            for i in ['全称', '全名']:
                if i in question:
                    conclusion = 20
            for i in ['简称', '简写', '缩写']:
                if i in question:
                    conclusion = 21
            if 'sci' in question and slot['journal_name'] is not None and 'sci' not in slot['journal_name']:
                conclusion = 17
        
        
        return conclusion


class ActionEsSearch(Action):

    def name(self) -> Text:
         return "action_ES_Search"

    def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        answer = 'search|%s' % tracker.latest_message['text']
        dispatcher.utter_message(answer)

        return [AllSlotsReset()]