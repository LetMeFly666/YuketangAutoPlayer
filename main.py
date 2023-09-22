'''
Author: LetMeFly
Date: 2021-11-01 15:52:32
LastEditors: LetMeFly
LastEditTime: 2022-10-11 15:47:47
'''

'''
PS F:\OtherApps\Program\VsCode\Code> & F:/OtherApps/Program/Python/Python/python.exe f:/OtherApps/Program/VsCode/Code/YuKeTang.py

DevTools listening on ws://127.0.0.1:59227/devtools/browser/1345bf1f-6b58-47d7-98cb-20e955bbe99a
请扫码登陆
[8224:6516:1102/113245.817:ERROR:chrome_browser_main_extra_parts_metrics.cc(230)] crbug.com/1216328: Checking Bluetooth availability started. Please report if there is no report that this ends.
[8224:21044:1102/113245.819:ERROR:device_event_log_impl.cc(214)] [11:32:45.820] USB: usb_device_handle_win.cc:1048 Failed to read descriptor from node connection: 连到系统上的设备没有发挥作用。 (0x1F)
[8224:6516:1102/113245.820:ERROR:chrome_browser_main_extra_parts_metrics.cc(233)] crbug.com/1216328: Checking Bluetooth availability ended.
[8224:6516:1102/113245.861:ERROR:chrome_browser_main_extra_parts_metrics.cc(236)] crbug.com/1216328: Checking default browser status started. Please report if there is no report that this ends.
[8224:6516:1102/113245.893:ERROR:chrome_browser_main_extra_parts_metrics.cc(240)] crbug.com/1216328: Checking default browser status ended.
登录成功
此课程已完成
此课程已完成
此课程已完成
不是课程
此课程已完成
不是课程
此课程已完成
不是课程
此课程已完成
此课程已完成
此课程已完成
不是课程
不是课程
此课程已完成
此课程已完成
此课程已完成
[12280:19080:1102/113441.896:ERROR:gpu_init.cc(453)] Passthrough is not supported, GL is disabled, ANGLE is 
不是课程
不是课程
此课程已完成
此课程已完成
此课程已完成
不是课程
不是课程
此课程已完成
此课程已完成
此课程已完成
不是课程
此课程已完成
此课程已完成
此课程已完成
不是课程
此课程已完成
此课程已完成
此课程已完成
不是课程
是课程
暂停状态
正在播放
此课程播放完毕！
此课程已完成
是课程
暂停状态
正在播放
此课程播放完毕！
不是课程
是课程
暂停状态
正在播放
此课程播放完毕！
是课程
暂停状态
正在播放
此课程播放完毕！
是课程
暂停状态
正在播放
此课程播放完毕！
不是课程
不是课程
全部完成！
'''

from selenium import webdriver
from time import sleep
driver = webdriver.Chrome()

# 访问雨课堂并点击“登录”按钮
driver.get("https://buct.yuketang.cn/")
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
    driver.get("https://buct.yuketang.cn/pro/lms/924ghA7XHG7/14295715/video/" + courseId)
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
    def ifVideoPaused():
        result = driver.execute_script("return document.querySelector('video').paused;")
        return result
    tryToPlayTimes = 0
    while ifVideoPaused():
        print("暂停状态")
        try:
            playButton = driver.find_element_by_class_name('xt_video_player_play_btn')
            playButton.click()
        except:
            driver.execute_script("document.querySelector('.xt_video_player_play_btn').click();")
            driver.execute_script("console.log(document.querySelector('.xt_video_player_play_btn'));")
            driver.execute_script("document.querySelector('video').play();")
        tryToPlayTimes += 1
        if tryToPlayTimes > 7:
            driver.refresh()
            tryToPlayTimes = 0
            # while True:
            #     try:
            #         script = input("请输入要执行的脚本")
            #         print(driver.execute_script(script))
            #     except:
            #         print("执行失败")
            sleep(3)
        sleep(1)
    print("正在播放")
    while not driver.execute_script("function ifFinished() {percent = document.querySelector('.xt_video_player_progress_currentTime');style = percent.getAttribute('style');return style=='width: 100%;'} return ifFinished();"):
            sleep(1)
    print("此课程播放完毕！")
    return True
        

# 访问每一门课
while True:
    try:
        for courseId in range(25534615, 25534718 + 1):
            finishThisCourse(str(courseId))
        print("全部完成！")
        break
    except:
        pass


# 雨课堂字幕：https://buct.yuketang.cn/mooc-api/v1/lms/service/subtitle_parse/?c_d=0D0C4F3DE7D58B649C33DC5901307461&lg=0&_=1665473764724