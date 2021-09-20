import sys
from subprocess import Popen, PIPE, STDOUT
import time


def start():
    while True:
        stop(is_stop=False)
        Popen('clear', shell=True)
        cmd = "rasa run --enable-api -p 5004"
        print("Start Serving!")
        Popen(cmd, shell=True)
        time.sleep(86400)


def stop(is_stop=True):
    HOST = '0.0.0.0'
    PORT = '5004'
    # 杀掉服务python进程
    cmd = "netstat -nlp | grep \"%s:%s\"" % (HOST, PORT)
    kill = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=True)
    info = kill.stdout.readlines()
    for each in info:
        each = each.decode('utf-8').split()[6]
        if '/' in each:
            Popen("kill -9 %s -t -f" % each[:each.index('/')], stdout=PIPE, stderr=STDOUT, shell=True)

    # 是否打印信息
    if is_stop:
        print("Stop Serving!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rasa_schedule.py start|stop|restart")
    else:
        if sys.argv[1] == 'start':
            start()
        elif sys.argv[1] == 'stop':
            stop()
        elif sys.argv[1] == 'restart':
            stop()
            start()
        else:
            print("Usage: python rasa_schedule.py start|stop|restart")