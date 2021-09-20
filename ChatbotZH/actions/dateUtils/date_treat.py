import jieba
import jieba.posseg as pseg
from actions.dateUtils import arabic
from refo import finditer, Predicate, Star, Any, Question
import re
import time

# 时间槽值
dateYear_from = None
dateYear_to = None
dateMonth_from = None
dateMonth_to = None
dateDay_from = None
dateDay_to = None
# 特殊设置
time_only_one = 0
recent_type = 1

# 星期字典
weekday_dic = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
# 当前日期
current_year = int(time.strftime("%Y"))
next_year = int(time.strftime("%Y")) + 1
current_month = int(time.strftime("%m"))
current_day = int(time.strftime("%d"))
current_weekday = int(weekday_dic[time.strftime("%A")])

# -----------------后续处理日期需要用到的函数以及数据结构的定义-----------------
# 每个月天数字典
Day_Of_Month0 = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
Day_Of_Month1 = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}


# 分析日期 time str -> date slot
def analyse(times):
    # 更新当前时间
    global current_year, next_year, current_month, current_day, current_weekday
    current_year = int(time.strftime("%Y"))
    next_year = int(time.strftime("%Y")) + 1
    current_month = int(time.strftime("%m"))
    current_day = int(time.strftime("%d"))
    current_weekday = int(weekday_dic[time.strftime("%A")])

    if times == '上半年':
        times = '1月到6月'
    elif times == '下半年':
        times = '7月到12月'
    word_objects = get_word_objects(times)
    # 初始化槽值
    init_state()
    if times == '半年':
        return None
    # 运用规则
    for rule in rules:
        rule.apply(word_objects)


class Word(object):
    def __init__(self, token, pos):
        self.token = token  # 单词
        self.pos = pos  # 词性


# jieba分词
def get_word_objects(sentence):
    # type: (str) -> list

    # 添加人工字典
    date_path = 'actions/dateUtils/date.txt'
    jieba.load_userdict(date_path)

    # 把汉字转成阿拉伯数字
    sentence = arabic.turn(sentence)

    for i in ['年', '月', '日', '号', '周', '今', '昨', '明', '前', '后', '上', '下', '个', '内']:
        sentence = sentence.replace(i, ' %s ' % i)
    Words = [Word(word, tag) for word, tag in pseg.cut(sentence)]  # 获得词性

    for w in Words:
        if w.token in ['年', '月', '日', '号']:
            w.pos = 't'
        if w.token in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            w.pos = 'm'

    res_Words = Words[:]
    for w in Words:
        if w.token == ' ':
            res_Words.remove(w)
    return res_Words


# 槽值初始化
def init_state():
    global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to, time_only_one
    # 日期
    dateYear_from = None
    dateYear_to = None
    dateMonth_from = None
    dateMonth_to = None
    dateDay_from = None
    dateDay_to = None
    # 时间匹配次数
    time_only_one = 0


# 判断是闰年还是平年的函数
def Leap_or_normal(YEAR):
    if int(YEAR) % 4 == 0 and int(YEAR) % 100 != 0:
        return 1
    elif int(YEAR) % 400 == 0:
        return 1
    else:
        return 0


# 判断当前是哪一年
leap = Leap_or_normal(current_year)
if leap:
    Day_Of_Month = Day_Of_Month1
else:
    Day_Of_Month = Day_Of_Month0


# 返回多少天后的日期
def date_plus(year_from, month_from, day_from, day_plus):
    year_to = year_from
    month_to = month_from
    num = day_plus + day_from
    while (num - Day_Of_Month[month_to]) > 0:
        num -= Day_Of_Month[month_to]
        month_to += 1
        if (month_to - 12) > 0:
            month_to -= 12
            year_to += 1
    day_to = num
    return year_to, month_to, day_to


# 返回多少天前的日期
def date_minus(year_from, month_from, day_from, day_minus):
    year_to = year_from
    month_to = month_from
    num = day_minus - day_from
    while num > 0:
        month_to -= 1
        num -= Day_Of_Month[month_to]
        if month_to < 1:
            year_to -= 1
            month_to += 12
    day_to = -num
    return year_to, month_to, day_to


# ------------------------------------------------------------
class W(Predicate):
    def __init__(self, token=".*", pos=".*"):
        self.token = re.compile(token + "$")
        self.pos = re.compile(pos + "$")
        super(W, self).__init__(self.match)

    def match(self, word):
        m1 = self.token.match(word.token)
        m2 = self.pos.match(word.pos)
        return m1 and m2


class Rule(object):
    def __init__(self, condition=None, action=None):
        assert condition and action
        self.condition = condition
        self.action = action

    def apply(self, sentence):
        matches = []
        for m in finditer(self.condition, sentence):
            i, j = m.span()  # 开始位置和结束位置
            matches.extend(sentence[i:j])  # 一个list后追加另一个list的值
        if matches:
            self.action(matches)


class KeywordRule(object):
    def __init__(self, condition=None, action=None, from_or_to=None):
        assert condition and action
        self.condition = condition
        self.action = action
        self.from_or_to = from_or_to

    def apply(self, sentence):
        matches = []
        for m in finditer(self.condition, sentence):
            i, j = m.span()
            matches.extend(sentence[i:j])
        if matches:
            self.action(matches, from_or_to=self.from_or_to)


