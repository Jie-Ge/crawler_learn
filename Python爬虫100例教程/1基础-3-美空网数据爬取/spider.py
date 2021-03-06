

# -*- coding: UTF-8 -*-
import requests  # 网络请求模块
import random  # 随机模块
import re  # 正则表达式模块
import time  # 时间模块
import threading  # 线程模块
import pymongo  # mongodb模块
from lxml import etree

'''
参考：https://blog.csdn.net/hihell/article/details/82703695
需求：爬取图片网站的所有图片
技术：
'''

all_detail_urls = []
# 起始种子地址
urls = ["https://douge2013.zcool.com.cn/follow?condition=0&p=1"]


# 生产者，获取各个用户的关注列表，并拿到各用户详情页链接
class Producer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)  # 在自写的类中的init中需要先初始化Thread
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'
        }

    def run(self):

        global urls
        global threadLock
        while len(urls) > 0:
            # print('urls>>>>>>>>>>>>>', urls)
            threadLock.acquire()
            url = urls.pop()
            threadLock.release()
            text = ''
            try:
                # print('1111111')
                text = requests.get(url, headers=self.headers).text
                # print('2222222')
            except:
                print('Producer异常')

            page = etree.HTML(text)
            this_detail_urls = page.xpath('//p[@class="author-info-title"]/a/@href')
            # print('this_detail_urls>>>>>>', this_detail_urls)

            global all_detail_urls

            # threadLock.acquire()
            all_detail_urls += this_detail_urls
            # threadLock.release()
            # print('all_detail_urls>>>>>>>>>', all_detail_urls)
            new_list_urls = []

            for detail_url in this_detail_urls:
                new_url = detail_url + '/follow?condition=0&p=1'
                new_list_urls.append(new_url)

            urls += new_list_urls

            time.sleep(0.5)


threadLock = threading.Lock()
myclient = pymongo.MongoClient('127.0.0.1', 27017)
eg_100_db = myclient['eg_100_db']

index = 0


# 访问详情页链接，并拿到图片地址，进而拿到图片，并保存到数据库
class Consumer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)  # 在自写的类中的init中需要先初始化Thread
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36'
        }

    def run(self):

        global pic_db
        global threadLock
        global index

        # # 这个地方写成死循环，为的是不断监控图片链接数组是否更新
        while True:
            print('Consumer is starting.......')
            global all_detail_urls

            try:
                print('>>>>>>>>>>>>333333333333')
                threadLock.acquire()
                detail_url = all_detail_urls.pop()  # 这里出错会直接抛出异常，就不会释放锁，会一直锁死
                threadLock.release()
                print('>>>>>>>>>>>>44444444444')
                # print('>>>>>>>>>>>>5555555555555')
                text = requests.get(detail_url, headers=self.headers).text
                page = etree.HTML(text)
                img_srcs = page.xpath('//div[@class="card-img"]//img/@src')
                # print('>>>>>>>>>>>>666666666666')
                for img_src in img_srcs:
                    img = requests.get(img_src, headers=self.headers).content
                    print('>>>>>>>>>>>>77777777777777')
                    threadLock.acquire()
                    index += 1
                    threadLock.release()
                    print('>>>>>>>>>>>>888888888888')
                    data = {'_id': index, 'pic': img}

                    eg_100_db.pic_3.insert_one(data)

                    print('success save !!!')

            except Exception as e:
                print('Consumer error !!!!!')
                threadLock.release()

            time.sleep(0.5)


if __name__ == "__main__":
    # 开启5个线程
    for t in range(5):
        p = Producer()
        p.start()

    # # 开启5个线程
    for t in range(5):
        c = Consumer()
        c.start()

