'''
Author: LetMeFly, Guo-Chenxu, Crsuh2er0, 420xincheng, tkzzzzzz6
Date: 2023-09-12 20:49:21
LastEditors: LetMeFly.xyz
LastEditTime: 2025-11-13 22:44:00
Description: 开源于https://github.com/LetMeFly666/YuketangAutoPlayer 欢迎issue、PR
'''
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from typing import List
from time import sleep
import random
import os
import sys
import configparser


def create_config_template(config_path):
    """创建config.ini模板文件"""
    config = configparser.ConfigParser()
    config['Settings'] = {
        'headless': 'false',
        'course_url': 'https://在此填写你的课程URL',
        'cookie': '在此填写你的sessionid',
        'implicitly_wait': '10'
    }

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write('; YuketangAutoPlayer 配置文件\n')
            f.write('; headless: 是否无窗口运行 (true/false)，首次使用建议false\n')
            f.write('; course_url: 你的课程地址，必须包含 https:// 协议头\n')
            f.write(';             例如: https://www.yuketang.cn/v2/web/studentLog/12345678\n')
            f.write('; cookie: 你的sessionid值，获取方式见README.md\n')
            f.write('; implicitly_wait: 元素查找超时时间(秒)，一般不需要修改\n\n')
            config.write(f)
    except Exception as e:
        print(f'创建配置文件失败: {e}')


def load_config():
    """从config.ini加载配置"""
    config = configparser.ConfigParser()

    # 优先从可执行文件所在目录查找config.ini（支持打包后的exe）
    config_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'config.ini')

    if not os.path.exists(config_path):
        # 如果exe目录没有，尝试从当前工作目录查找
        config_path = os.path.join(os.getcwd(), 'config.ini')

    if not os.path.exists(config_path):
        # 如果config.ini不存在，创建模板
        print(f'未找到配置文件，正在创建模板: {config_path}')
        create_config_template(config_path)
        print('\n已创建配置模板，接下来可直接在终端输入 course_url 和 cookie')

    try:
        config.read(config_path, encoding='utf-8')
        print(f'成功加载配置文件: {config_path}')
        return config, config_path
    except Exception as e:
        print(f'读取配置文件失败: {e}')
        input('按回车键退出...')
        sys.exit(1)


