# -*- coding: UTF-8 –*
"""
@create 2021-07-07
"""
import os
import re
import cv2
import time
import json
import random
import selenium
import numpy as np
import pandas as pd
from selenium import webdriver
import matplotlib.pyplot as plt
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

current_path = os.path.abspath(__file__)
root_path = os.path.dirname(current_path)
config_basic_path = os.path.join(root_path, 'config')
tmp_basic_path = os.path.join(root_path, 'tmp')


def get_driver_by_login():
    url = "https://dian.ysbang.cn/#/login"
    # 获取用户名密码
    with open(os.path.join(config_basic_path, "user.conf")) as f:
        user_config = f.read()
        user_config = json.loads(user_config)
    # 登录操作
    opt = webdriver.ChromeOptions()
    opt.add_argument('--headless')
    opt.add_argument('--disable-gpu')
    opt.add_argument('--disable-software-rasterizer')
    capabilities = DesiredCapabilities.CHROME.copy()
    capabilities['acceptSslCerts'] = True
    capabilities['acceptInsecureCerts'] = True
    # chrome与驱动版本 http://chromedriver.chromium.org/downloads
    driver = webdriver.Chrome(executable_path=os.path.join(root_path, "chromedriver.exe"), chrome_options=opt, desired_capabilities=capabilities)
    driver.get(url)
    driver.set_window_size(1920, 1080)
    driver.find_element_by_xpath("//input[@id='userAccount']").send_keys(user_config["name"])
    driver.find_element_by_xpath("//input[@id='password']").send_keys(user_config["password"])
    rect = driver.find_element_by_xpath("//img[@id='captchaImg']").rect  # 验证码位置
    image_name = str(int(time.time())) + ".png"
    image_path = os.path.join(tmp_basic_path, image_name)
    driver.save_screenshot(image_path)
    image = cv2.imread(image_path)
    image = image[rect["y"]:rect["y"] + rect["height"], rect["x"]:rect["x"] + rect["width"]]
    plt.imshow(image)
    plt.show(block=False)
    captcha = input("请输入验证码：")
    driver.find_element_by_xpath("//input[@id='captcha']").send_keys(captcha)
    driver.find_element_by_xpath("//button[@id='loginBtn']").click()
    time.sleep(10)
    return driver


def search(keyword):
    search_elem = driver.find_element_by_xpath("//input[@id='searchKey']")
    search_elem.send_keys(Keys.CONTROL + "a" + Keys.DELETE)
    search_elem.send_keys(keyword)
    driver.find_element_by_xpath("//span[@class='search-btn']").click()
    time.sleep(5)
    # 点击搜索结果
    total = len(driver.find_elements_by_xpath("//div[@class='drug-list']/div[@class='drug-drugInfo']"))
    for i in range(total):
        try:
            driver.find_element_by_xpath("//div[@class='drug-drugInfo'][@d-index='{}']".format(i)).click()
            time.sleep(5)
            if len(driver.window_handles) < 2:
                driver.find_element_by_xpath("//div[@class='drug-drugInfo'][@d-index='{}']".format(i)).click()
                time.sleep(5)
            driver.switch_to.window(driver.window_handles[1])
            text = driver.page_source
            # print(text)
            name_elem = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//div[@class='drug-name emphasized']")))
            name = name_elem.text  # 名称
            elems = driver.find_elements_by_xpath("//button[text()='参与拼团']")
            if len(elems) > 0:  # 不采集拼团
                print(name)
            else:
                try:
                    common_name = driver.find_element_by_xpath("//div[@class='new-drugInfo-div-content-cell2-content-p-content']/p").text  # 商品名称
                except:
                    driver.find_element_by_xpath("(//div[@class='new-drugInfo-div-tab-cell'])[1]").click()
                    time.sleep(1)
                    common_name = driver.find_element_by_xpath("//div[@class='new-drugInfo-div-content-cell2-content-p-content']/p").text  # 商品名称
                approval = driver.find_element_by_xpath("//div[@class='drug-info']/p[1]/span[2]").text  # 批准文号
                specification = driver.find_element_by_xpath("//div[@class='drug-info']/p[2]/span[2]").text  # 规格
                manufacturer = re.sub(r'[\s\S]+>生产厂家</span>[\s\S]+?<span.+?>([\s\S]+?)<[\s\S]+', r'\1', text)  # 生产厂家
                expireDate = re.sub(r'[\s\S]+>有效期至</span>[\s\S]+?<span.+?>([\s\S]+?)<[\s\S]+', r'\1', text)  # 有效期
                price = driver.find_element_by_xpath("//span[@class='current-price text-orange']").text  # 采购价
                try:
                    dis_price = driver.find_element_by_xpath("//div[@class='tooltip-wrap discount-tooltip gap-right-10']/div").text  # 折后价
                    dis_price = dis_price.replace("折后约 ¥", "")
                except selenium.common.exceptions.NoSuchElementException:
                    dis_price = ""
                provider_name = driver.find_element_by_xpath("//div[@class='ellipsis2']").text  # 商家名称
                print_text = """
                名称：{}
                商品名称：{}
                批准文号：{}
                规格：{}
                生产厂家：{}
                有效期：{}
                采购价：{}
                折后价：{}
                商家名称：{}
                """.format(name, common_name, approval, specification, manufacturer, expireDate, price, dis_price, provider_name)
                print(print_text)
                print("============================================")
                save_data.append([name, common_name, approval, specification, manufacturer, expireDate, price, dis_price, provider_name])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            # break  # 快速测试
        except Exception as e:
            print(e)


def get_search_data_detail():
    with open(os.path.join(root_path, "keywords.txt"), encoding="utf-8") as f:
        while True:
            line_text = f.readline()
            if line_text:
                print("正在采集关键词：{}".format(line_text))
                search(line_text)
                print("结束采集关键词：{}".format(line_text))
                # time.sleep(2)  # 降低访问频率
                time.sleep(random.randint(1, 4))
            else:
                break


def save():
    if save_data:
        print("开始保存")
        df = pd.DataFrame(np.array(save_data))
        df.to_csv('result\data.csv', encoding="utf_8_sig")
        print("保存成功")


if __name__ == "__main__":
    driver = get_driver_by_login()
    save_data = []
    get_search_data_detail()
    save()

