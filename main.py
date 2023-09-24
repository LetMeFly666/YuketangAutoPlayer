'''
Author: LetMeFly
Date: 2023-09-12 20:49:21
LastEditors: LetMeFly
LastEditTime: 2023-09-24 16:05:10
Description: 开源于https://github.com/LetMeFly666/YuketangAutoPlayer 欢迎issue、PR
'''
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
import random


IF_HEADLESS = False  # 是否以无窗口模式运行（首次运行建议使用有窗口模式以观察是否符合预期）
COURSE_URL = 'https://grsbupt.yuketang.cn/pro/lms/84eubUXLHEy/17556639/studycontent'  # 要刷的课的地址（获取方式见README）
COOKIE = 'sjfeij2983uyfh84y7498uf98ys8f8u9'  # 打死也不要告诉别人哦（获取方式见README）


option = webdriver.ChromeOptions()

if IF_HEADLESS:
    option.add_argument('--headless')

driver = webdriver.Chrome(options=option)
driver.maximize_window()
driver.implicitly_wait(20)

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


def ifVideo(div):
    i = div.find_element_by_tag_name('i')
    i_class = i.get_attribute('class')
    return 'icon--shipin' in i_class


def getAllvideos_notFinished(allClasses):
    allVideos = []
    for thisClass in allClasses:
        if ifVideo(thisClass) and '已完成' not in thisClass.text:
            allVideos.append(thisClass)
    return allVideos


def get1video_notFinished(allClasses):
    for thisClass in allClasses:
        if ifVideo(thisClass) and '已完成' not in thisClass.text:
            return thisClass
    return None


homePageURL = 'https://' + COURSE_URL.split('https://')[1].split('/')[0] + '/'
# driver.get('https://grsbupt.yuketang.cn/')
driver.get(homePageURL)
setCookie({'sessionid': COOKIE})
driver.get(COURSE_URL)
sleep(3)
if 'pro/portal/home' in driver.current_url:
    print('cookie失效或设置有误，请重设cookie或选择每次扫码登录')
    driver.get(homePageURL)
    driver.find_element_by_class_name("login-btn").click()
    print("请扫码登陆")
    while 'courselist' not in driver.current_url:  # 判断是否已经登陆成功
        sleep(0.5)
    print('登录成功')
    driver.get(COURSE_URL)


def change2speed2():
    speedbutton = driver.find_element_by_tag_name('xt-speedbutton')
    ActionChains(driver).move_to_element(speedbutton).perform()
    ul = speedbutton.find_element_by_tag_name('ul')
    lis = ul.find_elements_by_tag_name('li')
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
    voice = driver.find_element_by_tag_name('xt-volumebutton')
    ActionChains(driver).move_to_element(voice).perform()
    ActionChains(driver).click().perform()


def finish1video():
    allClasses = driver.find_elements_by_class_name('leaf-detail')
    allVideos = getAllvideos_notFinished(allClasses)
    if not allVideos:
        return False
    video = allVideos[0]
    driver.execute_script('arguments[0].scrollIntoView(false);', video)
    video.click()

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
            print(f'not finished {random.random()}')
            sleep(3)
    return False


while finish1video():
    driver.refresh()
driver.quit()
print('恭喜你！全部播放完毕')
sleep(5)