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

# 问ACL会议
def conference_journal(dict, dispatcher) -> str:
    a = judges(dict)

    if a == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
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
            answer = 'text|' + i['acronym'] + year
            if i['name'] != '':
                answer += '\'s fullname is ' + i['name'] + '.'
            if i['Deadline'] != '':
                answer += ' It is deadlined in ' + i['Deadline']
            if i['Begin'] != '':
                answer += ' and held in ' + i['Begin']
            if i['CCF'] != '':
                answer += '. It is ccf-' + i['CCF'].lower()
            dispatcher.utter_message(answer)
            
            return text
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
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

            answer = 'text|' + i['name']
            if i['ISSN'] != '':
                answer += '\'s ISSN is ' + i['ISSN'] + ', whose'
            if i['IF'] != '':
                answer += ' IF is ' + i['IF'] + ','
            if i['self_citing'] != '':
                answer += ' self-citing is ' + i['self_citing'] + ','
            if i['h_index'] != '':
                answer += ' h-index is ' + i['h_index'] + ','
            if answer[-1] == ',':
                answer = answer[:-1]
            dispatcher.utter_message(answer)
            return text  


# 问ACL会议的截稿时间
def conference_deadline(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
    else:
        data = result[0]['Deadline']
        try:
            year = result[0]['year']
        except:
            pass
        if data is not None:
            txt = 'text|the deadline of ' + dict['name'] + year + ' is ' + data
            return txt
        else:
            return 'text|Sorry, I couldn\'t find the deadline of ' + dict['name'] + year

# 问ACL会议的通知时间
def conference_notice(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
    else:
        data = result[0]['Notice']
        try:
            year = result[0]['year']
        except:
            pass
        if data is not None:
            txt = 'text|the notice of ' + dict['name'] + year + ' is ' + data
            return txt
        else:
            return 'text|Sorry, I couldn\'t find the notice of ' + dict['name'] + year

# 问ACL会议的举行时间
def conference_begin(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
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
            txt = 'text|the held date of ' + dict['name'] + year + ' is ' + data
            return txt
        else:
            return 'text|Sorry, I couldn\'t find the held date of ' + dict['name'] + year

# 问ACL会议的举办地点
def conference_location(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
    else:
        data = result[0]['Location']
        try:
            year = result[0]['year']
        except:
            pass
        if data is not None:
            txt = 'text|the ' + dict['name'] + year + ' is held in ' + data
            return txt
        else:
            return 'text|Sorry, I couldn\'t find the location of ' + dict['name'] + year

# 问ACL会议或IEEE期刊的官网
def homepage(dict) -> str:
    a = judges(dict)
    if a is None:
        return None
    elif a == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
        
        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
        else:
            data = result[0]['Link']
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|the website of ' + dict['name'] + year + ' is ' + data
                return txt
            else:
                return 'text|Sorry, I couldn\'t find the website of ' + dict['name']
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
        else:
            data = result[0]['website']
            if data is not None:
                txt = 'text|the website of ' + dict['journal_name'] + ' is ' + data
                return txt
            else:
                return 'text|Sorry, I couldn\'t find the website of ' +  dict['journal_name']   

# 问ACL会议的摘要截稿时间
def conference_abstract_due(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
    
    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
    else:
        data = result[0]['AbstractRegistrationDue']
        try:
            year = result[0]['year']
        except:
            pass
        if data is not None:
            txt = 'text|the abstractRegistrationDue of ' + dict['name'] + year + ' is ' + data
            return txt
        else:
            return 'text|Sorry, I couldn\'t find the abstractRegistrationDue of ' + dict['name'] + year

# 问ACL会议的级别
def conference_degree(dict) -> str:
    if dict['name'] is None:
        return None
    sc = searchConference(dict)
    result = sc.search()
    year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
    else:
        try:
            year = result[0]['year']
        except:
            pass
        ccf = result[0]['CCF'].lower() if result[0]['CCF'] is not None else ''
        core = result[0]['CORE'].lower() if result[0]['CORE'] is not None else ''
        qualis = result[0]['QUALIS'].lower() if result[0]['QUALIS'] is not None else ''
        if ccf == '' and core == '' and qualis == '':
            return 'text|Sorry, I couldn\'t find any degree of ' + dict['name'] + year
        else:
            empty_list= []
            if ccf != '':
                ccf = 'ccf-' + ccf + ','
            else:
                empty_list.append('ccf')
            
            if core != '':
                core = 'core-' + core+ ','
            else:
                empty_list.append('core')
            
            if qualis != '':
                qualis = 'qualis-' + qualis+ ','
            else:
                empty_list.append('qualis')

            txt = 'text|' + dict['name'] + year + ' is ' + ccf + core + qualis
            if len(empty_list) == 0:
                txt = txt[:-1]

            return txt

# 问会议或期刊的投稿网址
def submit_website(dict) -> str:
    a = judges(dict)
    if a is None:
        return None
    elif a == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
        
        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
        else:
            data = result[0]['Link']
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|You could find the submission notice from the website of ' + dict['name'] + year + ', which is ' + data
                return txt
            else:
                return 'text|Sorry, I couldn\'t find the submission website of ' + dict['name'] + year
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
        else:
            data = result[0]['submit']
            if data is not None:
                txt = 'text|the submission website of ' + dict['journal_name'] + ' is ' + data
                return txt
            else:
                return 'text|Sorry, I couldn\'t find the submission website of ' +  dict['journal_name']

# 问会议或期刊的领域方向
def categories(dict) -> str:
    a = judges(dict)
    if a is None:
        return None
    elif a == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
        
        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
        else:
            data = result[0]['Categories'].lower()
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|' + dict['name'] + year + ' focus on ' + data
                return txt
            else:
                return 'text|Sorry, I couldn\'t find the field of ' + dict['name'] + year
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
        else:
            data = result[0]['small_area'].lower().replace(';', '、')
            if data[-1] == '、':
                data = data[:-1]
            if data is not None:
                txt = 'text|' + dict['journal_name'] + ' focus on ' + data
                return txt
            else:
                return 'text|Sorry, I couldn\'t find the field of ' + dict['journal_name']

# 问期刊的IF影响因子
def journal_IF(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['IF']
        if data is not None:
            txt = 'text|the IF of ' + dict['journal_name'] + ' is ' + str(data)
            return txt
        else:
            return 'text|Sorry, I could\'s find the IF of ' + dict['journal_name']

# 问期刊的ISSN
def journal_ISSN(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['ISSN']
        if data is not None:
            txt = 'text|the ISSN of ' + dict['journal_name'] + ' is ' + data
            return txt
        else:
            return 'text|Sorry, I could\'s find the ISSN of ' + dict['journal_name']

# 问期刊的E-ISSN
def journal_EISSN(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['E_ISSN']
        if data is not None:
            txt = 'text|the E-ISSN of ' + dict['journal_name'] + ' is ' + data
            return txt
        else:
            return 'text|Sorry, I could\'s find the E-ISSN of ' + dict['journal_name']

# 问期刊的自引率
def journal_self_citing(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['self_citing']
        if data is not None:
            txt = 'text|the self-citing of ' + dict['journal_name'] + ' is ' + str(data)
            return txt
        else:
            return 'text|Sorry, I could\'s find the self-citing of ' + dict['journal_name']

# 问期刊的h-index
def journal_h_index(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['h_index']
        if data is not None:
            txt = 'text|the h-index of ' + dict['journal_name'] + ' is ' + str(data)
            return txt
        else:
            return 'text|Sorry, I could\'s find the h-index of ' + dict['journal_name']

# 问期刊的审稿速度
def journal_speed(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['speed']
        if data is not None:
            data = data.replace('网友分享经验：', '')
            if data != '':
                txt = 'text|the reviewing speed of ' + dict['journal_name'] + ' is ' + data
                return txt
            else:
                return 'text|Sorry, I could\'s find the reviewing speed of ' + dict['journal_name']
        else:
            return 'text|Sorry, I could\'s find the reviewing speed of ' + dict['journal_name']

# 问期刊的录用比例
def journal_rate(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['rate']
        if data is not None:
            data = data.replace('网友分享经验：', '')
            if data != '':
                txt = 'text|the accepted rate of ' + dict['journal_name'] + ' is ' + data
                return txt
            else:
                return 'text|Sorry, I could\'s find the accepted rate of ' + dict['journal_name']
        else:
            return 'text|Sorry, I could\'s find the accepted rate of ' + dict['journal_name']

# 问IEEE系列
def journal_IEEE(dict, dispatcher) -> str:   
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find anything about IEEE'
    else:
        data = result[0]['name']
        txt = 'text|There are ' + str(len(result)) + ' journals in IEEE in total, in which the more important is ' + data
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


# 问期刊的投稿经验
def journal_experience(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['experience']
        if data is not None:
            data = '|'.join(data)
            txt = 'text|' + data
            return txt
        else:
            return 'text|Sorry, I could\'s find any experience of ' + dict['journal_name']


# 问ACL会议或NATURE期刊的简称
def Acronym(dict) -> str:
    if judges(dict) is None:
        return None
    elif judges(dict) == 1:
        sc = searchConference(dict)
        result = sc.search()
        year = dict['begin_from'][:4] # 保证begin_from非空且长度大于4
        
        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['name'] + ' in ' + year
        else:
            data = result[0]['acronym']
            try:
                year = result[0]['year']
            except:
                pass
            if data is not None:
                txt = 'text|the acronym of ' + dict['name'] + year + ' is ' + data
                return txt
            else:
                return 'text|Sorry, I could\'s find the acronym of ' +  dict['name'] + year
    else:
        sc = searchJournal(dict)
        result = sc.search()

        if len(result) == 0:
            return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
        else:
            data = result[0]['acronym']
            if data is not None:
                txt = 'text|the acronym of ' + dict['journal_name'] + ' is ' + data
                return txt
            else:
                return 'text|Sorry, I could\'s find the acronym of ' + dict['journal_name']


# 问期刊的publisher
def journal_publisher(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['Publisher']
        if data is not None:
            txt = 'text|the publisher of ' + dict['journal_name'] + ' is ' + data
            return txt
        else:
            return 'text|Sorry, I could\'s find the publisher of ' + dict['journal_name']


# 问期刊的SCI分区
def journal_fenqu(dict) -> str:
    if dict['journal_name'] is None:
        return None
    
    sc = searchJournal(dict)
    result = sc.search()

    if len(result) == 0:
        return 'text|Sorry, I couldn\'t find the ' + dict['journal_name']
    else:
        data = result[0]['fenqu']
        if data is not None:
            txt = 'text|the sci factor of ' + dict['journal_name'] + ' is ' + data
            return txt
        else:
            return 'text|Sorry, I could\'s find the sci factor of ' + dict['journal_name']


