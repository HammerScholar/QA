import random
from urllib.request import Request, urlopen
from urllib import parse
import hashlib
import json

appid = '20210413000775885'
secretKey = 'DZpSeASsT2Lnbn8yQB8c'
url_baidu = 'http://api.fanyi.baidu.com/api/trans/vip/translate'


def translateBaidu(text, f='zh', t='en'):
    try:
        salt = random.randint(32768, 65536)
        sign = appid + text + str(salt) + secretKey
        sign = hashlib.md5(sign.encode()).hexdigest()
        url = url_baidu + '?appid=' + appid + '&q=' + parse.quote(text) + '&from=' + f + '&to=' + t + \
              '&salt=' + str(salt) + '&sign=' + sign
        response = urlopen(url)
        content = response.read().decode('utf-8')
        data = json.loads(content)
        result = str(data['trans_result'][0]['dst'])
        return result
    except:
        print(text, "翻译出错")
        return None


# test
def translateCategory():
    fw = open('category.json', 'r', encoding='UTF-8')
    tasks = json.load(fw)
    fw.close()
    # 生成会议领域列表
    conf_category = []
    for j in tasks:
        category = tasks[j].split(',')
        for i in category:
            if i.upper() not in conf_category:
                conf_category.append(i.upper())

    maps = {}
    count = 0
    for i in conf_category:
        a = translateBaidu(i, f='en', t='zh')
        maps[i] = a
        count = count + 1
        print(count)

    fw = open('category.json', 'w', encoding='UTF-8')
    json.dump(maps, fw)
    fw.close()


if __name__ == '__main__':
    # translateCategory()
    fw = open('category.json', 'r', encoding='UTF-8')
    d = json.load(fw)
    fw.close()

    fw = open('category.json', 'w', encoding='UTF-8')
    json.dump(d, fw, ensure_ascii=False)
    fw.close()