class QuestionSet:
    def __init__(self):
        pass

    @staticmethod
    def get_date_from_to(word_objects):
        global time_only_one
        time_only_one = 1
        for r in date_from_to_keyword_rules:
            r.apply(word_objects)

    @staticmethod
    def get_exact_date(word_objects):
        global time_only_one
        if time_only_one == 0:
            for r in exact_date_keyword_rules:
                r.apply(word_objects)
            time_only_one = 1

    @staticmethod
    def get_vague_date(word_objects):
        global time_only_one
        if time_only_one == 0:
            for r in vague_date_keyword_rules:
                r.apply(word_objects)
            time_only_one = 1

    @staticmethod
    def addition(word_objects):  # 对于匹配
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        # 根据年/月/日 补充确实的部分
        if dateYear_from is None:
            if dateMonth_from is None:
                if dateDay_from is None:  # none none none
                    pass
                else:  # none none date
                    dateYear_from = current_year
                    dateMonth_from = current_month
            else:
                if dateDay_from is None:  # none month none
                    dateYear_from = current_year
                    dateDay_from = 1
                else:  # none month date
                    dateYear_from = current_year
        else:
            if dateMonth_from is None:
                if dateDay_from is None:  # year none none
                    dateMonth_from = 1
                    dateDay_from = 1
                else:  # year none date
                    dateMonth_from = 1
            else:
                if dateDay_from is None:  # year month none
                    dateDay_from = 1
                else:  # year month date
                    pass

        # 根据年/月/日 补充确实的部分
        if dateYear_to is None:
            if dateMonth_to is None:
                if dateDay_to is None:  # none none none
                    pass
                else:  # none none date
                    dateYear_to = current_year
                    dateMonth_to = current_month
            else:
                if dateDay_to is None:  # none month none
                    dateYear_to = current_year
                    dateDay_to = Day_Of_Month[dateMonth_to]
                else:  # none month date
                    dateYear_to = current_year
        else:
            if dateMonth_to is None:
                if dateDay_to is None:  # year none none
                    dateMonth_to = 12
                    dateDay_to = 31
                else:  # year none date
                    dateMonth_to = current_month
            else:
                if dateDay_to is None:  # year month none
                    dateDay_to = Day_Of_Month[dateMonth_to]
                else:  # year month date
                    pass

        # 如果date_to补全了 而date_from没有补全
        if dateYear_to is not None and dateYear_from is None:
            # 如果date_to在未来
            if InFuture(dateYear_to, dateMonth_to, dateDay_to):
                dateYear_from, dateMonth_from, dateDay_from = current_year, current_month, current_day
            else:
                dateYear_from, dateMonth_from, dateDay_from = 2010, 1, 1

        # 如果date_from补全了 而date_to没有补全
        if dateYear_to is None and dateYear_from is not None:
            # 如果date_from在未来
            if InFuture(dateYear_from, dateMonth_from, dateDay_from):
                dateYear_to, dateMonth_to, dateDay_to = current_year + 2, 12, 31  # 两年可以包含未来所有
            else:
                dateYear_to, dateMonth_to, dateDay_to = current_year, current_month, current_day


# 在未来
def InFuture(year, month, date):
    if year > current_year:
        return True
    elif year == current_year:
        if month > current_month:
            return True
        elif month == current_month:
            if date > current_day:
                return True
    return False


