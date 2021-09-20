from typing import Any, Dict, Text, List
from actions.dateUtils import date_treat

# 取长度最长的元素
def getMaxLength(list) -> str:
    if list is None:
        return None
    if len(list) == 0:
        return None
    max = -1
    index = 0
    for i in range(0, len(list)):
        a = list[i]
        if len(a) > max:
            max = len(a)
            index = i
    return list[index]

# 把年份转换成时间段
def deal_year(year):
    froms, to = None, None
    if year is not None:
        froms = year + '-01-01'
        to = year + '-12-31'
    
    return froms, to 

# date, vague_time -> 时间段
# 注意中文中vague是list，而date是str
def deal_time(date, vague):
    date_from, date_to, vague_from, vague_to = None, None, None, None
    # date -> 时间段
    if date is not None:
        date_treat.analyse(date)
        # 从question_temp中获取槽值
        if date_treat.dateYear_from is not None and date_treat.dateMonth_from is not None and date_treat.dateDay_from is not None:
            date_from = "{:>4d}-{:0>2d}-{:0>2d}".format(date_treat.dateYear_from,
                                                                         date_treat.dateMonth_from,
                                                                         date_treat.dateDay_from)
        if date_treat.dateYear_to is not None and date_treat.dateMonth_to is not None and date_treat.dateDay_to is not None:
            date_to = "{:>4d}-{:0>2d}-{:0>2d}".format(date_treat.dateYear_to, date_treat.dateMonth_to,
                                                                       date_treat.dateDay_to)
    # vague -> 时间段
    if vague is not None and len(vague) > 0:
        vague_time = getMaxLength(vague)
        date_treat.analyse(vague_time)
        # 从question_temp中获取槽值
        if date_treat.dateYear_from is not None and date_treat.dateMonth_from is not None and date_treat.dateDay_from is not None:
            vague_from = "{:>4d}-{:0>2d}-{:0>2d}".format(date_treat.dateYear_from,
                                                                         date_treat.dateMonth_from,
                                                                         date_treat.dateDay_from)
        if date_treat.dateYear_to is not None and date_treat.dateMonth_to is not None and date_treat.dateDay_to is not None:
            vague_to = "{:>4d}-{:0>2d}-{:0>2d}".format(date_treat.dateYear_to, date_treat.dateMonth_to,
                                                                       date_treat.dateDay_to)

    # 取交集
    froms, to = time_intersection(date_from, date_to, vague_from, vague_to)
    
    return froms, to

# 取两个时间段的交集
def time_intersection(from1, to1, from2, to2):
    froms, to = None, None
    if from1 is None:
        froms = from2
    elif from2 is None:
        froms = from1
    else:
        # 没有交集
        if from1 > to2 or from2 > to1:
            froms = None
        else:
            froms = from1 if from1 > from2 else from2
    
    if to1 is None:
        to = to2
    elif to2 is None:
        to = to1
    else:
        # 没有交集
        if from1 > to2 or from2 > to1:
            to = None
        else:
            to = to1 if to1 < to2 else to2
    
    return froms, to

# 取出tracker中数据
def get_slot(slot):
    name = slot['conf_name']
    location = slot['GPE']
    online = slot['online']
    category = slot['conf_category']
    degree = slot['conf_degree']
    deadline = slot['conf_deadline']
    notice = slot['conf_notice']
    extended = slot['conf_extended']
    date = slot['DATE']
    vague_time = slot['vague_time']
    year = slot['year']
    conf_year = slot['conf_year']
    type = slot['type']
    author = slot['PERSON']
    journal_name= slot['journal_name']
    journal_category = slot['journal_category']
    ifs = slot['IF']
    h_index = slot['h_index']
    fenqu = slot['fenqu']
    publisher = slot['publisher']
    return name, location, online, category, degree, deadline, notice, extended, date, vague_time, year, conf_year, type, author, journal_category, ifs, journal_name, h_index, fenqu, publisher

