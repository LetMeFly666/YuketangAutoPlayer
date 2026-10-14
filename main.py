'''
Author: LetMeFly, Guo-Chenxu, Crsuh2er0, 420xincheng, tkzzzzzz6
Date: 2023-09-12 20:49:21
LastEditors: LetMeFly.xyz
LastEditTime: 2025-11-13 22:44:00
Description: 开源于https://github.com/LetMeFly666/YuketangAutoPlayer 欢迎issue、PR
'''
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import os
import sys
import configparser

from task_handlers import TaskRunner


def create_config_template(config_path):
    """创建config.ini模板文件"""
    config = configparser.ConfigParser()
    config['Settings'] = {
        'headless': 'false',
        'course_url': 'https://在此填写你的课程URL',
        'cookie': '在此填写你的sessionid',
        'implicitly_wait': '10',
        'graphic_text_wait': '5'
    }

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write('; YuketangAutoPlayer 配置文件\n')
            f.write('; headless: 是否无窗口运行 (true/false)，首次使用建议false\n')
            f.write('; course_url: 你的课程地址，必须包含 https:// 协议头\n')
            f.write(';             例如: https://www.yuketang.cn/v2/web/studentLog/12345678\n')
            f.write('; cookie: 你的sessionid值，获取方式见README.md\n')
            f.write('; implicitly_wait: 元素查找超时时间(秒)，一般不需要修改\n\n')
            f.write('; graphic_text_wait: 图文任务打开后等待时间(秒)\n\n')
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
print('YuketangAutoPlayer - 雨课堂视频和图文自动播放器')
print('='*50)

config = load_config()

# 读取配置项
try:
    IF_HEADLESS = config.getboolean('Settings', 'headless', fallback=False)
    COURSE_URL = config.get('Settings', 'course_url', fallback='')
    COOKIE = config.get('Settings', 'cookie', fallback='')
    IMPLICITLY_WAIT = config.getint('Settings', 'implicitly_wait', fallback=10)
    GRAPHIC_TEXT_WAIT = config.getint('Settings', 'graphic_text_wait', fallback=5)
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

def setCookie(cookies):
    driver.delete_all_cookies()
    for name, value in cookies.items():
        driver.add_cookie({'name': name, 'value': value, 'path': '/'})

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


runner = TaskRunner(
    driver,
    is_common_ui=IS_COMMONUI,
    graphic_text_wait=GRAPHIC_TEXT_WAIT,
)

while runner.process_next():
    driver.refresh()
    sleep(5)  # thanks for @420xincheng's #8
driver.quit()
print('恭喜你！所有支持的任务处理完毕')
sleep(5)