def save_config(config, config_path):
    """保存配置到config.ini"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
    except Exception as e:
        print(f'写入配置文件失败: {e}')
        input('按回车键退出...')
        sys.exit(1)


def is_valid_course_url(course_url):
    return bool(course_url) and '在此填写' not in course_url and course_url.startswith('https://')


def is_valid_cookie(cookie):
    return bool(cookie) and '在此填写' not in cookie


def prompt_course_url_and_cookie(config, config_path):
    """在终端输入course_url和cookie，并写回配置文件"""
    if not config.has_section('Settings'):
        config.add_section('Settings')

    print('\n你可以直接在终端输入课程地址和cookie（回车可保留当前值）')
    while True:
        current_course_url = config.get('Settings', 'course_url', fallback='').strip()
        current_cookie = config.get('Settings', 'cookie', fallback='').strip()

        course_status = current_course_url if is_valid_course_url(current_course_url) else '未配置'
        cookie_status = '已配置' if is_valid_cookie(current_cookie) else '未配置'
        print(f'当前 course_url: {course_status}')
        print(f'当前 cookie: {cookie_status}')

        input_course_url = input('请输入 course_url（https://...）: ').strip()
        input_cookie = input('请输入 cookie（sessionid）: ').strip()

        is_updated = False
        if input_course_url:
            config.set('Settings', 'course_url', input_course_url)
            is_updated = True
        if input_cookie:
            config.set('Settings', 'cookie', input_cookie)
            is_updated = True

        final_course_url = config.get('Settings', 'course_url', fallback='').strip()
        final_cookie = config.get('Settings', 'cookie', fallback='').strip()

        if not is_valid_course_url(final_course_url):
            print('\n错误: course_url 无效，必须以 https:// 开头')
            continue
        if not is_valid_cookie(final_cookie):
            print('\n错误: cookie 不能为空')
            continue

        if is_updated:
            save_config(config, config_path)
            print('已将输入内容写入 config.ini')
        return final_course_url, final_cookie


# 加载配置
print('='*50)
print('YuketangAutoPlayer - 雨课堂视频自动播放器')
print('='*50)

config, config_path = load_config()

# 读取配置项
try:
    IF_HEADLESS = config.getboolean('Settings', 'headless', fallback=False)
    IMPLICITLY_WAIT = config.getint('Settings', 'implicitly_wait', fallback=10)
except Exception as e:
    print(f'\n配置文件格式错误: {e}')
    input('按回车键退出...')
    sys.exit(1)

COURSE_URL, COOKIE = prompt_course_url_and_cookie(config, config_path)

print(f'\n配置信息:')
print(f'  无窗口模式: {IF_HEADLESS}')
print(f'  课程URL: {COURSE_URL[:50]}...' if len(COURSE_URL) > 50 else f'  课程URL: {COURSE_URL}')
print(f'  Cookie已配置: ✓')
print('='*50 + '\n')


option = webdriver.ChromeOptions()

if IF_HEADLESS:
    option.add_argument('--headless')

driver = webdriver.Chrome(options=option)
driver.maximize_window()
driver.implicitly_wait(IMPLICITLY_WAIT)
IS_COMMONUI = False

def str2dic(s):
    d = dict()
    for i in s.split('; '):
        temp = i.split('=')
        d[temp[0]] = temp[1]
    return d


def setCookie(cookies):
    driver.delete_all_cookies()
    for name, value in cookies.items():
        driver.add_cookie({'name': name, 'value': value, 'path': '/'})


def ifVideo(div: WebElement):
    for i in div.find_elements(By.TAG_NAME, 'i'):
        i_class = i.get_attribute('class')
        if 'icon--suo' in i_class:  # 锁的图标，表明视频未开放
            return False
    
    if IS_COMMONUI:  # www.yuketang.cn，非grsbupt.yuketang.cn，属新版ui
        try:
            span = div.find_element(By.CSS_SELECTOR, 'span.leaf-flag')
        except:
            return False
        return '视频' in span.text.strip()
    
    try:
        i = div.find_element(By.TAG_NAME, 'i')
    except:
        return False  # 每个小结后面都存在空行<li>
    i_class = i.get_attribute('class')
    return 'icon--shipin' in i_class


def getAllvideos_notFinished(allClasses: List[WebElement]):
    driver.implicitly_wait(0.1)  # 找不到元素时会找满implicitly_wait秒
    allVideos = []
    for thisClass in allClasses:
        if ifVideo(thisClass) and '已完成' not in thisClass.text and '截止' not in thisClass.text:
            print(f'找到未完成的视频: {thisClass.text.strip()}')
            allVideos.append(thisClass)
    driver.implicitly_wait(IMPLICITLY_WAIT)
    return allVideos


def get1video_notFinished(allClasses: List[WebElement]):
    for thisClass in allClasses:
        if ifVideo(thisClass) and '已完成' not in thisClass.text and '截止' not in thisClass.text:
            return thisClass
    return None


homePageURL = 'https://' + COURSE_URL.split('https://')[1].split('/')[0] + '/'
if 'www.yuketang.cn' in homePageURL:
    IS_COMMONUI = True
# driver.get('https://grsbupt.yuketang.cn/')
driver.get(homePageURL)
setCookie({'sessionid': COOKIE})
driver.get(COURSE_URL)
sleep(3)
if 'pro/portal/home' in driver.current_url:
    print('cookie失效或设置有误，请重设cookie或选择每次扫码登录')
    driver.get(homePageURL)
    driver.find_element(By.CLASS_NAME, 'login-btn').click()
    print("请扫码登录")
    while 'courselist' not in driver.current_url:  # 判断是否已经登录成功
        sleep(0.5)
    print('登录成功')
    driver.get(COURSE_URL)


def change2speed2():
    speedbutton = driver.find_element(By.TAG_NAME, 'xt-speedbutton')
    ActionChains(driver).move_to_element(speedbutton).perform()
    ul = speedbutton.find_element(By.TAG_NAME, 'ul')
    lis = ul.find_elements(By.TAG_NAME, 'li')
    li_speed2 = lis[0]
    diffY = speedbutton.location['y'] - li_speed2.location['y']
    # ActionChains(driver).move_to_element_with_offset(speedbutton, 3, 5).perform()
    # ActionChains(driver).click().perform()
    # 我也不知道为啥要一点一点移动上去，反正直接移动上去的话，点击是无效的
    for i in range(diffY // 10):  # 可能不是一个好算法
        ActionChains(driver).move_by_offset(0, -10).perform()
        sleep(0.5)
    sleep(0.8)
    ActionChains(driver).click().perform()


def mute1video():
    if driver.execute_script('return video.muted;'):
        return
    voice = driver.find_element(By.TAG_NAME, 'xt-volumebutton')
    ActionChains(driver).move_to_element(voice).perform()
    ActionChains(driver).click().perform()


def finish1video():
    if IS_COMMONUI:
        # TODO: WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "xxx")))
        # then remove the sleep before calling function finish1video
        # todo中改动较大需测试面较广，先用sleep代替
        scoreList = driver.find_element(By.ID, 'tab-student_school_report')
        scoreList.click()
        allClasses = driver.find_elements(By.CLASS_NAME, 'study-unit')
    else:
        allClasses = driver.find_elements(By.CLASS_NAME, 'leaf-detail')
    print('正在寻找未完成的视频，请耐心等待')
    allVideos = getAllvideos_notFinished(allClasses)
    if not allVideos:
        return False
    video = allVideos[0]
    driver.execute_script('arguments[0].scrollIntoView(false);', video)
    if IS_COMMONUI:
        span = video.find_element(By.TAG_NAME, 'span')
        span.click()
    else:
        video.click()
    print('正在播放')
    driver.switch_to.window(driver.window_handles[-1])
    WebDriverWait(driver, 10).until(lambda x: driver.execute_script('video = document.querySelector("video"); console.log(video); return video;'))  # 这里即使2次sleep3s选中的video还是null
    driver.execute_script('videoPlay = setInterval(function() {if (video.paused) {video.play();}}, 200);')
    driver.execute_script('setTimeout(() => clearInterval(videoPlay), 5000)')
    driver.execute_script('addFinishMark = function() {finished = document.createElement("span"); finished.setAttribute("id", "LetMeFly_Finished"); document.body.appendChild(finished); console.log("Finished");}')
    driver.execute_script('lastDuration = 0; setInterval(() => {nowDuration = video.currentTime; if (nowDuration < lastDuration) {addFinishMark()}; lastDuration = nowDuration}, 200)')
    driver.execute_script('video.addEventListener("pause", () => {video.play()})')
    mute1video()
    change2speed2()
    while True:
        if driver.execute_script('return document.querySelector("#LetMeFly_Finished");'):
            print('finished, wait 5s')
            sleep(5)  # 再让它播5秒
            driver.close()
            driver.switch_to.window(driver.window_handles[-1])
            return True
        else:
            print(f'正在播放视频 | not finished yet | 随机数: {random.random()}')
            sleep(3)
    return False


while finish1video():
    driver.refresh()
    sleep(5)  # thanks for @420xincheng's #8
driver.quit()
print('恭喜你！全部播放完毕')
sleep(5)
