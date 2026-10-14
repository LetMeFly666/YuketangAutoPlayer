"""任务发现和任务处理。

雨课堂不同页面使用了不同的 DOM：课程内容页通常是 ``leaf-detail``，
“未完成”页则使用 ``unfinished-study__item``。本模块把这两种 DOM
统一成 CourseTask，再由工厂选择具体处理器。
"""

from dataclasses import dataclass
from random import random
from time import sleep
from typing import List, Optional, Set

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait


UNFINISHED_ITEM_SELECTOR = "li.unfinished-study__item"
UNFINISHED_TYPE_SELECTOR = ".unfinished-study__type-text"
UNFINISHED_TITLE_SELECTOR = ".unfinished-study__item-title.el-popover__reference"


@dataclass
class CourseTask:
    """课程列表中的一个可执行任务。"""

    element: WebElement
    task_type: str
    title: str
    status: str
    source: str

    @property
    def is_pending(self) -> bool:
        if self.source != "unfinished" and "截止" in self.status:
            return False
        if self.source == "unfinished":
            # 该列表本身就是未完成列表；保留状态判断以兼容异步更新。
            return "已完成" not in self.status and "已读" not in self.status
        if self.task_type == "视频":
            return "已完成" not in self.status and "截止" not in self.status
        if self.task_type == "图文":
            return "已读" not in self.status and "已完成" not in self.status
        return False

    def click_target(self) -> WebElement:
        if self.source == "unfinished":
            return self.element.find_element(
                By.CSS_SELECTOR, UNFINISHED_TITLE_SELECTOR
            )
        if self.source == "common":
            return self.element.find_element(By.TAG_NAME, "span")
        return self.element


class TaskScanner:
    """把页面上的不同任务 DOM 转成 CourseTask。"""

    def __init__(self, driver, is_common_ui: bool = False):
        self.driver = driver
        self.is_common_ui = is_common_ui

    def scan(self) -> List[CourseTask]:
        unfinished = self.driver.find_elements(
            By.CSS_SELECTOR, UNFINISHED_ITEM_SELECTOR
        )
        visible_unfinished = [item for item in unfinished if item.is_displayed()]
        if visible_unfinished:
            return [self._from_unfinished(item) for item in visible_unfinished]

        # 课程页默认停留在“学习内容”时，未完成任务会在另一个 tab 中。
        # 优先切到该 tab，这样可以使用更稳定的 unfinished-study__item DOM。
        unfinished_tabs = self.driver.find_elements(
            By.CSS_SELECTOR, ".rain-tabs__nav-item-text"
        )
        unfinished_tab = next(
            (tab for tab in unfinished_tabs if tab.text.strip() == "未完成"),
            None,
        )
        if unfinished_tab:
            parent = unfinished_tab.find_element(By.XPATH, "..")
            parent_class = parent.get_attribute("class") or ""
            if "active" not in parent_class:
                self.driver.execute_script(
                    "arguments[0].click();", unfinished_tab
                )
                sleep(1)
            unfinished = self.driver.find_elements(
                By.CSS_SELECTOR, UNFINISHED_ITEM_SELECTOR
            )
            visible_unfinished = [
                item for item in unfinished if item.is_displayed()
            ]
            if visible_unfinished:
                return [
                    self._from_unfinished(item) for item in visible_unfinished
                ]

        # 兼容仓库原来支持的两种课程内容页。
        if self.is_common_ui:
            score_list = self.driver.find_elements(
                By.ID, "tab-student_school_report"
            )
            if score_list:
                score_list[0].click()
        selector = "study-unit" if self.is_common_ui else "leaf-detail"
        source = "common" if self.is_common_ui else "legacy"
        elements = self.driver.find_elements(By.CLASS_NAME, selector)
        return [
            task
            for task in (self._from_content(element, source) for element in elements)
            if task is not None
        ]

    def find_by_title(self, title: str) -> Optional[CourseTask]:
        for task in self.scan():
            if task.title == title:
                return task
        return None

    def _from_unfinished(self, element: WebElement) -> CourseTask:
        type_text = element.find_element(
            By.CSS_SELECTOR, UNFINISHED_TYPE_SELECTOR
        ).text.strip()
        title = element.find_element(
            By.CSS_SELECTOR, UNFINISHED_TITLE_SELECTOR
        ).text.strip()
        task_type = self._normalize_type(type_text)
        return CourseTask(element, task_type, title, element.text, "unfinished")

    def _from_content(
        self, element: WebElement, source: str
    ) -> Optional[CourseTask]:
        icon_classes = " ".join(
            (icon.get_attribute("class") or "")
            for icon in element.find_elements(By.TAG_NAME, "i")
        )
        if "icon--suo" in icon_classes:
            return None
        if "icon--shipin" in icon_classes:
            task_type = "视频"
        elif "icon--tuwen" in icon_classes:
            task_type = "图文"
        else:
            # common UI 的部分版本不使用 icon--shipin，而是把类型写在
            # span.leaf-flag 中。
            leaf_flags = element.find_elements(By.CSS_SELECTOR, "span.leaf-flag")
            flag_text = " ".join(flag.text.strip() for flag in leaf_flags)
            if "视频" in flag_text:
                task_type = "视频"
            elif "图文" in flag_text:
                task_type = "图文"
            else:
                return None

        title = ""
        for selector in (".title", ".leaf-title"):
            title_elements = element.find_elements(By.CSS_SELECTOR, selector)
            if title_elements:
                title = title_elements[0].text.strip()
                break
        return CourseTask(element, task_type, title, element.text, source)

    @staticmethod
    def _normalize_type(type_text: str) -> str:
        if "视频" in type_text:
            return "视频"
        if "图文" in type_text:
            return "图文"
        return type_text