# 定义关键词
class Vague_date_compare:
    '''分析匹配模糊日期'''

    def __init__(self):
        pass

    # ——————————————————年————————————————————————
    @staticmethod
    def last_year_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year - 1 if dateYear_from is None else dateYear_from
        elif from_or_to == 'to':
            dateYear_to = current_year - 1 if dateYear_to is None else dateYear_to
        else:
            dateYear_from = current_year - 1 if dateYear_from is None else dateYear_from
            dateYear_to = current_year - 1 if dateYear_to is None else dateYear_to

    @staticmethod
    def this_year_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year if dateYear_from is None else dateYear_from
        elif from_or_to == 'to':
            dateYear_to = current_year if dateYear_to is None else dateYear_to
        else:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateYear_to = current_year if dateYear_to is None else dateYear_to

    @staticmethod
    def next_year_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year + 1 if dateYear_from is None else dateYear_from
        elif from_or_to == 'to':
            dateYear_to = current_year + 1 if dateYear_to is None else dateYear_to
        else:
            dateYear_from = current_year + 1 if dateYear_from is None else dateYear_from
            dateYear_to = current_year + 1 if dateYear_to is None else dateYear_to

    # ——————————————————月————————————————————————
    @staticmethod
    def last_last_last_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month - 3 if dateMonth_from is None else dateMonth_from
            if dateMonth_from <= 0:
                dateMonth_from += 12 if dateMonth_from is None else dateMonth_from
                dateYear_from -= 1 if dateYear_from is None else dateYear_from
        elif from_or_to == 'to':
            dateYear_to = current_year if dateYear_to is None else dateYear_to
            dateMonth_to = current_month - 3 if dateMonth_to is None else dateMonth_to
            if dateMonth_to <= 0:
                dateMonth_to += 12 if dateMonth_to is None else dateMonth_to
                dateYear_to -= 1 if dateYear_to is None else dateYear_to
        else:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month - 3 if dateMonth_from is None else dateMonth_from
            if dateMonth_from <= 0:
                dateMonth_from += 12
                dateYear_from -= 1
            dateYear_to = dateYear_from if dateYear_to is None else dateYear_to
            dateMonth_to = dateMonth_from if dateMonth_to is None else dateMonth_to

    @staticmethod
    def last_last_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month - 2 if dateMonth_from is None else dateMonth_from
            if dateMonth_from <= 0:
                dateMonth_from += 12
                dateYear_from -= 1
        elif from_or_to == 'to':
            dateYear_to = current_year if dateYear_to is None else dateYear_to
            dateMonth_to = current_month - 2 if dateMonth_to is None else dateMonth_to
            if dateMonth_to <= 0:
                dateMonth_to += 12
                dateYear_to -= 1
        else:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month - 2 if dateMonth_from is None else dateMonth_from
            if dateMonth_from <= 0:
                dateMonth_from += 12
                dateYear_from -= 1
            dateYear_to = dateYear_from if dateYear_to is None else dateYear_to
            dateMonth_to = dateMonth_from if dateMonth_to is None else dateMonth_to

    @staticmethod
    def last_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month - 1 if dateMonth_from is None else dateMonth_from
            if dateMonth_from <= 0:
                dateMonth_from += 12
                dateYear_from -= 1
        elif from_or_to == 'to':
            dateYear_to = current_year if dateYear_to is None else dateYear_to
            dateMonth_to = current_month - 1 if dateMonth_to is None else dateMonth_to
            if dateMonth_to <= 0:
                dateMonth_to += 12
                dateYear_to -= 1
        else:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month - 1 if dateMonth_from is None else dateMonth_from
            if dateMonth_from <= 0:
                dateMonth_from += 12
                dateYear_from -= 1
            dateYear_to = dateYear_from if dateYear_to is None else dateYear_to
            dateMonth_to = dateMonth_from if dateMonth_to is None else dateMonth_to

    @staticmethod
    def this_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month if dateMonth_from is None else dateMonth_from
        elif from_or_to == 'to':
            dateYear_to = current_year if dateYear_to is None else dateYear_to
            dateMonth_to = current_month if dateMonth_to is None else dateMonth_to
        else:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month if dateMonth_from is None else dateMonth_from
            dateYear_to = dateYear_from if dateYear_to is None else dateYear_to
            dateMonth_to = dateMonth_from if dateMonth_to is None else dateMonth_to

    @staticmethod
    def next_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month + 1 if dateMonth_from is None else dateMonth_from
            if dateMonth_from >= 12:
                dateMonth_from = (dateMonth_from - 1) % 12 + 1
                dateYear_from += 1
        elif from_or_to == 'to':
            dateYear_to = current_year if dateYear_to is None else dateYear_to
            dateMonth_to = current_month + 1 if dateMonth_to is None else dateMonth_to
            if dateMonth_to >= 12:
                dateMonth_to = (dateMonth_to - 1) % 12 + 1
                dateYear_to += 1
        else:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month + 1 if dateMonth_from is None else dateMonth_from
            if dateMonth_from >= 12:
                dateMonth_from = (dateMonth_from - 1) % 12 + 1
                dateYear_from += 1
            dateYear_to = dateYear_from if dateYear_to is None else dateYear_to
            dateMonth_to = dateMonth_from if dateMonth_to is None else dateMonth_to

    @staticmethod
    def next_next_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month + 2 if dateMonth_from is None else dateMonth_from
            if dateMonth_from >= 12:
                dateMonth_from = (dateMonth_from - 1) % 12 + 1
                dateYear_from += 1
        elif from_or_to == 'to':
            dateYear_to = current_year if dateYear_to is None else dateYear_to
            dateMonth_to = current_month + 2 if dateMonth_to is None else dateMonth_to
            if dateMonth_to >= 12:
                dateMonth_to = (dateMonth_to - 1) % 12 + 1
                dateYear_to += 1
        else:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month + 2 if dateMonth_from is None else dateMonth_from
            if dateMonth_from >= 12:
                dateMonth_from = (dateMonth_from - 1) % 12 + 1
                dateYear_from += 1
            dateYear_to = dateYear_from if dateYear_to is None else dateYear_to
            dateMonth_to = dateMonth_from if dateMonth_to is None else dateMonth_to

    @staticmethod
    def next_next_next_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month + 3 if dateMonth_from is None else dateMonth_from
            if dateMonth_from >= 12:
                dateMonth_from = (dateMonth_from - 1) % 12 + 1
                dateYear_from += 1
        elif from_or_to == 'to':
            dateYear_to = current_year if dateYear_to is None else dateYear_to
            dateMonth_to = current_month + 3 if dateMonth_to is None else dateMonth_to
            if dateMonth_to >= 12:
                dateMonth_to = (dateMonth_to - 1) % 12 + 1
                dateYear_to += 1
        else:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month + 3 if dateMonth_from is None else dateMonth_from
            if dateMonth_from >= 12:
                dateMonth_from = (dateMonth_from - 1) % 12 + 1
                dateYear_from += 1
            dateYear_to = dateYear_from if dateYear_to is None else dateYear_to
            dateMonth_to = dateMonth_from if dateMonth_to is None else dateMonth_to

    # ——————————————————周————————————————————————
    @staticmethod
    def last_last_last_week_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            day_minus = current_weekday - 1 + 21
            dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                     day_minus)
        elif from_or_to == 'to':
            day_minus = current_weekday - 1 + 21 - 6
            dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day, day_minus)
        else:
            day_minus = current_weekday - 1 + 21
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(dateYear_from, dateMonth_from, dateDay_from, 6)

    @staticmethod
    def last_last_week_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            day_minus = current_weekday - 1 + 14
            dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                     day_minus)
        elif from_or_to == 'to':
            day_minus = current_weekday - 1 + 14 - 6
            dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day, day_minus)
        else:
            day_minus = current_weekday - 1 + 14
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(dateYear_from, dateMonth_from, dateDay_from, 6)

    @staticmethod
    def last_week_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            day_minus = current_weekday - 1 + 7
            dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                     day_minus)
        elif from_or_to == 'to':
            day_minus = current_weekday - 1 + 7 - 6
            dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day, day_minus)
        else:
            day_minus = current_weekday - 1 + 7
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(dateYear_from, dateMonth_from, dateDay_from, 6)

    @staticmethod
    def this_week_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            day_minus = current_weekday - 1
            dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                     day_minus)
        elif from_or_to == 'to':
            day_plus = 1 - current_weekday + 6
            dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            day_minus = current_weekday - 1
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(dateYear_from, dateMonth_from, dateDay_from, 6)

    @staticmethod
    def next_week_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            day_plus = 1 - current_weekday + 7
            dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day, day_plus)
        elif from_or_to == 'to':
            day_plus = 1 - current_weekday + 7 + 6
            dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            day_plus = 1 - current_weekday + 7
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(dateYear_from, dateMonth_from, dateDay_from, 7)

    @staticmethod
    def next_next_week_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            day_plus = 1 - current_weekday + 14
            dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day, day_plus)
        elif from_or_to == 'to':
            day_plus = 1 - current_weekday + 14 + 6
            dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            day_plus = 1 - current_weekday + 14
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(dateYear_from, dateMonth_from, dateDay_from, 7)

    @staticmethod
    def next_next_next_week_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            day_plus = 1 - current_weekday + 21
            dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day, day_plus)
        elif from_or_to == 'to':
            day_plus = 1 - current_weekday + 21 + 6
            dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            day_plus = 1 - current_weekday + 21
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(dateYear_from, dateMonth_from, dateDay_from, 7)

    # ——————————————————日————————————————————————
    @staticmethod
    def last_last_last_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_minus = 3
        if from_or_to == 'from':
            dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                     day_minus)
        elif from_or_to == 'to':
            dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day, day_minus)
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from

    @staticmethod
    def last_last_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_minus = 2
        if from_or_to == 'from':
            dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                     day_minus)
        elif from_or_to == 'to':
            dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day, day_minus)
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from

    @staticmethod
    def last_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_minus = 1
        if from_or_to == 'from':
            dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                     day_minus)
        elif from_or_to == 'to':
            dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day, day_minus)
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from

    @staticmethod
    def this_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            dateYear_from = current_year
            dateMonth_from = current_month
            dateDay_from = current_day
        elif from_or_to == 'to':
            dateYear_to = current_year
            dateMonth_to = current_month
            dateDay_to = current_day
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from = current_year
                dateMonth_from = current_month
                dateDay_from = current_day

            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to = current_year
                dateMonth_to = current_month
                dateDay_to = current_day

    @staticmethod
    def next_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_plus = 1
        if from_or_to == 'from':
            dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                    day_plus)
        elif from_or_to == 'to':
            dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from

    @staticmethod
    def next_next_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_plus = 2
        if from_or_to == 'from':
            dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                    day_plus)
        elif from_or_to == 'to':
            dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from

    @staticmethod
    def next_next_next_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_plus = 3
        if from_or_to == 'from':
            dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                    day_plus)
        elif from_or_to == 'to':
            dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from

    # ——————————————————模糊————————————————————————
    @staticmethod
    def month_after_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        for w in word_objects:
            if w.pos == pos_number:
                month_plus = int(w.token)
        if from_or_to == 'from':
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from = current_year + (current_month + month_plus - 1) // 12
                dateMonth_from = (current_month + month_plus - 1) % 12 + 1
                dateDay_from = current_day
        elif from_or_to == 'to':
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to = current_year + (current_month + month_plus - 1) // 12
                dateMonth_to = (current_month + month_plus - 1) % 12 + 1
                dateDay_to = current_day
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from = current_year + (current_month + month_plus - 1) // 12
                dateMonth_from = (current_month + month_plus - 1) % 12 + 1
                dateDay_from = current_day
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to = current_year + (current_month + month_plus - 1) // 12
                dateMonth_to = (current_month + month_plus - 1) % 12 + 1
                dateDay_to = current_day

    @staticmethod
    def week_after_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        for w in word_objects:
            if w.pos == pos_number:
                day_plus = int(w.token) * 7
        if from_or_to == 'from':
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
        elif from_or_to == 'to':
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day,
                                                                  day_plus)

    @staticmethod
    def day_after_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        for w in word_objects:
            if w.pos == pos_number:
                day_plus = int(w.token)
        if from_or_to == 'from':
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
        elif from_or_to == 'to':
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)

    @staticmethod
    def follow_several_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        month_plus = 0
        for w in word_objects:
            if w.pos == pos_number:
                month_plus = int(w.token)
        if month_plus == 0:  # 如果未设置，默认为3个月
            month_plus = 3

        # 在未来
        if recent_type == 1:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month if dateMonth_from is None else dateMonth_from
            dateDay_from = current_day if dateDay_from is None else dateDay_from

            dateYear_to = current_year + (current_month + month_plus - 1) // 12 if dateYear_to is None else dateYear_to
            dateMonth_to = (current_month + month_plus - 1) % 12 + 1 if dateMonth_to is None else dateMonth_to
            dateDay_to = current_day if dateDay_to is None else dateDay_to
        # 在过去
        else:
            dateYear_from = current_year - 1 + (current_month - month_plus + 11) // 12 if dateYear_from is None else dateYear_from
            dateMonth_from = (current_month - month_plus + 11) % 12 + 1 if dateMonth_from is None else dateMonth_from
            dateDay_from = current_day if dateDay_from is None else dateDay_from

            dateYear_to = current_year if dateYear_to is None else dateYear_to
            dateMonth_to = current_month if dateMonth_to is None else dateMonth_to
            dateDay_to = current_day if dateDay_to is None else dateDay_to

    @staticmethod
    def follow_several_week_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_plus = 0
        for w in word_objects:
            if w.pos == pos_number:
                day_plus = int(w.token) * 7
        if day_plus == 0:  # 如果未设置，默认为3周
            day_plus = 21

        # 在未来
        if recent_type == 1:
            dateYear_from = current_year if dateYear_from is None else dateYear_from
            dateMonth_from = current_month if dateMonth_from is None else dateMonth_from
            dateDay_from = current_day if dateDay_from is None else dateDay_from

            if dateDay_to is None and dateMonth_to is None and dateYear_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            dateYear_to = current_year if dateYear_to is None else dateYear_to
            dateMonth_to = current_month if dateMonth_to is None else dateMonth_to
            dateDay_to = current_day if dateDay_to is None else dateDay_to

            if dateDay_from is None and dateMonth_from is None and dateYear_from is None:
                dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day, day_plus)

    @staticmethod
    def follow_several_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_plus = 0
        for w in word_objects:
            if w.pos == pos_number:
                day_plus = int(w.token)
        if day_plus == 0:  # 如果未设置，默认为7天
            day_plus = 7

        # 在未来
        if recent_type == 1:
            dateYear_from = current_year
            dateMonth_from = current_month
            dateDay_from = current_day

            dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            dateYear_to = current_year
            dateMonth_to = current_month
            dateDay_to = current_day

            dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day, day_plus)

    @staticmethod
    def past_several_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        month_minus = 0
        for w in word_objects:
            if w.pos == pos_number:
                month_minus = int(w.token)
        if month_minus == 0:  # 如果未设置，默认为3个月
            month_minus = 3
        dateYear_from = current_year + (current_month - month_minus - 1) // 12
        dateMonth_from = (current_month - month_minus - 1) % 12 + 1
        dateDay_from = current_day

        dateYear_to = current_year
        dateMonth_to = current_month
        dateDay_to = current_day

    @staticmethod
    def past_several_week_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_minus = 0
        for w in word_objects:
            if w.pos == pos_number:
                day_minus = int(w.token) * 7
        if day_minus == 0:  # 如果未设置，默认是3周
            day_minus = 21
        dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day, day_minus)

        dateYear_to = current_year
        dateMonth_to = current_month
        dateDay_to = current_day

    @staticmethod
    def past_several_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        day_minus = 0
        for w in word_objects:
            if w.pos == pos_number:
                day_minus = int(w.token)
        if day_minus == 0:  # 如果未设置，默认是7
            day_minus = 7
        dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day, day_minus)

        dateYear_to = current_year
        dateMonth_to = current_month
        dateDay_to = current_day


