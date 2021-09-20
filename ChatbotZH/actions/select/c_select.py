from actions.recommend.conference import searchConference
from actions.recommend.journal import searchJournal

# 会议：1截稿时间 2通知时间 3举行时间 4举行地点 6摘要截稿时间 7级别 
# 会议+期刊：5.官网 16.投稿网站 8.领域 
# 期刊：9.IF 10.ISSN 11.E-ISSN 12.自引率 13.h-index 14.审稿速度 15.录用比例

# dict中 None -> ''
def updateDict(slot):
    result = {}
    for i in slot.keys():
        if slot[i] is None:
            result[i] = ''
        else:
            if type(slot[i]) == str:
                result[i] = slot[i].replace('|', ',').replace(';', ',')
            else:
                result[i] = str(slot[i]).replace('|', ',').replace(';', ',')
    
    return result

# 判断问会议还是期刊
def judges(dict) -> int:
    if dict['name'] is None and dict['journal_name'] is None:
        return None
    elif dict['name'] is None and dict['journal_name'] is not None:
        a = 0 # 期刊
    elif dict['name'] is not None and dict['journal_name'] is None:
        a = 1 # 会议
    else:
        if len(dict['name']) >= len(dict['journal_name']):
            a = 1
        else:
            a = 0

    return a

# 问ACL会议或NATURE期刊
def conference_journal(dict, dispatcher) -> str:
    if judges(dict) is None:
        return None
    elif judges(dict) == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
        else:
            text = 'conf'
            i = result[0]
            i = updateDict(i)
            data = [i['acronym'], i['name'], i['Link'], i['Location'], i['Categories'], i['Deadline'], i['Notice'], i['Begin'], i['End'], i['Extended'], i['CCF'], i['CORE'], i['QUALIS'], str(i['Viewed'])]
            text = text + '|' + ';'.join(data)
            try:
                year = i['year']
            except:
                pass

            # 组装answer
            answer = i['acronym'] + year
            if i['name'] != '':
                answer += '的全称为' + i['name'] + '，'
            if i['Deadline'] != '':
                answer += '于' + i['Deadline'] + '截稿，'
            if i['Begin'] != '':
                if i['Location'] != '':
                    answer += '于' + i['Begin'] + '在' + i['Location'] + '举行.'
                else:
                    answer += '于' + i['Begin'] + '举行.'
            if i['CCF'] != '':
                answer += '它的CCF等级为' + i['CCF']
            dispatcher.utter_message('text|' + answer)

            return text
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' +  dict['journal_name'] + '期刊'
        else:
            text = 'journal'
            i = result[0]
            if i['small_area'] is not None:
                i['small_area'] = i['small_area'].replace(';', '#')
                if len(i['small_area']) > 0 and i['small_area'][-1] == '#':
                    i['small_area'] = i['small_area'][:-1]
            i = updateDict(i)
            data = [i['name'], i['acronym'], i['ISSN'], i['E_ISSN'], i['IF'], i['self_citing'], i['h_index'], i['website'], i['submit'], i['OA'], i['large_area'], i['small_area'], i['speed'], i['rate'], i['fenqu']]
            text = text + '|' + ';'.join(data)

            # 组装answer
            answer = i['name']
            if i['IF'] != '':
                answer += '的最新影响因子为' + i['IF'] + '，'
            if i['self_citing'] != '':
                data = '%.2f%%' % (float(i['self_citing']) * 100)
                answer += '自引率为' + data + '，'
            if i['h_index'] != '':
                answer += 'h5指数为' + i['h_index'] + '，'
            if i['submit'] != '':
                answer += '可以在' + i['submit'] + '上投稿'
            dispatcher.utter_message('text|' + answer)

            return text  


# 问ACL会议或NATURE期刊的截稿时间
def conference_deadline(dict) -> str:
    if judges(dict) is None:
        return None
    if judges(dict) == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
        else:
            data = result[0]['Deadline']
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|' + dict['name'] + year + '的截稿日期为' + data
                return txt
            else:
                return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议的截稿日期'
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
        else:
            data = result[0]['Deadline']
            if data is not None:
                txt = 'text|' + dict['journal_name'] + '的截稿日期为' + data
                return txt
            else:
                return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '的截稿日期'