class TaskHandler:
    """任务处理器基类。"""

    task_type = ""

    def __init__(self, driver):
        self.driver = driver

    def execute(self, task: CourseTask) -> bool:
        raise NotImplementedError

    def _click(self, task: CourseTask) -> None:
        target = task.click_target()
        self.driver.execute_script(
            'arguments[0].scrollIntoView({block: "center"});', target
        )
        try:
            target.click()
        except Exception:
            # Vue 的点击事件有时挂在父节点上，JS click 是 Selenium 点击失败时
            # 的兼容兜底，不作为首选路径。
            self.driver.execute_script("arguments[0].click();", target)

    def _open_context(self, task: CourseTask):
        original_handle = self.driver.current_window_handle
        handles_before = set(self.driver.window_handles)
        url_before = self.driver.current_url
        self._click(task)
        sleep(1)
        new_handles = set(self.driver.window_handles) - handles_before
        if new_handles:
            new_handle = next(iter(new_handles))
            self.driver.switch_to.window(new_handle)
        return original_handle, handles_before, url_before, new_handles

    def _close_context(
        self,
        original_handle: str,
        handles_before: Set[str],
        url_before: str,
        new_handles: Set[str],
    ) -> None:
        if new_handles and self.driver.current_window_handle not in handles_before:
            self.driver.close()
            self.driver.switch_to.window(original_handle)
            return

        # 图文有些版本使用当前窗口路由跳转，返回列表页等价于关闭详情页。
        if self.driver.current_url != url_before:
            self.driver.back()
            sleep(1)
        else:
            # 如果详情是同 URL 的弹层，ESC 可以关闭它；失败也不影响后续刷新。
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass


class GraphicTextTaskHandler(TaskHandler):
    """图文任务：打开、停留一段时间、关闭/返回。"""

    task_type = "图文"

    def __init__(self, driver, wait_seconds: int = 5):
        super().__init__(driver)
        self.wait_seconds = max(1, wait_seconds)

    def execute(self, task: CourseTask) -> bool:
        print(f"找到未完成的图文: {task.title}")
        original_handle, handles_before, url_before, new_handles = (
            self._open_context(task)
        )
        try:
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script(
                    "return document.readyState"
                )
                in ("interactive", "complete")
            )
        except Exception:
            # 某些 SPA 不重新触发 readyState，仍按用户确认的规则继续计时。
            pass
        print(f"正在阅读图文，等待 {self.wait_seconds} 秒")
        sleep(self.wait_seconds)
        self._close_context(
            original_handle, handles_before, url_before, new_handles
        )
        print(f"图文任务已处理: {task.title}")
        return True