class Exact_date_compare:
    '''分析匹配确切日期'''

    def __init__(self):
        pass

    @staticmethod
    def year_month_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        i = 0
        if from_or_to == 'from':
            for w in word_objects:
                if w.pos == pos_number:
                    if i == 0:
                        dateYear_from = int(w.token) if dateYear_from is None else dateYear_from
                        i += 1
                    elif i == 1:
                        dateMonth_from = int(w.token) if dateMonth_from is None else dateMonth_from
                        i += 1
                    else:
                        dateDay_from = int(w.token) if dateDay_from is None else dateDay_from
        elif from_or_to == 'to':
            for w in word_objects:
                if w.pos == pos_number:
                    if i == 0:
                        dateYear_to = int(w.token) if dateYear_to is None else dateYear_to
                        i += 1
                    elif i == 1:
                        dateMonth_to = int(w.token) if dateMonth_to is None else dateMonth_to
                        i += 1
                    else:
                        dateDay_to = int(w.token) if dateDay_to is None else dateDay_to
        else:
            for w in word_objects:
                if w.pos == pos_number:
                    if i == 0:
                        dateYear_from = int(w.token) if dateYear_from is None else dateYear_from
                        dateYear_to = int(w.token) if dateYear_to is None else dateYear_to
                        i += 1
                    elif i == 1:
                        dateMonth_from = int(w.token) if dateMonth_from is None else dateMonth_from
                        dateMonth_to = int(w.token) if dateMonth_to is None else dateMonth_to
                        i += 1
                    else:
                        dateDay_from = int(w.token) if dateDay_from is None else dateDay_from
                        dateDay_to = int(w.token) if dateDay_to is None else dateDay_to

    @staticmethod
    def year_month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        i = 0
        if from_or_to == 'from':
            for w in word_objects:
                if w.pos == pos_number:
                    if i == 0:
                        dateYear_from = int(w.token) if dateYear_from is None else dateYear_from
                        i += 1
                    elif i == 1:
                        dateMonth_from = int(w.token) if dateMonth_from is None else dateMonth_from
                        i += 1
        elif from_or_to == 'to':
            for w in word_objects:
                if w.pos == pos_number:
                    if i == 0:
                        dateYear_to = int(w.token) if dateYear_to is None else dateYear_to
                        i += 1
                    elif i == 1:
                        dateMonth_to = int(w.token) if dateMonth_to is None else dateMonth_to
                        i += 1
        else:
            for w in word_objects:
                if w.pos == pos_number:
                    if i == 0:
                        dateYear_from = int(w.token) if dateYear_from is None else dateYear_from
                        dateYear_to = int(w.token) if dateYear_to is None else dateYear_to
                        i += 1
                    elif i == 1:
                        dateMonth_from = int(w.token) if dateMonth_from is None else dateMonth_from
                        dateMonth_to = int(w.token) if dateMonth_to is None else dateMonth_to
                        i += 1

    @staticmethod
    def month_day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        i = 0
        if from_or_to == 'from':
            for w in word_objects:
                if w.pos == pos_number:
                    if i == 0:
                        dateMonth_from = int(w.token) if dateMonth_from is None else dateMonth_from
                        i += 1
                    elif i == 1:
                        dateDay_from = int(w.token) if dateDay_from is None else dateDay_from
        elif from_or_to == 'to':
            for w in word_objects:
                if w.pos == pos_number:
                    if i == 0:
                        dateMonth_to = int(w.token) if dateMonth_to is None else dateMonth_to
                        i += 1
                    elif i == 1:
                        dateDay_to = int(w.token) if dateDay_to is None else dateDay_to
        else:
            for w in word_objects:
                if w.pos == pos_number:
                    if i == 0:
                        dateMonth_from = int(w.token) if dateMonth_from is None else dateMonth_from
                        dateMonth_to = int(w.token) if dateMonth_to is None else dateMonth_to
                        i += 1
                    elif i == 1:
                        dateDay_from = int(w.token) if dateDay_from is None else dateDay_from
                        dateDay_to = int(w.token) if dateDay_to is None else dateDay_to

    @staticmethod
    def year_value(word_objects, from_or_to=None):
        global dateYear_from, dateYear_to
        if from_or_to == 'from':
            for w in word_objects:
                if w.pos == pos_number:
                    dateYear_from = int(w.token) if dateYear_from is None else dateYear_from
        elif from_or_to == 'to':
            for w in word_objects:
                if w.pos == pos_number:
                    dateYear_to = int(w.token) if dateYear_to is None else dateYear_to
        else:
            for w in word_objects:
                if w.pos == pos_number:
                    dateYear_from = int(w.token) if dateYear_from is None else dateYear_from
                    dateYear_to = dateYear_from if dateYear_to is None else dateYear_to

    @staticmethod
    def month_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            for w in word_objects:
                if w.pos == pos_number:
                    dateMonth_from = int(w.token) if dateMonth_from is None else dateMonth_from
        elif from_or_to == 'to':
            for w in word_objects:
                if w.pos == pos_number:
                    dateMonth_to = int(w.token) if dateMonth_to is None else dateMonth_to
        else:
            for w in word_objects:
                if w.pos == pos_number:
                    dateMonth_from = int(w.token) if dateMonth_from is None else dateMonth_from
                    dateMonth_to = int(w.token) if dateMonth_to is None else dateMonth_to

    @staticmethod
    def day_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        if from_or_to == 'from':
            for w in word_objects:
                if w.pos == pos_number:
                    dateDay_from = int(w.token) if dateDay_from is None else dateDay_from
        elif from_or_to == 'to':
            for w in word_objects:
                if w.pos == pos_number:
                    dateDay_to = int(w.token) if dateDay_to is None else dateDay_to
        else:
            for w in word_objects:
                if w.pos == pos_number:
                    dateDay_from = int(w.token) if dateDay_from is None else dateDay_from
                    dateDay_to = int(w.token) if dateDay_to is None else dateDay_to

    @staticmethod
    def last_last_weekday_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        for w in word_objects:
            if w.pos == pos_number:
                weekday = int(w.token)
        day_minus = current_weekday + 14 - weekday
        if from_or_to == 'from':
            if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
        elif from_or_to == 'to':
            if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day, day_minus)
        else:
            if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
            if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from

    @staticmethod
    def last_weekday_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        for w in word_objects:
            if w.pos == pos_number:
                weekday = int(w.token)
        day_minus = current_weekday + 7 - weekday
        if from_or_to == 'from':
            if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
        elif from_or_to == 'to':
            if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day, day_minus)
        else:
            if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                         day_minus)
            if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from

    @staticmethod
    def weekday_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        for w in word_objects:
            if w.pos == pos_number:
                weekday = int(w.token)

        if weekday - current_weekday > 0:
            day_plus = weekday - current_weekday
            if from_or_to == 'from':
                if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                    dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                            day_plus)
            elif from_or_to == 'to':
                if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                    dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day,
                                                                      day_plus)
            else:
                if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                    dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                            day_plus)
                if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                    dateYear_to = dateYear_from
                    dateMonth_to = dateMonth_from
                    dateDay_to = dateDay_from
        else:
            day_minus = current_weekday - weekday
            if from_or_to == 'from':
                if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                    dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                             day_minus)
            elif from_or_to == 'to':
                if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                    dateYear_to, dateMonth_to, dateDay_to = date_minus(current_year, current_month, current_day,
                                                                       day_minus)
            else:
                if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                    dateYear_from, dateMonth_from, dateDay_from = date_minus(current_year, current_month, current_day,
                                                                             day_minus)
                if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                    dateYear_to = dateYear_from
                    dateMonth_to = dateMonth_from
                    dateDay_to = dateDay_from

    @staticmethod
    def next_weekday_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        for w in word_objects:
            if w.pos == pos_number:
                weekday = int(w.token)
        day_plus = weekday + 7 - current_weekday
        if from_or_to == 'from':
            if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
        elif from_or_to == 'to':
            if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from

    @staticmethod
    def next_next_weekday_value(word_objects, from_or_to=None):
        global dateYear_from, dateMonth_from, dateDay_from, dateYear_to, dateMonth_to, dateDay_to
        for w in word_objects:
            if w.pos == pos_number:
                weekday = int(w.token)
        day_plus = weekday + 14 - current_weekday
        if from_or_to == 'from':
            if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
        elif from_or_to == 'to':
            if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                dateYear_to, dateMonth_to, dateDay_to = date_plus(current_year, current_month, current_day, day_plus)
        else:
            if dateYear_from is None and dateMonth_from is None and dateDay_from is None:
                dateYear_from, dateMonth_from, dateDay_from = date_plus(current_year, current_month, current_day,
                                                                        day_plus)
            if dateYear_to is None and dateMonth_to is None and dateDay_to is None:
                dateYear_to = dateYear_from
                dateMonth_to = dateMonth_from
                dateDay_to = dateDay_from


