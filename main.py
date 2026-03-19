import sys
import os

# 允许 file 之间互相访问
os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = \
    "--allow-file-access-from-files --allow-universal-access-from-files"

import threading
import urllib.request
import ssl
import ctypes
from ctypes import wintypes
import json
import time
import random
import logging
import re
import http.server
import socketserver
import socket

# 配置日志
log_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'pikachu-music')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'download.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_screen_size():
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return width, height
    except:
        return 1920, 1080

def get_main_window_handle():
    try:
        return ctypes.windll.user32.FindWindowW(None, "皮卡丘的音乐站 - Pikachu Music")
    except:
        return 0

def show_message_box(text, title, style=0x40):
    try:
        hwnd = get_main_window_handle()
        style = style | 0x00040000 | 0x00010000
        ctypes.windll.user32.MessageBoxW(hwnd, text, title, style)
    except Exception as e:
        print(f"显示消息框失败: {e}")

def select_folder_win32(title="选择保存位置", initial_dir=None):
    try:
        import clr
        clr.AddReference('System.Windows.Forms')
        from System.Windows.Forms import FolderBrowserDialog, DialogResult
        
        dialog = FolderBrowserDialog()
        dialog.Description = title
        dialog.ShowNewFolderButton = True
        
        if initial_dir and os.path.exists(initial_dir):
            dialog.SelectedPath = initial_dir
        
        result = dialog.ShowDialog()
        
        if result == DialogResult.OK:
            return dialog.SelectedPath
        return None
    except Exception as e:
        print(f"Win32选择文件夹失败: {e}")
        return None

def select_folder(title="选择保存位置", initial_dir=None):
    return select_folder_win32(title, initial_dir)

def download_file(url, filename, download_dir, show_success=True):
    try:
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
        
        download_path = os.path.join(download_dir, filename)
        
        if os.path.exists(download_path):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(download_path):
                new_filename = f"{base} ({counter}){ext}"
                download_path = os.path.join(download_dir, new_filename)
                counter += 1
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
            with open(download_path, 'wb') as f:
                f.write(response.read())
        
        time.sleep(0.5)
        
        if show_success:
            show_message_box(
                f"下载完成！\n\n文件已保存到：\n{download_path}",
                "下载成功",
                0x40
            )
        return True
    except Exception as e:
        logging.error(f"下载失败：{str(e)}\nURL: {url}\n文件名: {filename}\n保存目录: {download_dir}")
        if show_success:
            show_message_box(
                f"下载失败：{str(e)}\n\n请尝试在浏览器中手动下载。",
                "下载错误",
                0x10
            )
        return False

def save_text_file(content, filename, save_dir):
    try:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        save_path = os.path.join(save_dir, filename)
        
        if os.path.exists(save_path):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(save_path):
                new_filename = f"{base} ({counter}){ext}"
                save_path = os.path.join(save_dir, new_filename)
                counter += 1
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        logging.error(f"保存文件失败: {str(e)}\n文件名: {filename}\n保存目录: {save_dir}")
        print(f"保存文件失败: {e}")
        return False