# 讲tracker中的slot解析成后端处理的格式
# slot： {conf_name, GPE, online, conf_category, conf_degree, conf_deadline, conf_notice, conf_extended, DATE, vague_time, year, conf_year, type, jounal_category, IF, journal_name, PERSON, h_index, fenqu, publisher}
# result：{name, location, category, extended, ccf, core, qualis, deadline_from, deadline_to, notice_from, notice_to, begin_from, begin_to, type, jounal_category, ifs, journal_name, author, h_index, fenqu, publisher}
def set_dict(slot) -> Dict[Text, Any]:
    name, location, online, category, degree, deadline, notice, extended, date, vague_time, year, conf_year, type, author, journal_category, ifs, journal_name, h_index, fenqu, publisher = get_slot(slot)
    # 解析
    dict = {}
    dict['name'] = getMaxLength(name)
    if online is not None:
        dict['location'] = 'Online'
    else:
        dict['location'] = location
    dict['category'] = getMaxLength(category)
    dict['extended'] = extended
    dict['type'] = type

    dict['ccf'] = None
    dict['core'] = None
    dict['qualis'] = None
    if degree is not None:
        degree = getMaxLength(degree).replace(' ', '').replace('-', '').replace('_', '').upper()
        if 'CCF' in degree:
            dict['ccf'] = degree[3:]
        elif 'CORE' in degree:
            dict['core'] = degree[4:]
        elif 'QUALIS' in degree:
            dict['qualis'] = degree[6:]

    # 处理date
    if date is not None:
        if len(date) > 0:
            date = ' '.join(date).replace(',', ' ')
        else:
            date = None
    # 处理conf_year
    if year is None and conf_year is not None:
        year = conf_year[-4:]
    if conf_year is not None:
        dict['name'] = conf_year[:-4]

    date_from, date_to = deal_time(date, vague_time)
    year_from, year_to = deal_year(year)

    # 截稿日期时间段
    if deadline is not None:
        dict['deadline_from'], dict['deadline_to'] = date_from, date_to
    else:
        dict['deadline_from'], dict['deadline_to'] = None, None
    
    # 通知日期时间段
    if deadline is None and notice is not None:
        dict['notice_from'], dict['notice_to'] = date_from, date_to
    else:
        dict['notice_from'], dict['notice_to'] = None, None
    
    # 举办日期时间段
    if deadline is None and notice is None:
        dict['begin_from'], dict['begin_to'] = time_intersection(date_from, date_to, year_from, year_to)
    elif name is not None:
        dict['begin_from'], dict['begin_to'] = year_from, year_to
    else:
        dict['begin_from'], dict['begin_to'] = None, None
    
    dict['author'] = getMaxLength(author)
    dict['journal_name'] = getMaxLength(journal_name)
    dict['journal_category'] = getMaxLength(journal_category)
    print(dict['journal_category'])
    if dict['journal_category'] is not None and dict['journal_category'] == 'AI':
        dict['journal_category'] = '人工智能'
    dict['ifs'] = ifs
    dict['h_index'] = h_index
    dict['fenqu'] = fenqu
    dict['publisher'] = publisher

    return dict

# 获得slot中value不为空的key的个数
# 只有一个时间槽值，返回-1
def key_fulls(slot) -> int:
    sum1 = 0
    sum2 = 0
    sum3 = 0
    key1 = ['location', 'category', 'extended', 'ccf', 'core', 'qualis', 'deadline_from', 'notice_from', 'begin_from']
    key2 = ['name', 'author','begin_from']
    key3 = ['journal_category', 'ifs', 'h_index']
    
    # 会议
    for i in key1:
        if slot[i] is not None:
            sum1 = sum1 + 1
    if sum1 == 1 and (slot['deadline_from'] is not None or slot['notice_from'] is not None or slot['begin_from'] is not None):
        sum1 = -1
    
    # 论文
    for i in key2:
        if slot[i] is not None:
            sum2 = sum2 + 1
    
    # 期刊
    for i in key3:
        if slot[i] is not None:
            sum3 = sum3 + 1
    if sum3 == 1 and (slot['journal_category'] is not None):
        sum3 = -1

    
    return sum1, sum2, sum3

# 把slot中None转成''
def updateSlot(slot):
    result = {}
    for i in slot.keys():
        if slot[i] is None:
            result[i] = ''
        else:
            result[i] = slot[i]
    
    return result

# 把slot转成str
# str: name, location, category, extended, ccf, core, qualis, deadline_from, deadline_to, notice_from, notice_to, begin_from, begin_to, type, author, journal_name, journal_category, ifs, h_index, fenqu, publisher
def copySlot(slot) -> str:
    slots = updateSlot(slot)
    copy = slots['name'] + ';' + slots['location'] + ';' + slots['category'] + ';' + slots['extended'] + ';' + slots['ccf'] + ';' + slots['core'] + ';'
    copy = copy + slots['qualis'] + ';' + slots['deadline_from'] + ';' + slots['deadline_to'] + ';' + slots['notice_from'] + ';'
    copy = copy + slots['notice_to'] + ';' + slots['begin_from'] + ';' + slots['begin_to'] + ';' + slots['type'] + ';' 
    copy = copy + slots['author'] + ';' + slots['journal_name'] + ';' + slots['journal_category'] + ';' + slots['ifs'] + ';' + slots['h_index'] + ';' + slots['fenqu'] + ';' + slots['publisher']
    return copy

# 把copy转成slot
# copy: name, location, category, extended, ccf, core, qualis, deadline_from, deadline_to, notice_from, notice_to, begin_from, begin_to, type, author, journal_category, ifs, h_index, fenqu, publisher
def slotCopy(copy) -> Dict[Text, Any]:
    slot_copys = copy.split(';')
    keys = ['name', 'location', 'category', 'extended', 'ccf', 'core', 'qualis', 'deadline_from', 'deadline_to', 'notice_from', 'notice_to', 'begin_from', 'begin_to', 'type', 'author', 'journal_name', 'journal_category', 'ifs', 'h_index', 'fenqu', 'publisher']
    slot = {}
    for i in range(0, len(keys)):
        slot[keys[i]] = slot_copys[i] if slot_copys[i] != '' else None
    return slot

# 判断lastSlot是否有时间
def hasTime(lastSlot) -> bool:
    slot = slotCopy(lastSlot)
    if slot['deadline_from'] is None and slot['notice_from'] is None and slot['begin_from'] is None:
        return False
    else:
        return True

# 得到lastSlot的type
def getType(lastSlot) -> str:
    slot = slotCopy(lastSlot)
    return slot['type']

# 把slot_copy和slot合并
# 注意slot_copy is list but slot is dict
def mergeSlot(slot_copy, slot) -> Dict[Text, Any]:
    slot_copys = slotCopy(slot_copy)
    for i in slot.keys():
        if slot[i] is not None:
            slot_copys[i] = slot[i]

    return slot_copys