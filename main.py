'''
Author: LetMeFly
Date: 2021-11-01 15:52:32
LastEditors: LetMeFly
LastEditTime: 2023-09-12 19:27:08
'''

from selenium import webdriver
from time import sleep
driver = webdriver.Chrome()

# 访问雨课堂并点击“登录”按钮
driver.get("https://grsbupt.yuketang.cn/")
driver.find_element_by_class_name("login-btn").click()
print("请扫码登陆")

# 判断是否已经登陆成功
while True:
    location = driver.current_url
    if "courselist" in location:
        break
    sleep(0.5)
print("登录成功")

# 完成一门课程的函数
def finishThisCourse(courseId):
    # 访问此视频
    driver.get("https://grsbupt.yuketang.cn/pro/lms/84eubUXLHEy/17556639/video/" + courseId)
    # 判断是否已经完成
    sleep(3)
    if len(driver.find_elements_by_class_name("icon--gou")):
        print("此课程已完成")
        return True
    def ifCouldPlayAVideo():
        videoTag = driver.find_element_by_id("video-box")
        return len(videoTag.find_elements_by_tag_name("div"))
    couldPlayVideo = False
    for tryTimes in range(5): # 尝试5次，一次可能是因为网络，5次大概率不是视频
        if ifCouldPlayAVideo():
            couldPlayVideo = True
            print("是课程")
            break
        sleep(2)
    if not couldPlayVideo:
        print("不是课程")
        return False # 认为不是视频
    sleep(5)
    # video = driver.find_element_by_tag_name("video")
    # def ifVideoPaused():
    #     result = driver.execute_script("return document.querySelector('video').paused;")
    #     return result
    # tryToPlayTimes = 0
    # while ifVideoPaused():
    #     print("暂停状态")
    #     try:
    #         playButton = driver.find_element_by_class_name('xt_video_player_play_btn')
    #         playButton.click()
    #     except:
    #         driver.execute_script("document.querySelector('.xt_video_player_play_btn').click();")
    #         driver.execute_script("console.log(document.querySelector('.xt_video_player_play_btn'));")
    #         driver.execute_script("document.querySelector('video').play();")
    #     tryToPlayTimes += 1
    #     if tryToPlayTimes > 7:
    #         driver.refresh()
    #         tryToPlayTimes = 0
    #         # while True:
    #         #     try:
    #         #         script = input("请输入要执行的脚本")
    #         #         print(driver.execute_script(script))
    #         #     except:
    #         #         print("执行失败")
    #         sleep(3)
    #     sleep(1)

    driver.execute_script("video = document.querySelector('video');")
    element_video = driver.find_element_by_tag_name('video')
    webdriver.ActionChains(driver).move_to_element(element_video).perform()
    webdriver.ActionChains(driver).click().perform()
    driver.execute_script("startVideo = setInterval(() => {video.play(); console.log('尝试播放视频');}, 1000); setTimeout(() => {clearInterval(startVideo); console.log('停止尝试播放视频')}, 5200);")
    print("正在播放")
    driver.execute_script("video.addEventListener('pause', function() {video.play();});")
    sleep(5)
    element_speeds = driver.find_element_by_class_name('xt_video_player_common_value')
    webdriver.ActionChains(driver).move_to_element(element_speeds).perform()
    sleep(0.2)
    element_speed2 = driver.find_element_by_xpath('//*[@id="video-box"]/div/xt-wrap/xt-controls/xt-inner/xt-speedbutton/xt-speedlist/ul/li[1]')
    webdriver.ActionChains(driver).move_to_element_with_offset(element_speed2, 3, 5).perform()
    sleep(0.3)
    element_speed2.click()
    # webdriver.ActionChains(driver).context_click(element_speed2).perform()

    while not len(driver.find_elements_by_class_name("icon--gou")):
        sleep(1)
    print("此课程播放完毕！")
    return True
        

# 访问每一门课
for courseId in range(37551787, 37551907 + 1):
    # try:
    if True:
        finishThisCourse(str(courseId))
    # except:
    #     pass
print("全部完成！")



# 雨课堂字幕：https://buct.yuketang.cn/mooc-api/v1/lms/service/subtitle_parse/?c_d=0D0C4F3DE7D58B649C33DC5901307461&lg=0&_=1665473764724