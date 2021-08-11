from amazoncaptcha import AmazonCaptcha
import scrapy
from random import choice
import re
from random import choice
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from lxml import etree
import lxml.html
from lxml.cssselect import CSSSelector


class BaseSpider(scrapy.Spider):
    def __init__(self):
        self.proxies = self.proxy_generator()



    def solve_captcha(self, reponse):
        print("Attempting to bypass captcha")
        captcha_url = response.xpath('//div[@class="a-row a-text-center"]/img/@src').attrib['src']
        captcha = AmazonCaptcha.fromlink(captcha_image_url)
        solution = captcha.solve()
        breakpoint()
        yield FormRequest.from_response(
            response,
            formdata={'field-keywords': solution},
            callback=origin_method
        )



    def proxy_generator(self):
        proxies = []
        try:
            response = requests.get(url="https://spys.me/proxy.txt", headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            proxy_table = str(soup).split('\n')
            proxy_table = proxy_table[9:-3]
            
            for proxy in proxy_table:
                start_index = proxy.find(':')
                end_index = proxy.find(' ')
                proxies.append(proxy[:start_index] + proxy[start_index+1:end_index])

            with open(dirname(dirname(abspath(__file__))) + "/proxy_list.txt", 'w') as f:
                for item in proxies:
                    f.write("%s\n" % item['https'])
            return proxies
        except Exception as e:
            print(e)
            self.error_msg = "Unable to process proxies"
            return None