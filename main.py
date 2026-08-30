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
from selenium.webdriver.support import expected_conditions as EC
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
        print('\n请编辑 config.ini 文件填写你的配置信息后重新运行程序')
        input('按回车键退出...')
        sys.exit(0)

    try:
        config.read(config_path, encoding='utf-8')
        print(f'成功加载配置文件: {config_path}')
        return config
    except Exception as e:
        print(f'读取配置文件失败: {e}')
        input('按回车键退出...')
        sys.exit(1)


# 加载配置
print('='*50)
print('YuketangAutoPlayer - 雨课堂视频自动播放器')
print('='*50)

config = load_config()

# 读取配置项
try:
    IF_HEADLESS = config.getboolean('Settings', 'headless', fallback=False)
    COURSE_URL = config.get('Settings', 'course_url', fallback='')
    COOKIE = config.get('Settings', 'cookie', fallback='')
    IMPLICITLY_WAIT = config.getint('Settings', 'implicitly_wait', fallback=10)
except Exception as e:
    print(f'\n配置文件格式错误: {e}')
    input('按回车键退出...')
    sys.exit(1)

# 验证配置
if not COURSE_URL or not COOKIE or '在此填写' in COURSE_URL or '在此填写' in COOKIE:
    print('\n错误: 检测到配置文件未正确填写!')
    print('请编辑 config.ini 文件，填写正确的 course_url 和 cookie')
    input('按回车键退出...')
    sys.exit(1)

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
        scoreList = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'tab-student_school_report'))
        )
        driver.execute_script("arguments[0].click();", scoreList)
        sleep(2) 
        allClasses = driver.find_elements(By.CLASS_NAME, 'study-unit')
    else:
        allClasses = driver.find_elements(By.CLASS_NAME, 'leaf-detail')
        
    print('正在寻找未完成的视频，请耐心等待')
    allVideos = getAllvideos_notFinished(allClasses)
    if not allVideos:
        return False
        
    # 获取第一个未完成的视频
    current_video = allVideos[0]
    
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", current_video)
    sleep(1) 
    
    if IS_COMMONUI:
        span = current_video.find_element(By.TAG_NAME, 'span')
        driver.execute_script("arguments[0].click();", span)
    else:
        driver.execute_script("arguments[0].click();", current_video)
        
    print('正在播放')
    driver.switch_to.window(driver.window_handles[-1])
    
    # === 核心播放与注入逻辑 ===
    # 在当前页面及同源 iframe 中查找可播放的视频，并注册为全局变量 window.video
    find_video_script = """
    function collectVideos(doc, videos) {
        videos.push.apply(videos, Array.from(doc.querySelectorAll('video')));
        for (const iframe of doc.querySelectorAll('iframe')) {
            try {
                if (iframe.contentDocument) {
                    collectVideos(iframe.contentDocument, videos);
                }
            } catch (e) {
                // 跨域 iframe 无法读取，直接跳过
            }
        }
    }

    const videos = [];
    collectVideos(document, videos);
    const playableVideos = videos.filter(function(video) {
        return video.currentSrc || video.src || video.querySelector('source[src]');
    });
    const candidates = playableVideos.length ? playableVideos : videos;
    window.video = candidates.find(function(video) {
        return !video.paused && !video.ended;
    }) || candidates.find(function(video) {
        return !video.ended && video.readyState > 0;
    }) || candidates[0] || null;
    return window.video;
    """
    WebDriverWait(driver, 10).until(
        lambda x: driver.execute_script(find_video_script)
    )
    
    js_script = """
    // 1. 强制静音，绕过浏览器的自动播放限制
    window.video.muted = true;

    // 清理上一次注入的监听器和计时器，避免重复注册
    if (typeof window.cleanupVideoHandling === 'function') {
        window.cleanupVideoHandling();
    }
    
    // 2. 启动初始播放
    var p = window.video.play();
    if (p !== undefined) {
        p.catch(function(e) { console.log("播放拦截已忽略:", e); });
    }

    // 监听暂停事件并立即恢复播放，不覆盖原生 pause 方法
    window.videoResumeTarget = window.video;
    window.resumeVideo = function() {
        if (!window.videoResumeTarget || window.videoResumeTarget.ended ||
                !window.videoResumeTarget.paused) {
            return;
        }
        var resumePromise = window.videoResumeTarget.play();
        if (resumePromise !== undefined) {
            resumePromise.catch(function(e) { console.log("恢复播放失败:", e); });
        }
    };
    window.videoResumeHandler = window.resumeVideo;
    window.videoResumeTarget.addEventListener('pause', window.videoResumeHandler);
    
    // 3. 标记视频播放完毕
    window.addFinishMark = function() {
        if (!document.querySelector("#LetMeFly_Finished")) {
            var finished = document.createElement("span"); 
            finished.setAttribute("id", "LetMeFly_Finished"); 
            document.body.appendChild(finished); 
        }
    };
    
    window.cleanupVideoHandling = function() {
        if (window.videoCheckInterval) {
            clearInterval(window.videoCheckInterval);
            window.videoCheckInterval = null;
        }
        if (window.videoResumeTarget && window.videoResumeHandler) {
            window.videoResumeTarget.removeEventListener('pause', window.videoResumeHandler);
        }
        window.videoResumeTarget = null;
        window.videoResumeHandler = null;
        window.resumeVideo = null;
    };

    // 每秒恢复意外暂停，并根据视频总时长判断是否播放完毕
    window.videoCheckInterval = setInterval(function() {
        if (window.video.paused && !window.video.ended) {
            window.resumeVideo();
            var playerDocument = window.video.ownerDocument || document;
            var playBtn = playerDocument.querySelector('.xt_video_player_play_btn') ||
                playerDocument.querySelector('.play-btn') ||
                document.querySelector('.xt_video_player_play_btn') ||
                document.querySelector('.play-btn');
            if (playBtn) playBtn.click();
        }

        var duration = window.video.duration;
        var reachedEnd = Number.isFinite(duration) && duration > 0 &&
            window.video.currentTime >= duration - 1;
        if (window.video.ended || reachedEnd) {
            window.addFinishMark();
            window.cleanupVideoHandling();
        }
    }, 1000);
    """
    
    # 注入黑科技JS
    driver.execute_script(js_script)
    
    print('等待播放器 UI 加载...')
    sleep(3) 
    
    # 加上 try-except 保护，即使UI变化找不到按钮也不会崩溃
    try:
        mute1video()
    except Exception:
        pass
        
    try:
        change2speed2()
    except Exception as e:
        print(f"调节倍速失败，按原速播放...")

    # 循环检测是否播放完成
    while True:
        if driver.execute_script('return document.querySelector("#LetMeFly_Finished");'):
            print('finished, wait 5s')
            sleep(5)  # 再让它播5秒
            driver.execute_script('''
                if (typeof window.cleanupVideoHandling === 'function') {
                    window.cleanupVideoHandling();
                }
            ''')
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