def check_update(url):
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        url_with_ts = url + '?t=' + str(int(time.time() * 1000))
        
        req = urllib.request.Request(url_with_ts, headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        })
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {'success': True, 'data': data}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def fetch_url(url):
    try:
        # 检查是否是文叔叔链接
        if 'wenshushu.cn' in url or 'wss.ink' in url or 'wss1.cn' in url:
            print(f"检测到文叔叔链接: {url}")
            # 调用wss模块的download功能
            import tempfile
            import os
            import importlib.util
            import sys
            import io
            from contextlib import redirect_stdout
            
            # 获取wss.py的路径
            wss_path = os.path.join(os.path.dirname(__file__), 'wss.py')
            print(f"wss.py路径: {wss_path}")
            
            # 创建模块规范
            spec = importlib.util.spec_from_file_location("wss", wss_path)
            if spec is None:
                raise Exception(f"无法创建wss模块规范: {wss_path}")
            
            # 创建模块
            wss_module = importlib.util.module_from_spec(spec)
            if wss_module is None:
                raise Exception("无法创建wss模块")
            
            # 添加到sys.modules
            sys.modules["wss"] = wss_module
            
            # 执行模块
            spec.loader.exec_module(wss_module)
            print("wss模块导入成功")
            
            # 创建临时文件保存下载的内容
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                temp_file_path = f.name
            
            print(f"创建临时文件: {temp_file_path}")
            
            try:
                # 创建requests会话并初始化
                import requests
                s = requests.Session()
                # 调用wss模块的login_anonymous函数获取token
                token = wss_module.login_anonymous(s)
                print(f"获取到token: {token[:20]}...")
                # 设置必要的头部
                s.headers['X-TOKEN'] = token
                s.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0"
                s.headers['Accept-Language'] = "en-US, en;q=0.9"
                
                # 将会话对象添加到wss模块的全局变量中
                wss_module.s = s
                
                # 捕获标准输出
                f_output = io.StringIO()
                with redirect_stdout(f_output):
                    # 调用download函数，传入临时文件路径
                    wss_module.download(url, output_path=temp_file_path)
                output = f_output.getvalue()
                print(f"wss.download()输出: {output}")
                
                # 读取下载的文件内容
                if os.path.exists(temp_file_path):
                    with open(temp_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"下载的文件大小: {len(content)} 字符")
                    print(f"下载的文件前100个字符: {content[:100]}...")
                    
                    # 检查文件是否为空
                    if not content:
                        print("下载的文件内容为空")
                        return {'success': False, 'error': '下载的文件内容为空'}
                    
                    # 尝试解析为JSON
                    try:
                        json_data = json.loads(content)
                        print("JSON解析成功")
                        return {'success': True, 'data': json_data, 'is_json': True}
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败: {e}")
                        print(f"文件内容: {content}")
                        return {'success': True, 'data': content, 'is_json': False}
                else:
                    raise Exception("下载的文件不存在")
            finally:
                # 删除临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    print(f"删除临时文件: {temp_file_path}")
        
        # 普通链接处理
        try:
            print(f"fetch_url: 处理普通链接: {url}")
        except Exception as e:
            print(f"fetch_url: 打印URL时出错: {e}")
        
        # 优先使用requests库，因为它更可靠
        try:
            import requests
            try:
                print(f"fetch_url: 使用requests库发起请求")
            except Exception as e:
                print(f"fetch_url: 打印请求方式时出错: {e}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            try:
                print(f"fetch_url: 请求头: {headers}")
            except Exception as e:
                print(f"fetch_url: 打印请求头时出错: {e}")
            
            response = requests.get(url, headers=headers, verify=False, timeout=15)
            
            try:
                print(f"fetch_url: 响应状态码: {response.status_code}")
            except Exception as e:
                print(f"fetch_url: 打印状态码时出错: {e}")
            
            try:
                print(f"fetch_url: 响应头: {dict(response.headers)}")
            except Exception as e:
                print(f"fetch_url: 打印响应头时出错: {e}")
            
            content = response.text
            try:
                print(f"fetch_url: 响应内容长度: {len(content)}")
            except Exception as e:
                print(f"fetch_url: 打印内容长度时出错: {e}")
            
            try:
                # 使用json.dumps处理非ASCII字符
                print(f"fetch_url: 响应内容前100字符: {json.dumps(content[:100], ensure_ascii=True)}...")
            except Exception as e:
                print(f"fetch_url: 打印响应内容时出错: {e}")
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    try:
                        print(f"fetch_url: JSON解析成功")
                    except Exception as e:
                        print(f"fetch_url: 打印JSON解析结果时出错: {e}")
                    return {'success': True, 'data': json_data, 'is_json': True}
                except json.JSONDecodeError:
                    try:
                        print(f"fetch_url: JSON解析失败，返回原始文本")
                    except Exception as e:
                        print(f"fetch_url: 打印JSON解析失败信息时出错: {e}")
                    return {'success': True, 'data': content, 'is_json': False}
            else:
                try:
                    print(f"fetch_url: 请求失败，状态码: {response.status_code}")
                except Exception as e:
                    print(f"fetch_url: 打印请求失败信息时出错: {e}")
                return {'success': True, 'data': {'code': response.status_code, 'data': None}, 'is_json': True}
                
        except ImportError:
            try:
                print(f"fetch_url: requests库不可用，使用urllib")
            except Exception as e:
                print(f"fetch_url: 打印库信息时出错: {e}")
            # 如果没有requests库，使用urllib
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/html, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            })
            
            # 增加重试机制，最多尝试2次
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    try:
                        print(f"fetch_url: 尝试第 {attempt + 1} 次请求")
                    except Exception as e:
                        print(f"fetch_url: 打印尝试次数时出错: {e}")
                    with urllib.request.urlopen(req, context=ssl_context, timeout=15) as response:
                        content = response.read().decode('utf-8')
                        content_type = response.headers.get('Content-Type', '')
                        
                        if 'application/json' in content_type:
                            return {'success': True, 'data': json.loads(content), 'is_json': True}
                        else:
                            return {'success': True, 'data': content, 'is_json': False}
                except TimeoutError:
                    try:
                        print(f"fetch_url: 第 {attempt + 1} 次请求超时，{'重试中...' if attempt < max_retries - 1 else '放弃'}")
                    except Exception as e:
                        print(f"fetch_url: 打印超时信息时出错: {e}")
                    if attempt == max_retries - 1:
                        raise
    except Exception as e:
        print(f"fetch_url失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def force_kill_process():
    try:
        os._exit(0)
    except Exception as e:
        print(f"强制退出失败: {e}")
        sys.exit(0)

class DownloadHandler:
    def __init__(self, window=None):
        self.window = window
    
    def selectDownloadFolder(self, initial_dir=None):
        return select_folder("请选择下载保存位置", initial_dir)
    
    def downloadWithDir(self, url, filename, download_dir, show_success=True):
        if not download_dir:
            show_message_box("未指定下载目录", "下载错误", 0x10)
            raise Exception("未指定下载目录")
        
        if not filename:
            filename = url.split('/')[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
            if not filename:
                filename = "download.mp3"
        
        # 直接执行下载，不使用线程，以便返回实际的下载结果
        success = download_file(url, filename, download_dir, show_success)
        if not success:
            raise Exception("下载失败")
        return True
    
    def saveTextFile(self, content, filename, save_dir, show_success=True):
        if not save_dir:
            show_message_box("未指定保存目录", "保存错误", 0x10)
            raise Exception("未指定保存目录")
        
        if not filename:
            filename = "untitled.txt"
        
        success = save_text_file(content, filename, save_dir)
        if not success:
            raise Exception("保存失败，请检查目录权限")
        
        if show_success:
            show_message_box(
                f"保存成功！\n\n文件已保存到：\n{os.path.join(save_dir, filename)}",
                "保存成功",
                0x40
            )
        return True
    
    def checkUpdate(self, url):
        return check_update(url)
    
    def fetchUrl(self, url):
        return fetch_url(url)
    
    def closeApp(self):
        try:
            force_kill_process()
            return True
        except Exception as e:
            print(f"关闭应用失败: {e}")
            return False
    
    def saveLocalFolder(self, folder_path):
        try:
            config_file = os.path.join(log_dir, 'local_folder.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'localFolder': folder_path}, f)
            return True
        except Exception as e:
            print(f"保存本地文件夹路径失败: {e}")
            return False
    
    def getLocalFolder(self):
        try:
            config_file = os.path.join(log_dir, 'local_folder.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('localFolder', None)
            return None
        except Exception as e:
            print(f"读取本地文件夹路径失败: {e}")
            return None
    
    def clearLocalFolder(self):
        """清除本地文件夹配置"""
        try:
            config_file = os.path.join(log_dir, 'local_folder.json')
            if os.path.exists(config_file):
                os.remove(config_file)
                print("已清除本地文件夹配置")
            return True
        except Exception as e:
            print(f"清除本地文件夹配置失败: {e}")
            return False
    
    def selectLocalFolder(self):
        try:
            last_folder = self.getLocalFolder()
            folder = select_folder("请选择音乐文件夹", last_folder)
            if folder:
                self.saveLocalFolder(folder)
            return folder
        except Exception as e:
            print(f"选择本地文件夹失败: {e}")
            return None
    
    def scanLocalFolder(self, folder_path=None):
        try:
            if not folder_path:
                folder_path = self.getLocalFolder()
            
            if not folder_path or not os.path.exists(folder_path):
                return []
            
            audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a', '.wma']
            lrc_extensions = ['.lrc']
            
            audio_files = []
            lrc_files = {}
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_lower = file.lower()
                    file_path = os.path.join(root, file)
                    
                    if any(file_lower.endswith(ext) for ext in lrc_extensions):
                        base_name = os.path.splitext(file)[0]
                        lrc_files[base_name] = file_path
                    elif any(file_lower.endswith(ext) for ext in audio_extensions):
                        audio_files.append(file_path)
            
            tracks = []
            for i, audio_path in enumerate(audio_files):
                file_name = os.path.basename(audio_path)
                base_name = os.path.splitext(file_name)[0]
                
                title = base_name
                artist = ''
                album = ''
                
                separators = [' - ', ' – ', '-', '–', ':', '：']
                best_parts = [base_name]
                
                for sep in separators:
                    parts = base_name.split(sep)
                    if len(parts) > len(best_parts):
                        best_parts = parts
                
                if len(best_parts) >= 3:
                    artist = best_parts[0].strip()
                    album = best_parts[1].strip()
                    title = ' - '.join(best_parts[2:]).strip()
                elif len(best_parts) >= 2:
                    artist = best_parts[0].strip()
                    title = ' - '.join(best_parts[1:]).strip()
                
                title = re.sub(r'\[.*?\]', '', title).strip()
                
                lrc_content = ''
                if base_name in lrc_files:
                    try:
                        with open(lrc_files[base_name], 'r', encoding='utf-8') as f:
                            lrc_content = f.read()
                    except:
                        pass
                
                file_size = os.path.getsize(audio_path)
                
                tracks.append({
                    'uid': f'local_{int(time.time() * 1000)}_{i}',
                    'title': title,
                    'artist': artist,
                    'album': album,
                    'cover': '',
                    'audioUrl': audio_path,  # 直接返回文件路径
                    'lrc': lrc_content,
                    'source': 'local',
                    'quality': 'local',
                    'qualityLabel': '本地文件',
                    'fileName': file_name,
                    'filePath': audio_path,
                    'fileSize': file_size
                })
            
            return tracks
        except Exception as e:
            print(f"扫描本地文件夹失败: {e}")
            return []
    
    def readLocalFile(self, file_path):
        try:
            if not os.path.exists(file_path):
                return {'success': False, 'error': '文件不存在'}
            
            import base64
            with open(file_path, 'rb') as f:
                content = f.read()
            
            base64_content = base64.b64encode(content).decode('utf-8')
            
            del content
            
            return {'success': True, 'content': base64_content}
        except Exception as e:
            print(f"读取本地文件失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def getNeteaseChartList(self):
        """获取网易云所有榜单列表"""
        try:
            print("获取网易云榜单列表...")
            
            # 网易云音乐榜单列表页面
            url = "https://music.163.com/discover/toplist"
            
            # 设置请求头，模拟浏览器访问
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://music.163.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
            }
            
            # 使用与checkUpdate相同的网络请求方式
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                html = response.read().decode('utf-8')
                print(f"响应内容长度: {len(html)}")
                
                # 提取所有榜单信息
                import re
                # 匹配榜单链接和名称
                chart_pattern = re.compile(r'<a href="/discover/toplist\?id=(\d+)"[^>]*>(.*?)</a>', re.DOTALL)
                matches = chart_pattern.findall(html)
                
                charts = []
                for match in matches:
                    chart_id = match[0]
                    chart_name = match[1].strip()
                    # 清理名称，去除可能的标签和空白
                    chart_name = re.sub(r'<.*?>', '', chart_name)
                    chart_name = chart_name.strip()
                    if chart_name:
                        charts.append({
                            'id': chart_id,
                            'name': chart_name
                        })
                
                print(f"获取到{len(charts)}个榜单")
                return {'success': True, 'data': charts}
        except Exception as e:
            print(f"获取网易云榜单列表失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def getNeteaseChart(self, chart_id):
        """获取网易云榜单数据"""
        try:
            print(f"获取网易云榜单数据，ID: {chart_id}...")
            
            # 网易云音乐榜单的网页地址
            url = f"https://music.163.com/discover/toplist?id={chart_id}"
            
            # 设置请求头，模拟浏览器访问
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://music.163.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
            }
            
            # 使用与checkUpdate相同的网络请求方式
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                html = response.read().decode('utf-8')
                print(f"响应内容长度: {len(html)}")
                
                # 提取包含歌曲列表的JSON数据
                import re
                # 找到所有textarea标签，第一个通常包含歌曲数据
                all_textareas = re.findall(r'<textarea[^>]*>(.*?)</textarea>', html, re.DOTALL)
                
                if all_textareas:
                    # 第一个textarea包含歌曲数据
                    song_data_json = all_textareas[0]
                    print(f"提取到的歌曲数据JSON长度: {len(song_data_json)}")
                    song_data = json.loads(song_data_json)
                    
                    # 提取歌曲信息
                    songs = []
                    for song in song_data:
                        # 提取歌曲ID
                        song_id = song.get('id', '')
                        # 提取歌曲标题和艺术家
                        title = song.get('name', '未知歌曲')
                        # 提取艺术家
                        artists = song.get('artists', [])
                        artist_names = [artist.get('name', '') for artist in artists]
                        artist = ' / '.join(artist_names) if artist_names else '未知艺术家'
                        
                        songs.append({
                            'id': song_id,
                            'songid': song_id,
                            'uid': f'netease-{song_id}',
                            'title': title,
                            'artist': artist,
                            'source': 'netease'
                        })
                    
                    print(f"获取网易云榜单成功，共{len(songs)}首歌曲")
                    return {'success': True, 'data': {'tracks': songs}}
                else:
                    raise Exception('未找到歌曲数据')
        except Exception as e:
            print(f"获取网易云榜单失败: {e}")
            # 失败时返回空数据，避免前端出错
            return {'success': True, 'data': {'tracks': []}}
            
    def getCantonesePlaylists(self, language='粤语'):
        """获取网易云歌单列表"""
        try:
            print(f"[DEBUG] 获取网易云{language}歌单列表开始...")
            
            # 添加随机延迟，避免访问过于频繁
            import time
            import random
            delay = random.uniform(0.5, 1)  # 0.5-1秒随机延迟
            print(f"[DEBUG] 添加延迟: {delay:.2f}秒")
            time.sleep(delay)
            
            # 网易云音乐歌单页面（需要对中文参数进行编码）
            import urllib.parse
            cat_param = urllib.parse.quote(language)
            url = f"https://music.163.com/discover/playlist/?cat={cat_param}"
            print(f"[DEBUG] 访问URL: {url}")
            
            # 设置请求头，模拟浏览器访问
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://music.163.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
            }
            print(f"[DEBUG] 请求头设置完成")
            
            # 使用与checkUpdate相同的网络请求方式
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            print(f"[DEBUG] SSL上下文配置完成")
            
            req = urllib.request.Request(url, headers=headers)
            print(f"[DEBUG] 请求对象创建完成")
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                print(f"[DEBUG] 请求成功，状态码: {response.status}")
                html = response.read().decode('utf-8')
                print(f"[DEBUG] 响应内容长度: {len(html)}")
                
                # 保存响应内容到临时文件，方便调试
                import tempfile
                import os
                temp_file = os.path.join(tempfile.gettempdir(), 'cantonese_playlist_debug.html')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"[DEBUG] 响应内容已保存到临时文件: {temp_file}")
                
                # 提取歌单信息
                import re
                print(f"[DEBUG] 开始提取歌单信息...")
                
                # 根据用户提供的HTML结构，使用更精准的正则表达式
                # 匹配title属性、href中的歌单ID和class属性（按实际顺序）
                playlist_pattern = re.compile(r'<a[^>]*title="([^"]+)"[^>]*href="/playlist\?id=(\d+)"[^>]*class="tit f-thide s-fc0"', re.DOTALL)
                matches = playlist_pattern.findall(html)
                print(f"[DEBUG] 优化后的正则表达式匹配到 {len(matches)} 个结果")
                
                playlists = []
                # 获取前20个歌单
                for i, match in enumerate(matches[:20]):
                    playlist_name = match[0].strip()  # title属性值
                    playlist_id = match[1]            # href中的ID
                    if playlist_name:
                        playlists.append({
                            'id': playlist_id,
                            'name': playlist_name
                        })
                
                if not playlists:
                    # 尝试第二种正则表达式，可能是因为HTML结构不同
                    print("[DEBUG] 第一种正则表达式未匹配到结果，尝试第二种正则表达式...")
                    playlist_pattern2 = re.compile(r'<a href="/playlist\?id=(\d+)"[^>]*title="([^"]+)"[^>]*class="tit f-thide s-fc0"', re.DOTALL)
                    matches2 = playlist_pattern2.findall(html)
                    print(f"[DEBUG] 第二种正则表达式匹配到 {len(matches2)} 个结果")
                    for i, match in enumerate(matches2[:10]):
                        playlist_id = match[0]
                        playlist_name = match[1].strip()
                        if playlist_name:
                            playlists.append({
                                'id': playlist_id,
                                'name': playlist_name
                            })
                
                if not playlists:
                    # 尝试第三种更宽松的正则表达式
                    print("[DEBUG] 第二种正则表达式未匹配到结果，尝试第三种正则表达式...")
                    playlist_pattern3 = re.compile(r'<a href="/playlist\?id=(\d+)"[^>]*>(.*?)</a>', re.DOTALL)
                    matches3 = playlist_pattern3.findall(html)
                    print(f"[DEBUG] 第三种正则表达式匹配到 {len(matches3)} 个结果")
                    for i, match in enumerate(matches3[:10]):
                        playlist_id = match[0]
                        playlist_name = match[1].strip()
                        # 清理名称，去除可能的标签和空白
                        playlist_name = re.sub(r'<.*?>', '', playlist_name)
                        playlist_name = playlist_name.strip()
                        if playlist_name and len(playlist_name) > 1:
                            playlists.append({
                                'id': playlist_id,
                                'name': playlist_name
                            })
                
                print(f"[DEBUG] 最终获取到{len(playlists)}个粤语歌单")
                if playlists:
                    print(f"[DEBUG] 前3个歌单: {playlists[:3]}")
                return {'success': True, 'data': playlists}
        except Exception as e:
            print(f"[DEBUG] 获取网易云粤语歌单列表失败: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
            
    def getNeteasePlaylist(self, playlist_id):
        """获取网易云歌单歌曲数据"""
        try:
            # 输出日志到前端控制台
            if self.window:
                self.window.evaluate_js(
                    f"console.log({json.dumps(f'[DEBUG] 获取网易云歌单数据开始，ID: {playlist_id}...')})")
            print(f"[DEBUG] 获取网易云歌单数据开始，ID: {playlist_id}...")
            
            # 添加随机延迟，避免访问过于频繁
            import time
            import random
            delay = random.uniform(0.5, 1)  # 0.5-1秒随机延迟
            if self.window:
                self.window.evaluate_js(
                    f"console.log({json.dumps(f'[DEBUG] 添加延迟: {delay:.2f}秒')})")
            print(f"[DEBUG] 添加延迟: {delay:.2f}秒")
            time.sleep(delay)
            
            # 使用网易云音乐API获取歌单数据
            api_url = f"https://music.163.com/api/playlist/detail?id={playlist_id}"
            if self.window:
                self.window.evaluate_js(
                    f"console.log({json.dumps(f'[DEBUG] API URL: {api_url}')})")
            print(f"[DEBUG] API URL: {api_url}")
            
            # 设置请求头，模拟浏览器访问
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://music.163.com/',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            if self.window:
                self.window.evaluate_js('console.log("[DEBUG] 请求头设置完成")')
            print(f"[DEBUG] 请求头设置完成")
            
            # 使用与checkUpdate相同的网络请求方式
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            if self.window:
                self.window.evaluate_js('console.log("[DEBUG] SSL上下文配置完成")')
            print(f"[DEBUG] SSL上下文配置完成")
            
            req = urllib.request.Request(api_url, headers=headers)
            if self.window:
                self.window.evaluate_js('console.log("[DEBUG] 请求对象创建完成")')
            print(f"[DEBUG] 请求对象创建完成")
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                if self.window:
                    self.window.evaluate_js(
                        f"console.log({json.dumps(f'[DEBUG] 请求成功，状态码: {response.status}')})")
                print(f"[DEBUG] 请求成功，状态码: {response.status}")
                data = response.read().decode('utf-8')
                if self.window:
                    self.window.evaluate_js(
                        f"console.log({json.dumps(f'[DEBUG] 响应内容长度: {len(data)}')})")
                    # 只打印响应长度，避免复杂的字符串转义问题
                print(f"[DEBUG] 响应内容长度: {len(data)}")
                print(f"[DEBUG] 响应内容前200字符: {data[:200]}")
                
                # 解析JSON数据
                try:
                    result = json.loads(data)
                    if self.window:
                        self.window.evaluate_js('console.log("[DEBUG] JSON解析成功")')
                        code = result.get('code')
                        message = result.get('message')
                        self.window.evaluate_js(
                            f'console.log({json.dumps(f"[DEBUG] API 响应 code: {code}")})')
                        self.window.evaluate_js(
                            f'console.log({json.dumps(f"[DEBUG] API 响应 message: {message}")})')
                    print(f"[DEBUG] JSON解析成功")
                    print(f"[DEBUG] API 响应 code: {result.get('code')}")
                    print(f"[DEBUG] API 响应 message: {result.get('message')}")
                except json.JSONDecodeError as e:
                    if self.window:
                        self.window.evaluate_js(
                            f"console.log({json.dumps(f'[DEBUG] JSON解析失败: {e}')})")
                        self.window.evaluate_js(
                            f"console.log({json.dumps(f'[DEBUG] 响应内容: {data[:100]}...')})")
                    print(f"[DEBUG] JSON解析失败: {e}")
                    print(f"[DEBUG] 响应内容: {data}")
                    raise
                
                # 检查API返回状态
                if result.get('code') == 200:
                    playlist = result.get('result', {})
                    tracks = playlist.get('tracks', [])
                    if self.window:
                        self.window.evaluate_js(
                            f"console.log({json.dumps(f'[DEBUG] 获取到 {len(tracks)} 首歌曲')})")
                    print(f"[DEBUG] 获取到 {len(tracks)} 首歌曲")
                    
                    if tracks:
                        # 提取歌曲信息
                        songs = []
                        for i, track in enumerate(tracks):
                            # 打印前10首歌曲的信息
                            if i < 10:
                                # 只在控制台打印，避免JavaScript语法错误
                                try:
                                    # 使用ensure_ascii=True避免编码错误
                                    print(f"[DEBUG] 歌曲 {i+1} 数据结构: {json.dumps(track, ensure_ascii=True)[:100]}...")
                                except Exception as e:
                                    # 捕获编码错误，避免程序崩溃
                                    print(f"[DEBUG] 打印歌曲信息时出错: {e}")
                                    # 只打印标题和艺术家，避免复杂的编码问题
                                    print(f"[DEBUG] 歌曲 {i+1}: {track.get('name', '未知歌曲')} - {', '.join([artist.get('name', '') for artist in track.get('artists', [])])}")
                            
                            # 提取歌曲ID
                            song_id = track.get('id', '')
                            # 提取歌曲标题
                            title = track.get('name', '未知歌曲')
                            # 提取艺术家
                            artists = track.get('artists', [])
                            artist_names = [artist.get('name', '') for artist in artists]
                            artist = ' / '.join(artist_names) if artist_names else '未知艺术家'
                            
                            songs.append({
                                'id': song_id,
                                'songid': song_id,
                                'uid': f'netease-{song_id}',
                                'title': title,
                                'artist': artist,
                                'source': 'netease'
                            })
                        
                        if self.window:
                            self.window.evaluate_js(
                                f"console.log({json.dumps(f'[DEBUG] 获取网易云歌单成功，共{len(songs)}首歌曲')})")
                        print(f"[DEBUG] 获取网易云歌单成功，共{len(songs)}首歌曲")
                        return {'success': True, 'data': {'tracks': songs, 'code': result.get('code'), 'message': result.get('message')}} 
                    else:
                        raise Exception('API返回的歌单中没有歌曲')
                elif result.get('code') == -447:
                    # 服务器忙碌，重试一次
                    if self.window:
                        code = result.get('code')
                        message = result.get('message')
                        self.window.evaluate_js(
                            f'console.log({json.dumps(f"[DEBUG] API返回错误，代码: {code}, 消息: {message}")})')
                        self.window.evaluate_js('console.log("[DEBUG] 服务器忙碌，2秒后重试...")')
                    print(f"[DEBUG] API返回错误，代码: {result.get('code')}, 消息: {result.get('message')}")
                    print("[DEBUG] 服务器忙碌，2秒后重试...")
                    time.sleep(2)
                    if self.window:
                        self.window.evaluate_js('console.log("[DEBUG] 开始重试...")')
                    print("[DEBUG] 开始重试...")
                    # 重新发送请求
                    req = urllib.request.Request(api_url, headers=headers)
                    with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                        if self.window:
                            self.window.evaluate_js(
                                f"console.log({json.dumps(f'[DEBUG] 重试请求成功，状态码: {response.status}')})")
                        print(f"[DEBUG] 重试请求成功，状态码: {response.status}")
                        data = response.read().decode('utf-8')
                        if self.window:
                            self.window.evaluate_js(
                                f"console.log({json.dumps(f'[DEBUG] 重试响应内容长度: {len(data)}')})")
                        print(f"[DEBUG] 重试响应内容长度: {len(data)}")
                        result = json.loads(data)
                        if self.window:
                            code = result.get('code')
                            message = result.get('message')
                            self.window.evaluate_js(
                                f'console.log({json.dumps(f"[DEBUG] 重试 API 响应 code: {code}")})')
                            self.window.evaluate_js(
                                f'console.log({json.dumps(f"[DEBUG] 重试 API 响应 message: {message}")})')
                        print(f"[DEBUG] 重试 API 响应 code: {result.get('code')}")
                        print(f"[DEBUG] 重试 API 响应 message: {result.get('message')}")
                        
                        if result.get('code') == 200:
                            playlist = result.get('result', {})
                            tracks = playlist.get('tracks', [])
                            if self.window:
                                self.window.evaluate_js(
                                    f"console.log({json.dumps(f'[DEBUG] 重试获取到 {len(tracks)} 首歌曲')})")
                            print(f"[DEBUG] 重试获取到 {len(tracks)} 首歌曲")
                            
                            if tracks:
                                # 提取歌曲信息
                                songs = []
                                for i, track in enumerate(tracks):
                                    # 提取歌曲ID
                                    song_id = track.get('id', '')
                                    # 提取歌曲标题
                                    title = track.get('name', '未知歌曲')
                                    # 提取艺术家
                                    artists = track.get('artists', [])
                                    artist_names = [artist.get('name', '') for artist in artists]
                                    artist = ' / '.join(artist_names) if artist_names else '未知艺术家'
                                    
                                    songs.append({
                                        'id': song_id,
                                        'songid': song_id,
                                        'uid': f'netease-{song_id}',
                                        'title': title,
                                        'artist': artist,
                                        'source': 'netease'
                                    })
                                
                                if self.window:
                                    self.window.evaluate_js(
                                        f"console.log({json.dumps(f'[DEBUG] 重试获取网易云歌单成功，共{len(songs)}首歌曲')})")
                                print(f"[DEBUG] 重试获取网易云歌单成功，共{len(songs)}首歌曲")
                                return {'success': True, 'data': {'tracks': songs, 'code': result.get('code'), 'message': result.get('message')}} 
                            else:
                                raise Exception('API返回的歌单中没有歌曲')
                        else:
                            raise Exception(f'API返回错误，代码: {result.get("code")}')
                else:
                    raise Exception(f'API返回错误，代码: {result.get("code")}')
        except Exception as e:
            if self.window:
                self.window.evaluate_js(
                    f"console.log({json.dumps(f'[DEBUG] 获取网易云歌单失败: {e}')})")
            print(f"[DEBUG] 获取网易云歌单失败: {e}")
            import traceback
            traceback.print_exc()
            # 失败时返回空数据，避免前端出错
            return {'success': True, 'data': {'tracks': []}}
    
    def downloadUpdate(self, url, save_path, temp_filename, script_filename):
        """下载更新文件
        
        Args:
            url: 下载链接
            save_path: 保存目录
            temp_filename: 临时文件名（带随机后缀）
            script_filename: 批处理脚本文件名
        
        Returns:
            dict: 下载结果
        """
        try:
            import requests
            import time
            
            # 确保保存目录存在
            os.makedirs(save_path, exist_ok=True)
            
            # 下载文件路径（带随机后缀的临时文件名）
            download_path = os.path.join(save_path, temp_filename)
            script_path = os.path.join(save_path, script_filename)
            
            # 最终目标文件名
            target_exe = os.path.join(save_path, 'pikachu_music.exe')
            
            print(f"[更新] 开始下载更新文件: {url}")
            print(f"[更新] 下载路径: {download_path}")
            print(f"[更新] 目标路径: {target_exe}")
            
            # 下载文件
            response = requests.get(url, stream=True, verify=False)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            start_time = time.time()
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 计算进度
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed = downloaded_size / elapsed_time / 1024  # KB/s
                                remaining = (total_size - downloaded_size) / 1024 / speed if speed > 0 else 0
                                print(f"[更新] 下载进度: {progress}% - {speed:.2f} KB/s - 剩余 {remaining:.1f} 秒")
                            else:
                                print(f"[更新] 下载进度: {progress}%")
            
            elapsed_time = time.time() - start_time
            total_size_mb = total_size / 1024 / 1024
            print(f"[更新] 下载完成: {download_path}")
            print(f"[更新] 下载大小: {total_size_mb:.2f} MB")
            print(f"[更新] 耗时: {elapsed_time:.2f} 秒")
            
            # 生成批处理脚本：等待软件关闭 -> 删除旧文件 -> 重命名新文件 -> 创建快捷方式 -> 删除脚本
            script_content = f"@echo off\n"
            script_content += f"chcp 65001 >nul\n"
            script_content += f"\n"
            script_content += f":: 输出执行日志到同目录的log文件\n"
            script_content += f"set \"LOG_FILE=%~dpn0.log\"\n"
            script_content += f"echo 更新开始: %date% %time% > \"%LOG_FILE%\"\n"
            script_content += f"echo 目标文件: {target_exe} >> \"%LOG_FILE%\"\n"
            script_content += f"echo 下载文件: {download_path} >> \"%LOG_FILE%\"\n"
            script_content += f"echo 保存路径: {save_path} >> \"%LOG_FILE%\"\n"
            script_content += f"\n"
            script_content += f":: 检查软件是否正在运行\n"
            script_content += f":check_running\n"
            script_content += f"echo 检查软件是否运行... >> \"%LOG_FILE%\"\n"
            script_content += f"tasklist | find /i \"pikachu_music.exe\" >nul\n"
            script_content += f"if %errorlevel% equ 0 (\n"
            script_content += f"    echo 软件正在运行，等待关闭... >> \"%LOG_FILE%\"\n"
            script_content += f"    timeout /t 1 /nobreak >nul\n"
            script_content += f"    goto check_running\n"
            script_content += f")\n"
            script_content += f"echo 软件已关闭，开始更新 >> \"%LOG_FILE%\"\n"
            script_content += f":: 等待1秒确保软件完全关闭\n"
            script_content += f"timeout /t 1 /nobreak >nul\n"
            script_content += f"\n"
            script_content += f":: 覆盖文件\n"
            script_content += f"echo 更新文件: {download_path} -> {target_exe} >> \"%LOG_FILE%\"\n"
            
            script_content += f"if exist \"{target_exe}\" (\n"
            script_content += f"    del /f /q \"{target_exe}\" >> \"%LOG_FILE%\" 2>&1\n"
            script_content += f")\n"
            
            script_content += f"move /y \"{download_path}\" \"{target_exe}\" >> \"%LOG_FILE%\" 2>&1\n"
            
            script_content += f"if %errorlevel% equ 0 (\n"
            script_content += f"    echo 文件更新成功 >> \"%LOG_FILE%\"\n"
            script_content += f") else (\n"
            script_content += f"    echo 文件更新失败，错误代码：%errorlevel% >> \"%LOG_FILE%\"\n"
            script_content += f")\n"
            script_content += f"\n"
            script_content += f":: 强制Windows重新识别文件（通过复制到新文件再覆盖）\n"
            script_content += f"echo 刷新文件元数据... >> \"%LOG_FILE%\"\n"
            script_content += f"copy /y \"{target_exe}\" \"{save_path}\\pikachu_music_temp_icon.exe\" >nul 2>&1\n"
            script_content += f"del /f /q \"{target_exe}\" >nul 2>&1\n"
            script_content += f"move /y \"{save_path}\\pikachu_music_temp_icon.exe\" \"{target_exe}\" >nul 2>&1\n"
            script_content += f"echo 文件元数据刷新完成 >> \"%LOG_FILE%\"\n"
            script_content += f"\n"
            script_content += f":: 检查更新后的文件是否存在（使用dir命令避免中文路径问题）\n"
            script_content += f"dir \"{target_exe}\" >nul 2>&1\n"
            script_content += f"if %errorlevel% equ 0 (\n"
            script_content += f"    echo 目标文件存在: {target_exe} >> \"%LOG_FILE%\"\n"
            script_content += f"    :: 等待3秒让Windows更新文件信息和图标缓存\n"
            script_content += f"    timeout /t 3 /nobreak >nul\n"
            script_content += f") else (\n"
            script_content += f"    echo 错误：目标文件不存在: {target_exe} >> \"%LOG_FILE%\"\n"
            script_content += f"    echo 无法创建快捷方式，退出 >> \"%LOG_FILE%\"\n"
            script_content += f"    goto end\n"
            script_content += f")\n"
            script_content += f"\n"
            script_content += f":: 创建或更新桌面快捷方式\n"
            script_content += f"echo 开始创建/更新快捷方式 >> \"%LOG_FILE%\"\n"
            script_content += f":: 先删除旧快捷方式以刷新图标缓存\n"
            script_content += f"if exist \"%USERPROFILE%\\Desktop\\pikachu_music.lnk\" (\n"
            script_content += f"    del \"%USERPROFILE%\\Desktop\\pikachu_music.lnk\" >> \"%LOG_FILE%\" 2>&1\n"
            script_content += f"    echo 已删除旧快捷方式 >> \"%LOG_FILE%\"\n"
            script_content += f")\n"
            script_content += f":: 生成VBS脚本内容\n"
            script_content += f"set \"VBS_PATH=%~dpn0_temp.vbs\"\n"
            script_content += f":: 执行Python预先生成的VBS文件\n"
            script_content += f"cscript //nologo \"%VBS_PATH%\" >> \"%LOG_FILE%\" 2>&1\n"
            script_content += f"if %errorlevel% equ 0 (\n"
            script_content += f"    echo 快捷方式更新成功！ >> \"%LOG_FILE%\"\n"
            script_content += f") else (\n"
            script_content += f"    echo 快捷方式更新失败，错误代码：%errorlevel% >> \"%LOG_FILE%\"\n"
            script_content += f")\n"
            script_content += f"echo 删除临时VBS文件 >> \"%LOG_FILE%\"\n"
            script_content += f"del \"%VBS_PATH%\"\n"
            script_content += f":: 刷新Windows图标缓存\n"
            script_content += f"ie4uinit.exe -show >> \"%LOG_FILE%\" 2>&1\n"
            script_content += f"\n"
            script_content += f":: 等待VBS脚本完成快捷方式创建\n"
            script_content += f"timeout /t 1 /nobreak >nul\n"
            script_content += f":: 检查快捷方式是否创建成功（使用dir命令避免中文路径问题）\n"
            script_content += f"echo 检查快捷方式路径: %USERPROFILE%\\Desktop\\pikachu_music.lnk >> \"%LOG_FILE%\"\n"
            script_content += f"dir \"%USERPROFILE%\\Desktop\\pikachu_music.lnk\" >nul 2>&1\n"
            script_content += f"if %errorlevel% equ 0 (\n"
            script_content += f"    echo 快捷方式文件存在 >> \"%LOG_FILE%\"\n"
            script_content += f") else (\n"
            script_content += f"    echo 错误：快捷方式文件不存在 >> \"%LOG_FILE%\"\n"
            script_content += f")\n"
            script_content += f"\n"
            script_content += f":end\n"
            script_content += f":: 更新完成，删除脚本\n"
            script_content += f"echo 更新完成，准备删除脚本 >> \"%LOG_FILE%\"\n"
            script_content += f":: 使用cmd.exe /c 来删除脚本自身（使用%~f0获取当前脚本路径）\n"
            script_content += f"cmd.exe /c \"timeout /t 2 /nobreak >nul && del \"%~f0\"\"\n"
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            vbs_path = script_path.replace('.bat', '_temp.vbs')
            desktop_path = os.path.join(os.environ["USERPROFILE"], "Desktop").replace("\\", "\\\\")
            vbs_content = f'Set oWS = CreateObject("WScript.Shell")\n'
            vbs_content += f'sLinkFile = "{desktop_path}\\pikachu_music.lnk"\n'
            vbs_content += f'Set oLink = oWS.CreateShortcut(sLinkFile)\n'
            vbs_content += f'oLink.TargetPath = "{target_exe}"\n'
            vbs_content += f'oLink.WorkingDirectory = "{save_path}"\n'
            vbs_content += f'oLink.Description = "pikachu_music"\n'
            vbs_content += f'oLink.IconLocation = "{target_exe},0"\n'
            vbs_content += f'oLink.Save\n'
            
            with open(vbs_path, 'w', encoding='gbk') as f:
                f.write(vbs_content)
            
            print(f"[更新] 生成批处理脚本: {script_path}")
            print(f"[更新] 生成VBS脚本: {vbs_path}")
            
            return {
                'success': True,
                'temp_file': download_path,
                'script_file': script_path,
                'message': '下载完成',
                'save_path': save_path
            }
        except Exception as e:
            print(f"[更新] 下载更新失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def runUpdateScript(self, script_path):
        """运行更新脚本
        
        Args:
            script_path: 脚本路径
        
        Returns:
            dict: 运行结果
        """
        try:
            import subprocess
            
            print(f"运行更新脚本: {script_path}")
            
            # 确保脚本路径存在
            if not os.path.exists(script_path):
                raise Exception(f"脚本文件不存在: {script_path}")
            
            # 启动脚本并退出当前进程
            # 使用shell=True来处理包含空格和中文的路径
            subprocess.Popen(script_path, shell=True)
            
            # 关闭当前应用
            self.closeApp()
            
            return {
                'success': True,
                'message': '脚本已启动'
            }
        except Exception as e:
            print(f"运行脚本失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def checkShortcutExists(self):
        """检查桌面快捷方式是否存在
        
        Returns:
            bool: 是否存在
        """
        try:
            # 桌面路径
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop_path, "pikachu_music.lnk")
            
            return os.path.exists(shortcut_path)
        except Exception as e:
            print(f"检查快捷方式失败: {e}")
            return False
    
    def createShortcut(self, target_exe=None):
        """创建桌面快捷方式
        
        Args:
            target_exe: 目标可执行文件路径，如果为None则使用当前可执行文件
            
        Returns:
            dict: 创建结果
        """
        try:
            # 获取目标可执行文件路径
            if target_exe:
                current_exe = target_exe
            else:
                current_exe = sys.executable
            
            # 桌面路径
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop_path, "pikachu_music.lnk")
            
            # 确保路径存在
            os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
            
            # 使用批处理脚本创建快捷方式
            import tempfile
            import subprocess
            
            # 创建临时VBS脚本，使用gbk编码以支持VBScript
            with tempfile.NamedTemporaryFile(suffix='.vbs', delete=False, mode='w', encoding='gbk') as f:
                # 定义工作目录变量
                working_dir = os.path.dirname(current_exe)
                
                # 转义VBS脚本中的特殊字符
                def escape_vbs_string(s):
                    # VBS中只需要将双引号替换为两个双引号
                    return s.replace('"', '""')
                
                # 图标路径：使用当前正在运行的exe的图标
                # 这样即使目标文件还不存在（更新流程中），快捷方式也能显示正确的图标
                icon_source = sys.executable
                
                vbs_script = f"""
Set oWS = CreateObject("WScript.Shell")
sLinkFile = "{escape_vbs_string(shortcut_path)}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{escape_vbs_string(current_exe)}"
oLink.WorkingDirectory = "{escape_vbs_string(working_dir)}"
oLink.Description = "pikachu_music"
oLink.IconLocation = "{escape_vbs_string(icon_source)}, 0"
oLink.Save
"""
                f.write(vbs_script)
                temp_vbs = f.name
            
            try:
                # 运行VBS脚本，使用列表形式的参数
                result = subprocess.run(['cscript', '//nologo', temp_vbs], capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"VBS脚本执行失败: {result.stderr}")
                
                print(f"VBS脚本执行成功")
            finally:
                # 确保临时文件被删除
                try:
                    if os.path.exists(temp_vbs):
                        os.unlink(temp_vbs)
                        print(f"临时文件已删除: {temp_vbs}")
                except Exception as e:
                    print(f"删除临时文件失败: {e}")
            
            print(f"创建快捷方式成功: {shortcut_path}")
            return {
                'success': True,
                'message': '快捷方式创建成功'
            }
        except Exception as e:
            print(f"创建快捷方式失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def uploadFile(self, content, filename):
        try:
            print(f"=== 开始上传文件 ===")
            print(f"文件名: {filename}")
            print(f"文件大小: {len(content)} 字符")
            
            # 1. 创建临时文件
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_file_path = f.name
            
            print(f"创建临时文件: {temp_file_path}")
            print(f"临时文件大小: {os.path.getsize(temp_file_path)} 字节")
            
            try:
                # 2. 直接导入wss模块并调用其上传功能
                print("正在导入wss模块并调用上传功能...")
                
                # 动态导入wss模块
                import importlib.util
                import sys
                
                # 获取wss.py的路径
                wss_path = os.path.join(os.path.dirname(__file__), 'wss.py')
                print(f"wss.py路径: {wss_path}")
                
                # 创建模块规范
                spec = importlib.util.spec_from_file_location("wss", wss_path)
                if spec is None:
                    raise Exception(f"无法创建wss模块规范: {wss_path}")
                
                # 创建模块
                wss_module = importlib.util.module_from_spec(spec)
                if wss_module is None:
                    raise Exception("无法创建wss模块")
                
                # 添加到sys.modules
                sys.modules["wss"] = wss_module
                
                # 执行模块
                spec.loader.exec_module(wss_module)
                print("wss模块导入成功")
                
                # 调用wss模块的上传功能
                # 首先检查wss模块是否有upload函数
                if hasattr(wss_module, 'upload'):
                    print("调用wss模块的upload函数...")
                    # 捕获标准输出
                    import io
                    from contextlib import redirect_stdout
                    
                    # 保存原始的argv
                    original_argv = sys.argv.copy()
                    try:
                        # 创建requests会话并初始化
                        import requests
                        s = requests.Session()
                        # 调用wss模块的login_anonymous函数获取token
                        token = wss_module.login_anonymous(s)
                        print(f"获取到token: {token[:20]}...")
                        # 设置必要的头部
                        s.headers['X-TOKEN'] = token
                        s.headers['User-Agent'] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0"
                        s.headers['Accept-Language'] = "en-US, en;q=0.9"
                        
                        # 将会话对象添加到wss模块的全局变量中
                        wss_module.s = s
                        
                        # 捕获标准输出
                        f = io.StringIO()
                        with redirect_stdout(f):
                            # 调用upload函数
                            wss_module.upload(temp_file_path)
                        output = f.getvalue()
                        print(f"wss.upload()输出: {output}")
                        
                        # 解析输出，提取分享链接
                        share_url = None
                        for line in output.split('\n'):
                            if '公共链接：' in line:
                                share_url = line.split('：')[1].strip()
                                break
                            elif 'https://www.wenshushu.cn/t/' in line:
                                share_url = line.strip()
                                break
                            elif 'wss.ink/' in line:
                                share_url = line.strip()
                                break
                        
                        if not share_url:
                            print("未找到分享链接")
                            return {'success': False, 'error': '未找到分享链接'}
                        
                        print(f"\n=== 上传成功 ===")
                        print(f"分享链接: {share_url}")
                        
                        return {'success': True, 'url': share_url}
                    finally:
                        # 恢复原始的argv
                        sys.argv = original_argv
                else:
                    raise Exception("wss模块中没有找到upload函数")
            except Exception as e:
                print(f"调用wss模块失败: {e}")
                import traceback
                traceback.print_exc()
                return {'success': False, 'error': str(e)}
            finally:
                # 删除临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    print(f"删除临时文件: {temp_file_path}")
        except Exception as e:
            print(f"上传文件失败: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
        finally:
            print("=== 上传操作结束 ===")

# 本地 HTTP 服务器，用于提供本地音乐文件
class LocalMusicHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def log_message(self, format, *args):
        # 简化日志输出
        pass
    
    def do_GET(self):
        """处理 GET 请求，支持完整的文件路径"""
        import urllib.parse
        import mimetypes
        
        try:
            # 解析 URL 路径
            path = self.path
            # 移除开头的 /
            if path.startswith('/'):
                path = path[1:]
            # 解码 URL 编码的路径
            path = urllib.parse.unquote(path)
            
            # 检查文件是否存在
            if not os.path.exists(path):
                self.send_error(404, "File not found")
                return
            
            # 检查是否是文件
            if not os.path.isfile(path):
                self.send_error(404, "File not found")
                return
            
            # 检查文件类型，只允许音频文件
            allowed_extensions = ['.mp3', '.wav', '.flac', '.ogg', '.wma', '.aac', '.m4a']
            ext = os.path.splitext(path)[1].lower()
            if ext not in allowed_extensions:
                self.send_error(403, "Forbidden: Only audio files are allowed")
                return
            
            # 发送文件
            self.send_response(200)
            # 猜测文件类型
            content_type, _ = mimetypes.guess_type(path)
            if content_type:
                self.send_header('Content-type', content_type)
            else:
                self.send_header('Content-type', 'application/octet-stream')
            # 发送文件大小
            self.send_header('Content-Length', str(os.path.getsize(path)))
            self.end_headers()
            
            # 读取并发送文件内容
            with open(path, 'rb') as f:
                self.wfile.write(f.read())
                
        except Exception as e:
            self.send_error(500, f"Internal server error: {e}")

class LocalMusicServer:
    def __init__(self):
        self.port = 0  # 动态分配端口
        self.server = None
        self.thread = None
        self.base_url = None
        
    def find_free_port(self):
        """查找可用端口（使用 50000-60000 范围，避免常用端口）"""
        import random
        for _ in range(100):  # 最多尝试 100 次
            port = random.randint(50000, 60000)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('', port))
                    s.listen(1)
                    return port
                except OSError:
                    continue
        # 如果指定范围都不可用，使用系统分配的端口
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
        
    def start(self):
        """启动 HTTP 服务器"""
        self.port = self.find_free_port()
        self.base_url = f"http://localhost:{self.port}"
        
        def run_server():
            with socketserver.TCPServer(("", self.port), LocalMusicHandler) as httpd:
                self.server = httpd
                print(f"本地音乐服务器启动在端口 {self.port}")
                httpd.serve_forever()
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        return self.base_url
        
    def stop(self):
        """停止 HTTP 服务器"""
        if self.server:
            self.server.shutdown()
            print("本地音乐服务器已停止")
            
    def get_file_url(self, file_path):
        """将本地文件路径转换为 HTTP URL"""
        try:
            import urllib.parse
            # 获取文件的绝对路径
            abs_path = os.path.abspath(file_path)
            # 将反斜杠替换为正斜杠
            abs_path = abs_path.replace(os.sep, '/')
            # 对路径进行 URL 编码
            encoded_path = urllib.parse.quote(abs_path)
            # 构建完整的 HTTP URL
            return f"{self.base_url}/{encoded_path}"
        except Exception as e:
            print(f"转换文件路径失败: {e}")
            return None

def main():
    import webview
    
    html_path = get_resource_path("index.html")
    
    if not os.path.exists(html_path):
        show_message_box(
            f"找不到主页面文件：{html_path}\n\n请确保程序文件完整。",
            "文件缺失",
            0x10
        )
        return
    
    # 启动本地音乐服务器
    music_server = LocalMusicServer()
    music_server_url = music_server.start()
    print(f"本地音乐服务器地址: {music_server_url}")
    
    screen_width, screen_height = get_screen_size()
    
    window = webview.create_window(
        title="皮卡丘的音乐站 - Pikachu Music",
        url=html_path,
        width=screen_width,
        height=screen_height,
        x=0,
        y=0,
        resizable=True,
        fullscreen=False,
        text_select=True,
        confirm_close=True,
        maximized=True
    )
    
    download_handler = DownloadHandler(window)
    
    # 暴露音乐服务器相关函数
    def getMusicServerUrl():
        return music_server_url
    
    def getMusicFileUrl(file_path):
        return music_server.get_file_url(file_path)
    
    window.expose(getMusicServerUrl)
    window.expose(getMusicFileUrl)
    
    window.expose(download_handler.selectDownloadFolder)
    window.expose(download_handler.downloadWithDir)
    window.expose(download_handler.saveTextFile)
    window.expose(download_handler.checkUpdate)
    window.expose(download_handler.fetchUrl)
    window.expose(download_handler.uploadFile)
    window.expose(download_handler.closeApp)
    window.expose(download_handler.saveLocalFolder)
    window.expose(download_handler.getLocalFolder)
    window.expose(download_handler.clearLocalFolder)
    window.expose(download_handler.selectLocalFolder)
    window.expose(download_handler.scanLocalFolder)
    window.expose(download_handler.readLocalFile)
    window.expose(download_handler.getNeteaseChartList)
    window.expose(download_handler.getNeteaseChart)
    window.expose(download_handler.getCantonesePlaylists)
    window.expose(download_handler.getNeteasePlaylist)
    window.expose(download_handler.downloadUpdate)
    window.expose(download_handler.runUpdateScript)
    window.expose(download_handler.checkShortcutExists)
    window.expose(download_handler.createShortcut)
    
    webview.start(
        gui='edgechromium',
        debug=False,
        http_server=False,
        private_mode=False
    )

if __name__ == "__main__":
    main()