# 词汇定义
pos_number = "m"
number_entity = (W(pos=pos_number))
year_entity = (W("20\d\d") | W("19\d\d"))

when = (W("何时") | W("时候") | W("时间"))
where = (W("在哪") | W("何地") | W("地方") | W("地点"))

now = (W("现在"))
past = (W("过去") | W("之?前"))
follow = (W("接下来") | W("最近") | W("近") | W("之?内") | W("未来"))
after = (W("之?后"))
recent = (W("最近") | W("近期") | W("最新") | W("马上") | W("快要") | W("将要") | W("这段时间"))  # 默认在未来 recent_type:1对应未来 0对应过去

last_last_last = (W("大前") | (W("上") + W("上") + W("上") + Question(W("1")) + Question(W("个"))))
last_last = ((W("上") + W("上") + Question(W("1")) + Question(W("个"))) | W("前"))
last = ((W("上") + Question(W("1")) + Question(W("个"))) | W("去") | W("昨"))
this = ((W("这") + Question(W("1")) + Question(W("个"))) | W("今"))
next = ((W("下") + Question(W("1")) + Question(W("个"))) | W("明"))
next_next = ((W("下") + W("下") + Question(W("1")) + Question(W("个"))) | W("后"))
next_next_next = (W("大后") | (W("下") + W("下") + W("下") + Question(W("1")) + Question(W("个"))))
year = (W("年"))
month = (W("月"))
week = (W("周") | W("星期") | W("礼拜"))
day = (W("天"))
several_month = ((number_entity | W("几")) + Question(W("个")) + month)
several_week = ((number_entity | W("几")) + Question(W("个")) + (W("周") | W("星期") | W("礼拜")))
several_day = ((number_entity | W("几")) + W("天"))

