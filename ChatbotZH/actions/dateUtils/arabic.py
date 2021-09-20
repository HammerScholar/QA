'''
将句子中的大写数字转换为阿拉伯数字
'''

CN_NUM = {
    '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '零': 0,
    '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '貮': 2, '两': 2,
}

CN_UNIT = {
    '十': 10,
    '百': 100,
    '千': 1000,
    '万': 10000,
    '亿': 100000000
}
CN_KEY = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '百', '千', '两']


def arabic(cn):
    # 将大写数字转换为阿拉伯数字
    unit = 0  # current
    ldig = []  # digest
    for cndig in reversed(cn):
        if cndig in CN_UNIT:
            unit = CN_UNIT.get(cndig)
            if unit == 10000 or unit == 100000000:
                ldig.append(unit)
                unit = 1
        else:
            dig = CN_NUM.get(cndig)
            if unit:
                dig *= unit
                unit = 0
            ldig.append(dig)
    # 特例：十二
    if unit == 10:
        ldig.append(10)
    val, tmp = 0, 0
    for x in reversed(ldig):
        if x == 10000 or x == 100000000:
            val += tmp * x
            tmp = 0
        else:
            tmp += x
    val += tmp
    return val


def turn(sentence):
    NUM = ''
    result = ''
    flag = 0
    for word in sentence:
        if word in CN_KEY:
            if flag == 0:
                NUM += word
                flag = 1
            else:
                NUM += word
        else:
            if flag == 0:
                result += word
            else:
                result += str(arabic(NUM))
                result += word
                flag = 0
                NUM = ''
    if NUM != '':
        result += str(arabic(NUM))

    return result


# TODO 用于测试
if __name__ == "__main__":
    while True:
        sentence = input("请输入句子：")
        print(turn(sentence))