class VideoTaskHandler(TaskHandler):
    """保留原脚本的视频播放行为，同时复用统一的点击和窗口处理。"""

    task_type = "视频"

    def execute(self, task: CourseTask) -> bool:
        print(f"找到未完成的视频: {task.title}")
        original_handle, handles_before, url_before, new_handles = (
            self._open_context(task)
        )
        print("正在播放")
        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.execute_script(
                'window.currentVideo = document.querySelector("video"); '
                "return window.currentVideo;"
            )
        )
        self.driver.execute_script(
            "window.videoPlay = setInterval(function() {"
            "if (window.currentVideo && window.currentVideo.paused) "
            "{window.currentVideo.play();}}, 200);"
        )
        self.driver.execute_script(
            "setTimeout(() => clearInterval(window.videoPlay), 5000)"
        )
        self.driver.execute_script(
            "window.addFinishMark = function() {"
            "var finished = document.createElement('span');"
            "finished.setAttribute('id', 'LetMeFly_Finished');"
            "document.body.appendChild(finished);};"
        )
        self.driver.execute_script(
            "window.lastDuration = 0; window.videoCheck = setInterval(() => {"
            "var nowDuration = window.currentVideo.currentTime;"
            "if (nowDuration < window.lastDuration) {window.addFinishMark();}"
            "window.lastDuration = nowDuration;}, 200);"
        )
        self.driver.execute_script(
            "window.currentVideo.addEventListener('pause', () => "
            "window.currentVideo.play());"
        )
        self._mute()
        self._change_speed()
        while True:
            if self.driver.execute_script(
                "return document.querySelector('#LetMeFly_Finished');"
            ):
                print("视频播放完成，等待 5 秒")
                sleep(5)
                self._close_context(
                    original_handle, handles_before, url_before, new_handles
                )
                return True
            print(f"正在播放视频 | 尚未完成 | 随机数: {random()}")
            sleep(3)

    def _mute(self) -> None:
        if self.driver.execute_script("return window.currentVideo.muted;"):
            return
        voice = self.driver.find_element(By.TAG_NAME, "xt-volumebutton")
        ActionChains(self.driver).move_to_element(voice).click().perform()

    def _change_speed(self) -> None:
        """尽力切换到 2 倍速，不依赖固定的鼠标偏移坐标。

        旧实现通过 ``move_by_offset`` 一次移动 10 像素，依赖 WebDriver
        当前保存的鼠标坐标。窗口尺寸、页面滚动或播放器位置变化时，
        这个坐标可能落到视口外，从而抛出
        ``MoveTargetOutOfBoundsException``。直接点击菜单项不需要计算
        坐标；倍速不是视频完成条件，因此控件不可用时跳过即可。
        """
        try:
            speed_button = self.driver.find_element(By.TAG_NAME, "xt-speedbutton")
            speed_items = speed_button.find_element(By.TAG_NAME, "ul").find_elements(
                By.TAG_NAME, "li"
            )
        except (NoSuchElementException, WebDriverException):
            print("未找到倍速控件，保持默认播放速度")
            return

        if not speed_items:
            return

        # 旧版播放器第一个选项就是 2 倍速；优先按文本匹配，避免
        # 新版调整菜单顺序后误点到其他速度。
        speed_item = next(
            (item for item in speed_items if "2" in item.text or "二" in item.text),
            speed_items[0],
        )
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                speed_button,
            )
            # 先悬停打开自定义菜单；这里不再使用相对坐标移动。
            ActionChains(self.driver).move_to_element(speed_button).perform()
            sleep(0.3)
            speed_item.click()
        except (ElementClickInterceptedException, WebDriverException):
            # 菜单可能被播放器浮层遮挡，Selenium 的普通 click 会失败。
            # JS click 仍会触发菜单绑定的 click 事件，且不依赖鼠标坐标。
            try:
                self.driver.execute_script("arguments[0].click();", speed_item)
            except WebDriverException:
                print("切换倍速失败，保持默认播放速度")


class TaskHandlerFactory:
    """根据任务类型创建处理器。"""

    def __init__(self, driver, graphic_text_wait: int = 5):
        self.driver = driver
        self.graphic_text_wait = graphic_text_wait

    def create(self, task_type: str) -> Optional[TaskHandler]:
        if task_type == "视频":
            return VideoTaskHandler(self.driver)
        if task_type == "图文":
            return GraphicTextTaskHandler(self.driver, self.graphic_text_wait)
        return None


class TaskRunner:
    """扫描任务并交给对应处理器执行。"""

    def __init__(
        self,
        driver,
        is_common_ui: bool = False,
        graphic_text_wait: int = 5,
    ):
        self.scanner = TaskScanner(driver, is_common_ui)
        self.factory = TaskHandlerFactory(driver, graphic_text_wait)
        # 部分页面在关闭图文详情后不会立即刷新列表状态。用户已确认“打开、
        # 等待、关闭”即可视为完成，因此同一运行中不重复处理该任务。
        self._processed_graphic_titles = set()

    def process_next(self) -> bool:
        tasks = self.scanner.scan()
        for task in tasks:
            if not task.is_pending:
                continue
            if (
                task.task_type == "图文"
                and task.title in self._processed_graphic_titles
            ):
                continue
            handler = self.factory.create(task.task_type)
            if handler is None:
                continue
            result = handler.execute(task)
            if task.task_type == "图文" and result:
                self._processed_graphic_titles.add(task.title)
                current = self.scanner.find_by_title(task.title)
                if current is None or not current.is_pending:
                    print(f"已确认图文状态更新: {task.title}")
                else:
                    print(
                        f"图文已打开并关闭，但列表状态尚未更新: {task.title}"
                    )
            return result
        return False