vague_date = (((last_last_last | last_last | last | this | next | next_next | next_next_next) + (
        year | month | week | day)) |
              ((past | follow) + (several_month | several_day | several_week)) |
              ((several_month | several_day | several_week) + (past | follow)) |
              follow |
              now | recent |
              ((several_month | several_week | several_day) + after)
              )

exact_year = ((number_entity + W("年")) | year_entity)
exact_month = (number_entity + W("月") + Question(W("份"))) 
exact_day = (number_entity + (W("日") | W("号")))
exact_weekday = ((W("周") | W("星期")) + number_entity)
exact_year_month_day = exact_year + exact_month + exact_day
exact_year_month = (number_entity + W("年") + number_entity + W("月"))
exact_month_day = exact_month + exact_day
weekday = ((last_last | last | this | next | next_next) + exact_weekday)
exact_date = (
        exact_year_month_day | exact_year_month | exact_month_day | exact_year | exact_month | exact_day | weekday)

_from = (W("从") | W("自"))
_to = (W("到") | W("至"))
date_from_to = (Question(_from) + Question(exact_date | vague_date) + _to + (exact_date | vague_date))
'''
    某会议在什么时候开
    某会议在哪开
    某领域的会议什么时候开
    某领域的会议在哪开
    在某地的某时有什么会议 (分两个 模糊日期和确切日期)
    在某地有什么会议       
    在某时有什么会议 (分两个 模糊日期和确切日期)
    某会议的其他信息(包含call for papers、截稿日期) 

待补充
'''

