import time
import re
import random
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from utils.logger import logger
from utils.user_agents import get_random_ua
import os

os.environ['WDM_LOG_LEVEL'] = '0'

class SeleniumDetailCrawler:
    def __init__(self):
        self.driver = None
        self.init_driver()

    def init_driver(self):
        """初始化浏览器驱动（强化反爬 + 稳定加载）"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        try:
            opts = Options()
            opts.add_argument("--headless=new")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            
            # 屏蔽自动化特征（关键修复）
            opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            opts.add_experimental_option('useAutomationExtension', False)
            
            # 随机UA + 模拟正常浏览器指纹
            opts.add_argument(f"user-agent={get_random_ua()}")
            opts.add_argument("--lang=zh-CN")
            opts.add_argument("--window-size=1920,1080")
            
            # 提速：不加载图片、视频、不必要样式
            opts.add_argument("--disable-images")
            opts.add_argument("--disable-media-source")
            opts.add_argument("--disable-extensions")
            
            # 加载策略：只等DOM，不等资源（大幅减少超时）
            opts.page_load_strategy = 'eager'
            
            # 启动驱动
            self.driver = webdriver.Edge(options=opts)
            self.driver.set_page_load_timeout(50)    # 延长超时，避免豆瓣慢加载
            self.driver.set_script_timeout(30)
            
            # 终极隐藏 webdriver
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
                    window.navigator.chrome = {runtime: {}};
                """
            })
            
            logger.info("Selenium 初始化成功")
        except WebDriverException as e:
            logger.error(f"Selenium初始化失败：{e}")
            raise e

    def _dynamic_wait(self, min_sec=2, max_sec=4):
        """智能随机等待（更像真人）"""
        sleep_time = random.uniform(min_sec, max_sec)
        time.sleep(sleep_time)

    def crawl_detail(self, url):
        """爬取详情页（强化重试、延时、抗反爬）"""
        ret = {"year": "", "runtime": "", "imdb": "", "comments": []}
        if not url:
            logger.warning("详情页URL为空")
            return ret

        # 增加重试次数 + 每次重试延长等待（解决豆瓣间歇性封锁）
        retry_count = 4
        for attempt in range(retry_count + 1):
            try:
                # 访问前强制等待，降低请求频率
                self._dynamic_wait(2, 4)
                
                # 访问页面
                self.driver.get(url)
                self._dynamic_wait(2, 4)

                # 等待核心信息区
                info_elem = WebDriverWait(self.driver, 25).until(
                    EC.presence_of_element_located((By.ID, "info"))
                )
                info_text = info_elem.text.strip()

                # 解析年份
                year_match = re.search(r'(\d{4})', info_text)
                if year_match:
                    ret["year"] = year_match.group(1)
                
                # 解析片长
                runtime_match = re.search(r'(\d+)\s*分钟', info_text)
                if runtime_match:
                    ret["runtime"] = f"{runtime_match.group(1)}分钟"
                
                # 解析IMDb
                imdb_match = re.search(r'IMDb:\s*(\S+)', info_text, re.IGNORECASE)
                if imdb_match:
                    ret["imdb"] = imdb_match.group(1)

                # 处理短评
                current_url = self.driver.current_url
                try:
                    more_btn = WebDriverWait(self.driver, 12).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'更多短评')]"))
                    )
                    self.driver.get(more_btn.get_attribute("href"))
                    self._dynamic_wait(2, 3.5)
                    
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "comment-item"))
                    )
                except:
                    logger.warning("未找到更多短评，使用默认短评")
                    if self.driver.current_url != current_url:
                        self.driver.get(current_url)
                        self._dynamic_wait(2, 3)

                # 提取评论
                try:
                    comments = self.driver.find_elements(By.CLASS_NAME, "comment-item")
                    logger.info(f"找到 {len(comments)} 条短评")
                    for item in comments[:15]:
                        try:
                            username = item.find_element(By.CSS_SELECTOR, ".comment-info a").text.strip()
                            content = item.find_element(By.CLASS_NAME, "short").text.strip()
                            c_time = item.find_element(By.CLASS_NAME, "comment-time").text.strip()
                            
                            try:
                                rating = item.find_element(By.CLASS_NAME, "rating").get_attribute("title")
                            except:
                                rating = "无评分"
                            
                            if content:
                                ret["comments"].append({
                                    "username": username,
                                    "rating": rating,
                                    "content": content,
                                    "time": c_time
                                })
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"评论提取失败：{e}")

                logger.info(f"✅ 详情页爬取成功：{url} | 评论数：{len(ret['comments'])}")
                return ret

            # 超时处理：重启驱动 + 更长等待
            except TimeoutException:
                logger.warning(f"⏳ 详情页加载超时（第{attempt+1}次）：{url}")
                if attempt < retry_count:
                    self.init_driver()  # 超时直接重启浏览器
                    self._dynamic_wait(6, 10)  # 超久等待，避开反爬
                    continue
                else:
                    return ret

            # 驱动异常：强制重启
            except WebDriverException as e:
                logger.error(f"⚠️ 驱动异常（第{attempt+1}次）：{e}")
                if attempt < retry_count:
                    self.init_driver()
                    self._dynamic_wait(5, 8)
                    continue
                else:
                    return ret

            # 未知错误：重试
            except Exception as e:
                logger.warning(f"⚠️ 爬取失败（第{attempt+1}次）：{str(e)[:50]}")
                if attempt < retry_count:
                    self._dynamic_wait(4, 7)
                    continue
                else:
                    return ret

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium 已安全关闭")
            except:
                pass
            self.driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()