# 问ACL会议的通知时间
def conference_notice(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
    else:
        data = result[0]['Notice']
        try:
            year = result[0]['year']
        except:
            pass
        if data is not None:
            txt = 'text|' + dict['name'] + year + '的通知日期为' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议的通知日期'

# 问ACL会议的举行时间
def conference_begin(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
    else:
        try:
            year = result[0]['year']
        except:
            pass
        if result[0]['Begin'] is None:
            data = None
        elif result[0]['End'] is None:
            data = result[0]['Begin']
        else:
            data = result[0]['Begin'] + ' to ' + result[0]['End']
        
        if data is not None:
            txt = 'text|' + dict['name'] + year + '的举办时间为' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议的举行时间'

# 问ACL会议的举办地点
def conference_location(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
    else:
        data = result[0]['Location']
        try:
            year = result[0]['year']
        except:
            pass
        if data is not None:
            txt = 'text|' + dict['name'] + year + '的举办地点为' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议的举办地点'

# 问ACL会议或IEEE期刊的官网
def homepage(dict) -> str:
    if judges(dict) is None:
        return None
    elif judges(dict) == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
        
        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
        else:
            data = result[0]['Link']
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|' + dict['name'] + year + '的官网为' + data
                return txt
            else:
                return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议的官网'
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' +  dict['journal_name'] + '期刊'
        else:
            data = result[0]['website']
            if data is not None:
                txt = 'text|' + dict['journal_name'] + '的官网为' + data
                return txt
            else:
                return 'text|抱歉，没有搜寻到' +  dict['journal_name'] + '期刊的官网'    

# 问ACL会议的摘要截稿时间
def conference_abstract_due(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
    
    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
    else:
        data = result[0]['AbstractRegistrationDue']
        try:
            year = result[0]['year']
        except:
            pass
        if data is not None:
            txt = 'text|' + dict['name'] + year + '的摘要截稿时间为' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议的摘要截稿日期'

# 问ACL会议或NATURE期刊的级别
def conference_degree(dict) -> str:
    if judges(dict) is None:
        return None
    elif judges(dict) == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
        else:
            ccf = result[0]['CCF'] if result[0]['CCF'] is not None else ''
            core = result[0]['CORE'] if result[0]['CORE'] is not None else ''
            qualis = result[0]['QUALIS'] if result[0]['QUALIS'] is not None else ''
            try:
                year = result[0]['year']
            except:
                pass
            if ccf == '' and core == '' and qualis == '':
                return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议的任何级别信息'
            else:
                empty_list= []
                if ccf != '':
                    ccf = 'ccf等级为' + ccf + '，'
                else:
                    empty_list.append('ccf')
                
                if core != '':
                    core = 'core等级为' + core+ '，'
                else:
                    empty_list.append('core')
                
                if qualis != '':
                    qualis = 'qualis等级为' + qualis+ '，'
                else:
                    empty_list.append('qualis')

                txt = dict['name'] + year + '的' + ccf + core + qualis
                if len(empty_list) == 0:
                    txt = 'text|' + txt[:-1]
                elif len(empty_list) == 1:
                    txt = 'text|' + txt + '没有搜寻到其' + empty_list[0] + '信息'
                else:
                    txt = 'text|' + txt + '没有搜寻到其' + empty_list[0] + '和' + empty_list[1] + '信息'
                return txt
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
        else:
            data = result[0]['CCF']
            if data is not None:
                txt = 'text|' + dict['journal_name'] + '的ccf等级为' + data
                return txt
            else:
                return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '的ccf等级'

# 问会议或期刊的投稿网址
def submit_website(dict) -> str:
    if judges(dict) is None:
        return None
    elif judges(dict) == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
        
        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
        else:
            data = result[0]['Link']
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|' + '您可以从' + dict['name'] + year + '的官网上搜寻到投稿公告，' + dict['name'] + year + '的官网为' + data
                return txt
            else:
                return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议的投稿网站'
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' +  dict['journal_name'] + '期刊'
        else:
            data = result[0]['submit']
            if data is not None:
                txt = 'text|' + dict['journal_name'] + '的投稿网站为' + data
                return txt
            else:
                return 'text|抱歉，没有搜寻到' +  dict['journal_name'] + '期刊的投稿网址'   

# 问会议或期刊的领域方向
def categories(dict) -> str:
    if judges(dict) is None:
        return None
    elif judges(dict) == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
        
        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
        else:
            data = result[0]['Categories'].lower()
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|' + dict['name'] + year + '是与' + data + '相关的会议'
                return txt
            else:
                return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议的领域信息'
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' +  dict['journal_name'] + '期刊'
        else:
            data = result[0]['small_area'].lower().replace(';', '、')
            if data[-1] == '、':
                data = data[:-1]
            if data is not None:
                txt = 'text|' + dict['journal_name'] + '是与' + data + '相关的期刊'
                return txt
            else:
                return 'text|抱歉，没有搜寻到' +  dict['journal_name'] + '期刊的分类信息' 

# 问期刊的IF影响因子
def journal_IF(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
    else:
        data = result[0]['IF']
        if data is not None:
            txt = 'text|' + dict['journal_name'] + '的IF影响因子是' + str(data)
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的IF影响因子'

# 问期刊的ISSN
def journal_ISSN(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
    else:
        data = result[0]['ISSN']
        if data is not None:
            txt = 'text|' + dict['journal_name'] + '的ISSN是' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的ISSN信息'

# 问期刊的E-ISSN
def journal_EISSN(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
    else:
        data = result[0]['E_ISSN']
        if data is not None:
            txt = 'text|' + dict['journal_name'] + '的E-ISSN是' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的E-ISSN信息'

# 问期刊的自引率
def journal_self_citing(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_ name'] + '期刊'
    else:
        data = result[0]['self_citing']
        data = '%.2f%%' % (float(data) * 100)
        if data is not None:
            txt = 'text|' + dict['journal_name'] + '的自引率是' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的自引率'

# 问期刊的h-index
def journal_h_index(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
    else:
        data = result[0]['h_index']
        if data is not None:
            txt = 'text|' + dict['journal_name'] + '的h-index是' + str(data)
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的h-index'

# 问期刊的审稿速度
def journal_speed(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
    else:
        data = result[0]['speed']
        if data is not None:
            data = data.replace('网友分享经验：', '')
            if data != '':
                txt = 'text|' + dict['journal_name'] + '的审稿速度为' + data
                return txt
            else:
                return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的审稿速度'
        else:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的审稿速度'

# 问期刊的录用比例
def journal_rate(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
    else:
        data = result[0]['rate']
        if data is not None:
            data = data.replace('网友分享经验：', '')
            if data != '':
                if '%' in data:
                    txt = 'text|' + dict['journal_name'] + '的录用比例为' + data
                else:
                    txt = 'text|' + dict['journal_name'] + '的录用难度为' + data
                return txt
            else:
                return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的录用比例'
        else:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的录用比例'

# 问IEEE系列
def journal_IEEE(dict, dispatcher) -> str:
    if dict['journal_name'] is None:
        return None
      
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到IEEE期刊信息'
    else:
        data = result[0]['name']
        txt = 'text|共搜寻到IEEE系列期刊' + str(len(result)) + '个，其中影响因子最大的期刊是' + data
        dispatcher.utter_message(txt)

        text = 'journal'
        for i in result:
            if i['small_area'] is not None:
                i['small_area'] = i['small_area'].replace(';', '#')
                if len(i['small_area']) > 0 and i['small_area'][-1] == '#':
                    i['small_area'] = i['small_area'][:-1]
            i = updateDict(i)
            data = [i['name'], i['acronym'], i['ISSN'], i['E_ISSN'], i['IF'], i['self_citing'], i['h_index'], i['website'], i['submit'], i['OA'], i['large_area'], i['small_area'], i['speed'], i['rate'], i['fenqu']]
            text = text + '|' + ';'.join(data)
        return text

# 问期刊的SCI分区
def journal_fenqu(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
    else:
        data = result[0]['fenqu']
        if data is not None:
            txt = 'text|' + dict['journal_name'] + '的中科院SCI期刊分区为' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊的中科院SCI分区'


# 问期刊的publisher
def journal_publisher(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
    else:
        data = result[0]['Publisher']
        if data is not None:
            txt = 'text|' + dict['journal_name'] + '的出版商为' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '的出版商'


# 问期刊的投稿经验
def journal_experience(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|抱歉，没有搜寻到' + dict['journal_name'] + '期刊'
    else:
        data = result[0]['experience']
        if data is not None:
            data = '|'.join(data)
            txt = 'text|' + data
            return txt
        else:
            return 'text|抱歉，没有搜寻到网上关于' + dict['journal_name'] + '的任何投稿经验'


# 问ACL会议或NATURE期刊的全称
def fullName(dict) -> str:
    if judges(dict) is None:
        return None
    elif judges(dict) == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
        
        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
        else:
            data = result[0]['name']
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|' + dict['name'] + year + '的全称为' + data
                return txt
            else:
                return 'text|抱歉，没有找到'+  dict['name'] + year + '的全称'
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' +  dict['journal_name'] + '期刊'
        else:
            data = result[0]['name']
            if data is not None:
                txt = 'text|' + dict['journal_name'] + '的全称为' + data
                return txt
            else:
                return 'text|抱歉，没有找到' +  dict['journal_name'] + '期刊的全称'


# 问ACL会议或NATURE期刊的简称
def Acronym(dict) -> str:
    if judges(dict) is None:
        return None
    elif judges(dict) == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
        
        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' + year + '年的' + dict['name'] + '会议'
        else:
            data = result[0]['acronym']
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|' + dict['name'] + year + '的简称为' + data
                return txt
            else:
                return 'text|抱歉，没有找到'+  dict['name'] + year + '的简称'
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|抱歉，没有搜寻到' +  dict['journal_name'] + '期刊'
        else:
            data = result[0]['acronym']
            if data is not None:
                txt = 'text|' + dict['journal_name'] + '的简称为' + data
                return txt
            else:
                return 'text|抱歉，没有找到' +  dict['journal_name'] + '期刊的简称' 