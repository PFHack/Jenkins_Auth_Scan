# -*- coding: utf-8 -*-
# @Time    : 2022/8/23 14:36
# @Author  : PFinal南丞
# @Email   : lampxiezi@163.com
# @File    : scan.py
# @Software: PyCharm
import sys
import threading
from queue import Queue

import requests
from zoomeye.sdk import ZoomEye

yellow = '\033[01;33m'
white = '\033[01;37m'
green = '\033[01;32m'
blue = '\033[01;34m'
red = '\033[1;31m'
end = '\033[0m'

version = 'v0.1'
message = white + '{' + red + version + ' #dev' + white + '}'

jenkins_scan_banner = f"""
{yellow} JenkinsAuthScan is a tool to Scan for unauthorized {yellow}
       _            _    _                         _   _      _____                 
      | |          | |  (_)             /\        | | | |    / ____|                 {message}{green}
      | | ___ _ __ | | ___ _ __  ___   /  \  _   _| |_| |__ | (___   ___ __ _ _ __   {blue}
  _   | |/ _ \ '_ \| |/ / | '_ \/ __| / /\ \| | | | __| '_ \ \___ \ / __/ _` | '_ \  {blue}
 | |__| |  __/ | | |   <| | | | \__ \/ ____ \ |_| | |_| | | |____) | (_| (_| | | | | {green}
  \____/ \___|_| |_|_|\_\_|_| |_|___/_/    \_\__,_|\__|_| |_|_____/ \___\__,_|_| |_| {white}PFinal南丞{white}
  
{red}JenkinsAuthScan is under development, please update before each use!{end}
"""
data_queue = Queue()  # 存放解析数据的queue
flag = False


class Crawl_thread(threading.Thread):
    def __init__(self, thread_id, queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue

    def run(self):
        print("启动线程:", self.thread_id)
        self.crawl_threads()
        print("退出了该线程:", self.thread_id)

    def crawl_threads(self):
        zm = ZoomEye()
        zm.username = ''
        zm.password = ''
        try:
            zm.login()
            while True:
                if self.queue.empty():  # 如果队列为空，则跳出
                    break
                else:
                    page = self.queue.get()
                    print('当前工作的线程为：', self.thread_id, " 正在采集：", page)
                    try:
                        data = zm.dork_search('app:"Jenkins" +country:"CN"', page)
                        for ip in zm.dork_filter("ip,port"):
                            data_queue.put(str(ip[0]) + ':' + str(ip[1]))  # 将采集的结果放入data_queue中
                    except Exception as e:
                        print('采集线程错误', e)
        except ValueError as e:
            print(e)


class Parser_thread(threading.Thread):
    def __init__(self, thread_id, queue, file):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
        self.file = file

    def run(self):
        print('启动线程：', self.thread_id)
        while not flag:
            try:
                item = self.queue.get(False)  # get参数为false时队列为空，会抛出异常
                if not item:
                    pass
                self.parse_data(item)
                self.queue.task_done()  # 每当发出一次get操作，就会提示是否堵塞
            except Exception as e:
                print(e)
                pass

    def parse_data(self, item):
        try:
            self.file.write(item + "\n")
            script_url = 'http://' + item + '/script'
            r = requests.get(script_url)
            print(r.status_code)
        except Exception as e:
            print(e)


def scan():
    output = open('scan.txt', 'a', encoding='utf-8')  # 将结果保存到一个json文件中
    pageQueue = Queue(50)  # 任务队列，存放网页的队列
    for page in range(1, 10):
        pageQueue.put(page)  # 构造任务队列

    # 初始化采集线程
    crawl_threads = []
    crawl_name_list = ['crawl_1', 'crawl_2', 'crawl_3']  # 总共构造3个爬虫线程
    try:
        for thread_id in crawl_name_list:
            thread = Crawl_thread(thread_id, pageQueue)  # 启动爬虫线程
            thread.start()  # 启动线程
            crawl_threads.append(thread)
    except Exception as e:
        print(e)
        exit()

    # 等待队列情况，先进行网页的抓取
    while not pageQueue.empty():  # 判断是否为空
        pass  # 不为空，则继续阻塞

    # 等待所有线程结束
    for t in crawl_threads:
        t.join()

        # 初始化解析线程
    parse_thread = []
    parser_name_list = ['parse_1', 'parse_2', 'parse_3']
    for thread_id in parser_name_list:  #
        thread = Parser_thread(thread_id, data_queue, output)
        thread.start()  # 启动线程
        parse_thread.append(thread)

    # 等待队列情况，对采集的页面队列中的页面进行解析，等待所有页面解析完成
    while not data_queue.empty():
        pass
    # 通知线程退出
    global flag
    flag = True
    for t in parse_thread:
        t.join()  # 等待所有线程执行到此处再继续往下执行

    print('退出主线程')
    output.close()


if __name__ == '__main__':
    print(jenkins_scan_banner)
    if len(sys.argv[1:]) <= 0:
        print("请传递要操作的参数:   \n -s scan  \n-w  尝试连接 写入 ssh key")
        exit()
    if sys.argv[1:][0].find("-s=") >= 0:
        if sys.argv[1:][0].split("=")[1] == "zoom":
            scan()
        elif sys.argv[1:][0].split("=")[1] == "censys":
            pass
        else:
            print(f"{green}^_^ == RedisAuthScan 平台目前只支持  zoomeye，Shodan 平台扫描 {end}")
            exit()

    if sys.argv[1:][0] == "-e":
        pass
        # exploit()