"""
查找顺序:
1. 名称
2. 领域
3. 地点
4. 模糊时间
5. 确切时间：年月日
6. 确切时间：月日
7. 确切时间：日
8. CFPs
9. 截稿日期
10.延期
....其他规则待补充
"""
rules = [
    Rule(condition=date_from_to, action=QuestionSet.get_date_from_to),
    Rule(condition=exact_date, action=QuestionSet.get_exact_date),
    Rule(condition=vague_date, action=QuestionSet.get_vague_date),
    # 补充规则，用来补全缺失的日期槽值
    Rule(condition=Star(Any(), greedy=True), action=QuestionSet.addition)
]
# 模糊日期匹配
vague_date_keyword_rules = [
    KeywordRule(condition=last + year, action=Vague_date_compare.last_year_value),
    KeywordRule(condition=this + year, action=Vague_date_compare.this_year_value),
    KeywordRule(condition=next + year, action=Vague_date_compare.next_year_value),

    KeywordRule(condition=last_last_last + month, action=Vague_date_compare.last_last_last_month_value),
    KeywordRule(condition=last_last + month, action=Vague_date_compare.last_last_month_value),
    KeywordRule(condition=last + month, action=Vague_date_compare.last_month_value),
    KeywordRule(condition=this + month, action=Vague_date_compare.this_month_value),
    KeywordRule(condition=next_next_next + month, action=Vague_date_compare.next_next_next_month_value),
    KeywordRule(condition=next_next + month, action=Vague_date_compare.next_next_month_value),
    KeywordRule(condition=next + month, action=Vague_date_compare.next_month_value),

    KeywordRule(condition=last_last_last + week, action=Vague_date_compare.last_last_last_week_value),
    KeywordRule(condition=last_last + week, action=Vague_date_compare.last_last_week_value),
    KeywordRule(condition=last + week, action=Vague_date_compare.last_week_value),
    KeywordRule(condition=next_next_next + week, action=Vague_date_compare.next_next_next_week_value),
    KeywordRule(condition=next_next + week, action=Vague_date_compare.next_next_week_value),
    KeywordRule(condition=next + week, action=Vague_date_compare.next_week_value),
    KeywordRule(condition=this + week, action=Vague_date_compare.this_week_value),

    KeywordRule(condition=last_last_last + day, action=Vague_date_compare.last_last_last_day_value),
    KeywordRule(condition=last_last + day, action=Vague_date_compare.last_last_day_value),
    KeywordRule(condition=last + day, action=Vague_date_compare.last_day_value),
    KeywordRule(condition=next_next_next + day, action=Vague_date_compare.next_next_next_day_value),
    KeywordRule(condition=next_next + day, action=Vague_date_compare.next_next_day_value),
    KeywordRule(condition=next + day, action=Vague_date_compare.next_day_value),
    KeywordRule(condition=((this + day) | now), action=Vague_date_compare.this_day_value),

    KeywordRule(condition=several_month + after, action=Vague_date_compare.month_after_value),
    KeywordRule(condition=several_week + after, action=Vague_date_compare.week_after_value),
    KeywordRule(condition=several_day + after, action=Vague_date_compare.day_after_value),
    KeywordRule(condition=((follow + several_month) | (several_month + follow)),
                action=Vague_date_compare.follow_several_month_value),
    KeywordRule(condition=((past + several_month) | (several_month + past)),
                action=Vague_date_compare.past_several_month_value),
    KeywordRule(condition=((follow + several_week) | (several_week + follow)),
                action=Vague_date_compare.follow_several_week_value),
    KeywordRule(condition=((past + several_week) | (several_week + past)),
                action=Vague_date_compare.past_several_week_value),
    KeywordRule(condition=((follow + several_day) | (several_day + follow)),
                action=Vague_date_compare.follow_several_day_value),
    KeywordRule(condition=((past + several_day) | (several_day + past)),
                action=Vague_date_compare.past_several_day_value),
    KeywordRule(condition=recent, action=Vague_date_compare.follow_several_month_value)
]
# 确定日期匹配
exact_date_keyword_rules = [
    KeywordRule(condition=exact_year_month_day, action=Exact_date_compare.year_month_day_value),
    KeywordRule(condition=exact_year_month, action=Exact_date_compare.year_month_value),
    KeywordRule(condition=exact_month_day, action=Exact_date_compare.month_day_value),
    KeywordRule(condition=exact_year, action=Exact_date_compare.year_value),
    KeywordRule(condition=exact_month, action=Exact_date_compare.month_value),
    KeywordRule(condition=exact_day, action=Exact_date_compare.day_value),
    KeywordRule(condition=last_last + exact_weekday, action=Exact_date_compare.last_last_weekday_value),
    KeywordRule(condition=last + exact_weekday, action=Exact_date_compare.last_weekday_value),
    KeywordRule(condition=next_next + exact_weekday, action=Exact_date_compare.next_next_weekday_value),
    KeywordRule(condition=next + exact_weekday, action=Exact_date_compare.next_weekday_value),
    KeywordRule(condition=exact_weekday, action=Exact_date_compare.weekday_value)
]
# 从...到...日期匹配
date_from_to_keyword_rules = [
    # ------------------------从------------------------------
    KeywordRule(condition=Question(_from) + last + year + _to, action=Vague_date_compare.last_year_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + this + year + _to, action=Vague_date_compare.this_year_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next + year + _to, action=Vague_date_compare.next_year_value,
                from_or_to='from'),

    KeywordRule(condition=Question(_from) + last_last_last + month + _to,
                action=Vague_date_compare.last_last_last_month_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + last_last + month + _to, action=Vague_date_compare.last_last_month_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + last + month + _to, action=Vague_date_compare.last_month_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + this + month + _to, action=Vague_date_compare.this_month_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next + month + _to, action=Vague_date_compare.next_month_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next_next + month + _to, action=Vague_date_compare.next_next_month_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next_next_next + month + _to,
                action=Vague_date_compare.next_next_next_month_value,
                from_or_to='from'),

    KeywordRule(condition=Question(_from) + last_last_last + week + _to,
                action=Vague_date_compare.last_last_last_week_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + last_last + week + _to, action=Vague_date_compare.last_last_week_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + last + week + _to, action=Vague_date_compare.last_week_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + this + week + _to, action=Vague_date_compare.this_week_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next + week + _to, action=Vague_date_compare.next_week_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next_next + week + _to, action=Vague_date_compare.next_next_week_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next_next_next + week + _to,
                action=Vague_date_compare.next_next_next_week_value,
                from_or_to='from'),

    KeywordRule(condition=Question(_from) + last_last_last + day + _to,
                action=Vague_date_compare.last_last_last_day_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + last_last + day + _to, action=Vague_date_compare.last_last_day_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + last + day + _to, action=Vague_date_compare.last_day_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next + day + _to, action=Vague_date_compare.next_day_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next_next + day + _to, action=Vague_date_compare.next_next_day_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next_next_next + day + _to,
                action=Vague_date_compare.next_next_next_day_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + ((this + day) | now) + _to, action=Vague_date_compare.this_day_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + several_month + after + _to, action=Vague_date_compare.month_after_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + several_week + after + _to, action=Vague_date_compare.week_after_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + several_day + after + _to, action=Vague_date_compare.day_after_value,
                from_or_to='from'),

    KeywordRule(condition=Question(_from) + exact_year_month_day + _to, action=Exact_date_compare.year_month_day_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + exact_year_month + _to, action=Exact_date_compare.year_month_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + exact_month_day + _to, action=Exact_date_compare.month_day_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + exact_year + _to, action=Exact_date_compare.year_value, from_or_to='from'),
    KeywordRule(condition=Question(_from) + exact_month + _to, action=Exact_date_compare.month_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + exact_day + _to, action=Exact_date_compare.day_value, from_or_to='from'),
    KeywordRule(condition=Question(_from) + last_last + exact_weekday + _to,
                action=Exact_date_compare.last_last_weekday_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + last + exact_weekday + _to, action=Exact_date_compare.last_weekday_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next_next + exact_weekday + _to,
                action=Exact_date_compare.next_next_weekday_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + next + exact_weekday + _to, action=Exact_date_compare.next_weekday_value,
                from_or_to='from'),
    KeywordRule(condition=Question(_from) + exact_weekday + _to, action=Exact_date_compare.weekday_value,
                from_or_to='from'),

    # -----------------------到------------------------
    KeywordRule(condition=_to + last + year, action=Vague_date_compare.last_year_value, from_or_to='to'),
    KeywordRule(condition=_to + this + year, action=Vague_date_compare.this_year_value, from_or_to='to'),
    KeywordRule(condition=_to + next + year, action=Vague_date_compare.next_year_value, from_or_to='to'),

    KeywordRule(condition=_to + last_last_last + month,
                action=Vague_date_compare.last_last_last_month_value, from_or_to='to'),
    KeywordRule(condition=_to + last_last + month,
                action=Vague_date_compare.last_last_month_value, from_or_to='to'),
    KeywordRule(condition=_to + last + month, action=Vague_date_compare.last_month_value, from_or_to='to'),
    KeywordRule(condition=_to + this + month, action=Vague_date_compare.this_month_value, from_or_to='to'),
    KeywordRule(condition=_to + next + month, action=Vague_date_compare.next_month_value, from_or_to='to'),
    KeywordRule(condition=_to + next_next + month,
                action=Vague_date_compare.next_next_month_value, from_or_to='to'),
    KeywordRule(condition=_to + next_next_next + month,
                action=Vague_date_compare.next_next_next_month_value, from_or_to='to'),

    KeywordRule(condition=_to + last_last_last + week,
                action=Vague_date_compare.last_last_last_week_value, from_or_to='to'),
    KeywordRule(condition=_to + last_last + week, action=Vague_date_compare.last_last_week_value, from_or_to='to'),
    KeywordRule(condition=_to + last + week, action=Vague_date_compare.last_week_value, from_or_to='to'),
    KeywordRule(condition=_to + this + week, action=Vague_date_compare.this_week_value, from_or_to='to'),
    KeywordRule(condition=_to + next + week, action=Vague_date_compare.next_week_value, from_or_to='to'),
    KeywordRule(condition=_to + next_next + week, action=Vague_date_compare.next_next_week_value, from_or_to='to'),
    KeywordRule(condition=_to + next_next_next + week,
                action=Vague_date_compare.next_next_next_week_value, from_or_to='to'),

    KeywordRule(condition=_to + last_last_last + day,
                action=Vague_date_compare.last_last_last_day_value, from_or_to='to'),
    KeywordRule(condition=_to + last_last + day, action=Vague_date_compare.last_last_day_value, from_or_to='to'),
    KeywordRule(condition=_to + last + day, action=Vague_date_compare.last_day_value, from_or_to='to'),
    KeywordRule(condition=_to + next + day, action=Vague_date_compare.next_day_value, from_or_to='to'),
    KeywordRule(condition=_to + next_next + day, action=Vague_date_compare.next_next_day_value, from_or_to='to'),
    KeywordRule(condition=_to + next_next_next + day,
                action=Vague_date_compare.next_next_next_day_value, from_or_to='to'),
    KeywordRule(condition=_to + ((this + day) | now), action=Vague_date_compare.this_day_value, from_or_to='to'),
    KeywordRule(condition=_to + several_month + after, action=Vague_date_compare.month_after_value, from_or_to='to'),
    KeywordRule(condition=_to + several_week + after, action=Vague_date_compare.week_after_value, from_or_to='to'),
    KeywordRule(condition=_to + several_day + after, action=Vague_date_compare.day_after_value, from_or_to='to'),

    KeywordRule(condition=_to + exact_year_month_day,
                action=Exact_date_compare.year_month_day_value, from_or_to='to'),
    KeywordRule(condition=_to + exact_year_month, action=Exact_date_compare.year_month_value, from_or_to='to'),
    KeywordRule(condition=_to + exact_month_day, action=Exact_date_compare.month_day_value, from_or_to='to'),
    KeywordRule(condition=_to + exact_year, action=Exact_date_compare.year_value, from_or_to='to'),
    KeywordRule(condition=_to + exact_month, action=Exact_date_compare.month_value, from_or_to='to'),
    KeywordRule(condition=_to + exact_day, action=Exact_date_compare.day_value, from_or_to='to'),
    KeywordRule(condition=_to + last_last + exact_weekday, action=Exact_date_compare.last_last_weekday_value,
                from_or_to='to'),
    KeywordRule(condition=_to + last + exact_weekday, action=Exact_date_compare.last_weekday_value, from_or_to='to'),
    KeywordRule(condition=_to + next_next + exact_weekday, action=Exact_date_compare.next_next_weekday_value,
                from_or_to='to'),
    KeywordRule(condition=_to + next + exact_weekday, action=Exact_date_compare.next_weekday_value, from_or_to='to'),
    KeywordRule(condition=_to + exact_weekday, action=Exact_date_compare.weekday_value, from_or_to='to')
]

if __name__ == '__main__':
    recent_type = 0
    analyse("最近")
