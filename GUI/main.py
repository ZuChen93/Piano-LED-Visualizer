# -*- coding:utf-8 -*-

import spidev as SPI
from GUI import ST7789
import RPi.GPIO as GPIO

import os
import re
import time
import threading
import subprocess

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Raspberry Pi pin configuration:
RST = 27
DC = 25
BL = 24
bus = 0
device_pin = 0

device = ST7789.ST7789(SPI.SpiDev(bus, device_pin), RST, DC, BL)

device.Init()

device.clear()


def canvas(device):
    class Canvas:
        def __init__(self, device):
            self.device = device
            self.image1 = Image.new("RGB", (device.width, device.height), "BLACK")
            self.draw = ImageDraw.Draw(self.image1)

        def __getattr__(self, item):
            return getattr(self.draw, item)

        def __enter__(self):
            return self

        def __exit__(self, x, y, z):
            self.device.ShowImage(self.image1, 0, 0)

    return Canvas(device)


def load_db(name="/home/pi/mac.db"):
    mac_db = {}
    for line in open(name).readlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        mac_prefix, device_name = line.split(" ", 1)
        mac_db[mac_prefix] = device_name
    return mac_db


#Mac_db = load_db()


# a = ImageDraw.ImageDraw()
# a.multiline_text()
def log(level, *info):
    _time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    s = ""
    if level == 1:
        s = "+"
    elif level == 2:
        s = "-"
    elif level == 3:
        s = "*"
    elif level == 4:
        s = "!"
    print("[%s] %s - %s" % (s, _time, ", ".join([str(x) for x in info])))


# 加载字体文件
# 常用字体
font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 17)
# 加载页面使用字体
font_m = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 17)
# 小字体，Wi-Fi右下角序号使用字体
font_l = ImageFont.truetype("/usr/share/fonts/truetype/droid/DejaVuSans.ttf", 11)
# 小字体，页面右上角时间使用字体
font_head = ImageFont.truetype("/usr/share/fonts/truetype/droid/DejaVuSans.ttf", 16)
# 大字体，首页时间使用字体
font_b = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf", 36)
# 大字体 首页标语使用字体
font_b_c = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 30)

# 定义常用变量


# 按钮定义
KEY_up_PIN = 6
KEY_down_PIN = 19
KEY_left_PIN = 5
KEY_right_PIN = 26
KEY_press_PIN = 13
ok_PIN = 21
main_PIN = 20
cancel_PIN = 16

# 初始化输入设备
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY_up_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 初始化⬆️按钮
GPIO.setup(KEY_down_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 初始化⬇️按钮
GPIO.setup(KEY_left_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 初始化⬅️按钮
GPIO.setup(KEY_right_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 初始化➡️按钮
GPIO.setup(KEY_press_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 初始化🀄️按钮
GPIO.setup(ok_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 初始化第一个按钮
GPIO.setup(main_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 初始化第二个按钮
GPIO.setup(cancel_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 初始化第三个按钮


# 图形菜单，常用图形存放的位置
class Graphics:
    @staticmethod
    def signal(draw, left=0, top=0, width=10, height=8, signal=100):
        tx_w = width / 3 * 2 + 2
        tx_h = height
        draw.polygon([(left, top), (left + tx_w, top), (left + tx_w / 2, top + tx_h / 2),
                      (left, top), (left + tx_w / 2, top), (left + tx_w / 2, top + tx_h),
                      (left + tx_w / 2, top)], outline="#75f4fd", fill="#75f4fd")
        for f in range(5):
            if not f * 25 < signal:
                break
            draw.rectangle((
                left + width / 2 + 1 + 3 * f, top + height - height * 0.25 * f, left + width / 2 + 2 + 3 * f,
                top + height), fill="#75f4fd")

    @staticmethod
    def battery(draw, left=112, top=0, width=15, height=8, battery=100):
        draw.rectangle((left + 1, top, left + width, top + height), outline=1, fill="White")
        draw.rectangle((left, top + height / 3, left, top + height / 3 * 2), fill="black")
        battery = battery / 100.0
        aviable = width - 5
        draw.rectangle((left + width - 2 - aviable * battery, top + 2, left + width - 2, top + height - 2), fill=1)

    @staticmethod
    def message(draw, left=0, right=0, width=0, height=0):
        pass

    @staticmethod
    def wifi(draw, left=0, top=0, width=9, height=9, signal=100, num=1):
        # blue = (72, 149, 236)
        blue = "#75f4fd"
        hui = (194, 194, 194)
        if signal > 0:
            draw.pieslice((left, top, left + width * 2, top + height * 2), -135, -45, fill=blue)
            draw.pieslice((left + 3, top + 3, left + width * 2 - 3, top + height * 2 - 3), -135, -45, fill="#132238")
            draw.pieslice((left + 6, top + 6, left + width * 2 - 6, top + height * 2 - 6), -135, -45, fill=blue)
            draw.pieslice((left + 9, top + 9, left + width * 2 - 9, top + height * 2 - 9), -135, -45, fill="#132238")
            draw.pieslice((left + 12, top + 12, left + width * 2 - 12, top + height * 2 - 12), -135, -45, fill=blue)
        else:
            draw.pieslice((left, top, left + width * 2, top + height * 2), -135, -45, outline=hui, fill=hui)
        draw.text((left + 24, top + 8), "%s" % num, font=font_l, fill="#75f4fd")


# 写入页面头部信息，包含信号，Wi-Fi网卡等信息
def write_header(draw, ip="", wifi={}):
    if ip:
        Graphics.signal(draw, left=108, top=1, width=20, height=17, signal=100)
    else:
        Graphics.signal(draw, left=108, top=1, width=20, height=17, signal=0)

    # Graphics.battery(draw, left=218, top=1, width=20, height=15)
    Graphics.message(draw)
    # draw.text((170, 0), time.strftime("%H:%M", time.localtime()), font=font_head, fill="white")
    count = 0
    for iface, status in wifi.items():
        if status == True:
            count += 1
            Graphics.wifi(draw, 130 + 33 * (count - 1), 1, signal=100, num=count, width=17, height=17)
        elif status == False:
            count += 1
            Graphics.wifi(draw, 130 + 33 * (count - 1), 1, signal=0, num=count, width=17, height=17)


# 该函数用于写入页脚的菜单选项，分为左侧右侧和中间三部分，对于中文支持自动计算位置，尽量不要使用英文
def write_foot(draw, h=10, left_text="确定", right_text="返回", center=""):
    f = 240 - 21
    font_width = 17
    if left_text:
        draw.text((2, f), left_text, font=font, fill="white")
    if right_text:
        draw.text((240 - font_width * len(right_text) - 2, f), right_text, font=font, fill="white")
    if center:
        draw.text((240 / 2 - font_width * len(center) / 2, f), center, font=font, fill="white")


# 等待释放按键，该函数可以设置等待时间，并且返回等待时间，用于判断按钮按的时间
# 一般用作菜单的上下调整，可根据按下时间快速切换，或设置关机键，长按关机
def wait_release(PIN, count=999999999999):
    _tcount = 0
    while GPIO.input(PIN) == 0 and count > 0:
        time.sleep(0.001)
        count -= 1
        _tcount += 1
    return _tcount


# 如果按下某个按键，直接等待按键结束，返回状态为是否按下
def wait_press(PIN):
    flag = False
    while GPIO.input(PIN) == 0:
        if not flag:
            flag = True
        time.sleep(0.001)
    return flag


# 判断是否按下某个按键
def press_key(PIN):
    return GPIO.input(PIN) == 0


# 该变量用于存储后台常刷的Wi-Fi列表(全局变量)
wifi_list = []

# 颜色变量
qianlan_color = "#75f4fd"


class Wifi:
    def __init__(self):
        self.scan_flag = True

    def get_interface(self):
        # ifconfig = os.popen("ifconfig").read()
        # ifconfig = map(lambda x: x[:-2], re.findall("[a-z0-9A-Z]*: ", ifconfig))
        iwconfig = os.popen("iwconfig 2>/dev/null | grep IEEE").read()
        iwconfig = filter(lambda x: bool(x), map(lambda x: x.split(" ")[0], iwconfig.split("\n")))
        # return ifconfig, iwconfig
        ret = {}
        for iface in iwconfig:
            r = re.search("^([a-z]*?\d+)mon$", iface)
            if r:  # 网卡处于监听模式
                iface = r.group(1)
            status = self.open(iface)
            if iface != "wlan0" and iface != "wlan0mon":  # wlan0网卡指定用来做互联网接入设备
                ret[iface] = status
        return ret

    def get_wifi_list(self):
        try:
            from urllib.parse import unquote
        except:
            from urlparse import unquote
        w_list = os.popen("sudo iw dev wlan0 scan | grep \"SSID: \"").read()
        ret = []
        for wifi in w_list.split("\n"):
            wifi = wifi.strip("\r\n\t ")
            if wifi:
                try:
                    log(3, repr(wifi))
                    wifi = unquote(wifi.split(": ", 1)[1].replace("\\x", "%").encode("utf-8").decode("unicode-escape"))
                    ret.append(wifi)
                except Exception as e:
                    print(e)
                    pass
        return ret

    def start_mon(self, iface):
        os.system("sudo airmon-ng start %s %smon &" % (iface, iface))

    def stop_mon(self, iface):
        os.system("sudo airmon-ng stop %smon &" % iface)

    def start_airodump(self):
        os.system("sudo /home/pi/start.sh &")
        self.scan_flag = True
        t = threading.Thread(target=self.parse_wifi)
        t.setDaemon(True)
        t.start()

    def stop_airodump(self):
        os.system("sudo killall -s 9 airodump-ng 2>/dev/null &")
        self.scan_flag = False

    def open(self, iface="wlan1"):
        if os.popen("iwconfig %smon 2>/dev/null | grep \"IEEE 802.11\"" % iface).read().strip():
            return True
        elif os.popen("iwconfig %s 2>/dev/null | grep \"IEEE 802.11\"" % iface).read().strip():
            return False
        else:
            return None

    def parse_wifi(self, filename="/home/pi/result-01.csv"):
        global wifi_list
        global current_wifi
        while self.scan_flag:
            try:
                flag = False
                wifison = {}

                wifi = []
                if not os.path.exists(filename):
                    continue
                for line in open(filename).readlines():
                    if not line.strip():
                        continue
                    line = line.strip().split(",")
                    if line[0] == 'BSSID':
                        flag = True
                        continue
                    elif line[0] == 'Station MAC':
                        flag = False
                        continue
                    if flag:
                        wifi.append(line)
                    else:
                        try:
                            def getvalue(s_mac, start_time, end_time, signal, pack_num, bssid, *essid):
                                return s_mac, start_time, end_time, signal, pack_num, bssid, essid

                            s_mac, start_time, end_time, signal, pack_num, bssid, essid = getvalue(*line)
                            if wifison.get(bssid.strip(), None):
                                entity = {}
                                entity["smac"] = s_mac.strip()
                                entity["start_time"] = start_time.strip()
                                entity["end_time"] = end_time.strip()
                                entity["signal"] = signal.strip()
                                entity["pack_num"] = pack_num.strip()
                                entity["bssid"] = bssid.strip()
                                if any(essid):
                                    entity["essid"] = ",".join(any(essid))
                                else:
                                    entity["essid"] = ""
                                wifison[bssid.strip()].append(entity)
                            else:
                                entity = {}
                                entity["smac"] = s_mac.strip()
                                entity["start_time"] = start_time.strip()
                                entity["end_time"] = end_time.strip()
                                entity["signal"] = signal.strip()
                                entity["pack_num"] = pack_num.strip()
                                entity["bssid"] = bssid.strip()
                                if any(essid):
                                    entity["essid"] = ",".join(any(essid))
                                else:
                                    entity["essid"] = ""
                                wifison[bssid.strip()] = [entity]
                        except Exception as e:
                            pass
                wifis = []
                for line in wifi:
                    try:
                        w = {}
                        mac, time1, time2, ch, _, crypt, _, _, power, _, _, _, _, name, essid = line
                        w['bssid'] = mac.strip()
                        w['ch'] = ch.strip()
                        w['privacy'] = crypt.strip()
                        w['distance'] = power.strip("\r\n ")
                        w['essid'] = name.strip()
                        w['client'] = wifison.get(mac, [])
                        wifis.insert(0, w)
                        if wifison.get(mac.strip(), []):
                            del wifison[mac]
                    except Exception as e:
                        pass
                wifi_list = wifis
                if current_wifi:
                    t = list(filter(lambda x: x['bssid'] == current_wifi['bssid'], wifi_list))
                    if t:
                        current_wifi = t[0]
                time.sleep(1)
            except Exception as e:
                import traceback
                traceback.print_exc()


wifi_obj = Wifi()
current_wifi = None


class Oled:

    def __init__(self, device):
        self.device = device
        self.ip = ""
        self.wifi = ""
        self.wifi_signal = {}
        self.display_level = 25
        self.msg_info = ("", "", "", "", "", "")
        t = threading.Thread(target=self.damon)
        t.setDaemon(True)
        t.start()
        # device.contrast(self.display_level * 10)

    # 统一刷新时间
    def sleep(self, time_):
        time.sleep(0.001)

    # 后台获取IP地址，网卡状态等信息
    def damon(self):  # 监听修改当前ip存在状态
        # 获取系统信息
        def get_info():
            cmd = "hostname -I | cut -d\' \' -f1"
            IP = subprocess.check_output(cmd, shell=True)
            cmd = "top -bn1 | grep load | awk '{printf \"CPU: %.f%%\", $(NF)*100}'"
            CPU = subprocess.check_output(cmd, shell=True)
            cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
            MemUsage = subprocess.check_output(cmd, shell=True)
            cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
            Disk = subprocess.check_output(cmd, shell=True)
            wifi = os.popen("iwconfig wlan0 | grep \"IEEE 802.11\"").read().strip()
            f = open("/sys/class/thermal/thermal_zone0/temp")
            c = f.read()
            f.close()
            c = "%0.2f" % (float(c) / 1000)
            r = re.search("ESSID:\"([^\"]*?)\"", wifi)
            if r:
                wifi = "WIFI: %s" % r.group(1)
            else:
                wifi = "WIFI Not Connect"
            return IP.decode("utf-8"), CPU.decode("utf-8"), MemUsage.decode("utf-8"), Disk.decode("utf-8"), wifi, c

        while True:
            try:
                self.wifi_signal = wifi_obj.get_interface()
                self.ip = os.popen("hostname -I").read().strip()
                self.msg_info = get_info()
            except:
                pass
            time.sleep(1)

    # 关机菜单实现
    def poweroff(self):
        log(3, "进入关机选项")
        menu_list = [
            "是",
            "否",
        ]
        menu_i = 0
        left = False
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "重启")
                self.write_menu(draw, menu_list, menu_i)
                if wait_press(ok_PIN) or wait_press(KEY_press_PIN):
                    # 判断当前选择，然后进入
                    if menu_i == 0:
                        draw.rectangle((0, 0, 240, 240), fill=0, outline=1)
                        draw.text((45, 23), "Bye,Bye", font=font, fill=1)
                        log(3, "再见，我亲爱的傻屌开发者")
                        time.sleep(2)
                        os.system("sudo reboot")
                        time.sleep(20)
                    elif menu_i == 1:
                        log(3, "返回")
                        return
                menu_i = self.key_Auto(menu_i, len(menu_list))

                if press_key(cancel_PIN):
                    wait_release(cancel_PIN)
                    return
            self.sleep(0.01)

    # Loader屏幕实现
    def wait(self, time_):  # 等待进程，并且显示loading
        with canvas(device) as draw:
            self.write_bg(draw, "等待中")
            self.write_head(draw)
            self.writr_area(draw, 7, 70, 220, 50, 16)
            draw.text((70, 85), "正在加载中...", font=font_m, fill="white")
        time.sleep(time_)

    # 写入头信息时间，配合后台线程实现
    def write_head(self, draw):  # 写入头信息
        write_header(draw, self.ip, self.wifi_signal)

    # 写入菜单选择的实现
    def write_menu(self, draw, menu_list=[], index=0, flag=True):
        list_entity = 8
        if index < list_entity:
            for menu_text, menu_i in zip(menu_list[:8], range(len(menu_list))):
                if index == menu_i:
                    # 浅色
                    self.writr_area(draw, 8, 27 + menu_i * 23, 219, 19, 18, "#55d4dd")
                else:
                    # 深色
                    self.writr_area(draw, 8, 27 + menu_i * 23, 219, 20, 18, "#375e94")
                draw.text((27, 27 + menu_i * 23), menu_text, font=font, fill="white")
        else:
            self.writr_area(draw, 8, 27 + 0 * 23, 219, 19, 18, "#375e94")
            draw.text((27, 27 + 0 * 23), menu_list[index - 7], font=font, fill="white")
            self.writr_area(draw, 8, 27 + 1 * 23, 219, 19, 18, "#375e94")
            draw.text((27, 27 + 1 * 23), menu_list[index - 6], font=font, fill="white")
            self.writr_area(draw, 8, 27 + 2 * 23, 219, 19, 18, "#375e94")
            draw.text((27, 27 + 2 * 23), menu_list[index - 5], font=font, fill="white")
            self.writr_area(draw, 8, 27 + 3 * 23, 219, 19, 18, "#375e94")
            draw.text((27, 27 + 3 * 23), menu_list[index - 4], font=font, fill="white")
            self.writr_area(draw, 8, 27 + 4 * 23, 219, 19, 18, "#375e94")
            draw.text((27, 27 + 4 * 23), menu_list[index - 3], font=font, fill="white")
            self.writr_area(draw, 8, 27 + 5 * 23, 219, 19, 18, "#375e94")
            draw.text((27, 27 + 5 * 23), menu_list[index - 2], font=font, fill="white")
            self.writr_area(draw, 8, 27 + 6 * 23, 219, 19, 18, "#375e94")
            draw.text((27, 27 + 6 * 23), menu_list[index - 1], font=font, fill="white")
            self.writr_area(draw, 8, 27 + 7 * 23, 219, 19, 18, "#55d4dd")
            draw.text((27, 27 + 7 * 23), menu_list[index - 0], font=font, fill="white")

    # 按钮上下对值修改的统一接口
    def key_up_down(self, current=0, length=0):
        if press_key(KEY_up_PIN):
            wait_release(KEY_up_PIN, 80)
            current = current - 1 if current > 0 else length - 1
        if press_key(KEY_down_PIN):
            wait_release(KEY_down_PIN, 80)
            current = current + 1 if current < length - 1 else 0
        if current >= length:
            current = length - 1
        if current < 0:
            current = 0
        return current

    # 按钮左右对值修改的统一接口
    def key_left_right(self, current=0, length=0):
        if press_key(KEY_left_PIN):
            wait_release(KEY_left_PIN, 80)
            current = current - 1 if current > 0 else length - 1
        if press_key(KEY_right_PIN):
            wait_release(KEY_right_PIN, 80)
            current = current + 1 if current < length - 1 else 0
        if current >= length:
            current = length - 1
        if current < 0:
            current = 0
        return current

    def key_Auto(self, current, length):
        current = self.key_up_down(current, length)
        current = self.key_left_right(current, length)
        return current

    # 键盘功能实现
    def keyBoard(self, current_text=""):
        log(3, "进入键盘")
        ret_str = ""
        if current_text:
            ret_str = current_text
        location = [0, 0]

        def write_char(draw, location):
            chars = [
                ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'a', 'b'],
                ['c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n'],
                ['o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'],
                ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
                ['M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X'],
                ['Y', 'Z', '`', '~', '!', '@', '#', '$', '%', '^', '&', '*'],
                ['(', ')', '_', '+', '-', '=', '{', '}', '|', '[', ']', '\\'],
                [':', '"', ';', "'", ',', '.', '/', '<', '>', '?', " ", " "]
            ]
            for line_no in range(len(chars)):
                line = chars[line_no]
                for ch_no in range(len(line)):
                    if location[1] == line_no and location[0] == ch_no:
                        self.writr_area(draw, ch_no * 18 + 11, 45 + line_no * 20, 16, 18, 5, "#55d4dd")
                    else:
                        self.writr_area(draw, ch_no * 18 + 11, 45 + line_no * 20, 16, 18, 5)
                    draw.text((ch_no * 18 + 15, 45 + line_no * 20), line[ch_no], font=font, fill="white")
            return chars[location[1]][location[0]]

        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "输入")
                write_foot(draw, center="删除")
                c = write_char(draw, location)
                draw.line((8, 42, 220, 42), fill="#75f4fd")
                draw.text((8, 20), "%s<-" % ret_str, font=font, fill="#75f4fd")

                # 方向键选择字符
                location[1] = self.key_up_down(location[1], 8)
                location[0] = self.key_left_right(location[0], 12)

                # K2 删除字符
                if press_key(main_PIN):
                    wait_release(main_PIN)
                    ret_str = ret_str[:-1] if ret_str else ""
                    draw.text((8, 20), "%s<- " % ret_str, font=font, fill="#75f4fd")
                    log(3, "键盘删除字符，删除后:%s" % ret_str)

                # 中键选择字符
                if press_key(KEY_press_PIN):
                    wait_release(KEY_press_PIN)
                    log(3, "键盘选择字符:%s" % c)
                    ret_str += c
                    draw.text((8, 20), "  " * (len(ret_str) + 3), font=font, fill="#75f4fd")
                    draw.text((8, 20), "%s<-" % ret_str, font=font, fill="#75f4fd")

                # K1 提交选择
                if press_key(ok_PIN):
                    wait_release(ok_PIN)
                    log(3, "返回字符串:%s" % ret_str)
                    return ret_str
                # K3 返回传入值
                if press_key(cancel_PIN):
                    wait_release(cancel_PIN)
                    log(3, "返回原字符串:%s" % current_text)
                    return current_text
            self.sleep(0.002)


    # 连接Wi-Fi的具体实现
    def wifi_connect(self):
        up = True
        log(3, "进入Wi-Fi连接功能")
        ssid = "MyWifi"
        password = "123456789"
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "连Wi-Fi")
                write_foot(draw, left_text="确定", center="扫描")
                # SSID和密码显示的模版
                draw.text((8, 30), "Wi-Fi 名称:", font=font, fill="white")
                draw.text((8, 80), "Wi-Fi 密码:", font=font, fill="white")
                draw.line((8, 70, 220, 70), fill="#75f4fd")
                draw.line((8, 120, 220, 120), fill="#75f4fd")

                # SSid和密码具体内容的显示
                if up:
                    draw.text((8, 50), "%s<-" % ssid, font=font, fill="white")
                    draw.text((8, 100), "%s" % password, font=font, fill="white")
                else:
                    draw.text((8, 50), "%s" % ssid, font=font, fill="white")
                    draw.text((8, 100), "%s<-" % password, font=font, fill="white")
                if press_key(ok_PIN):
                    wait_release(ok_PIN)
                    cmd = "/home/pi/connect_pi.sh wlan0 %s %s" % (ssid, password)
                    log(1, "执行连接Wi-Fi命令:%s" % cmd)
                    os.system(cmd)
                    return
                    # 判断当前选择，然后进入
                if press_key(KEY_press_PIN):
                    wait_release(KEY_press_PIN)
                    if up:
                        ssid = self.keyBoard(ssid)
                        log(3, "输入Wi-Fi名称:%s" % ssid)
                    else:
                        password = self.keyBoard(password)
                        log(3, "输入Wi-Fi密码:%s" % password)
                if wait_press(main_PIN):
                    self.wait(0.1)
                    ssid = self.wifi_connect_list() or ssid

                if wait_press(KEY_up_PIN) or wait_press(KEY_down_PIN):
                    up = not up
                self.write_head(draw)
                if wait_press(cancel_PIN):
                    log(3, "返回")
                    return
            self.sleep(0.01)

    # Wi-Fi连接时的扫描可见Wi-Fi
    def wifi_connect_list(self):  # 扫描当前Wi-Fi并且选择
        log(3, "进入Wi-Fi连接展示列表")
        connect_list = wifi_obj.get_wifi_list()
        list_i = 0
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "结果")
                write_foot(draw, left_text="选择", center="重新扫描")
                self.write_menu(draw, connect_list, list_i)
                if wait_press(KEY_press_PIN) or wait_press(ok_PIN):
                    log(3, "选择Wi-Fi:%s" % connect_list[list_i])
                    return connect_list[list_i]

                list_i = self.key_Auto(list_i, len(connect_list))
                if wait_press(main_PIN):
                    log(3, "重新扫描Wi-Fi列表")
                    list_i = 0
                    self.wait(0.1)
                    connect_list = wifi_obj.get_wifi_list()
                self.write_head(draw)
                if wait_press(cancel_PIN):
                    log(3, "取消选择")
                    return ""

    # Wi-Fi菜单的实现
    def wifi_menu(self):
        log(3, "进入Wi-Fi菜单")
        menu_list = [
            "连接 WIFI",
            "测试键盘",
        ]
        menu_i = 0
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "信息")
                self.write_menu(draw, menu_list, menu_i)
                write_foot(draw, left_text="确定")
                if wait_press(ok_PIN) or wait_press(KEY_press_PIN):
                    # 判断当前选择，然后进入
                    if menu_i == 0:
                        self.wifi_connect()
                    elif menu_i == 1:
                        os.system(self.keyBoard())
                menu_i = self.key_Auto(menu_i, len(menu_list))
                self.write_head(draw)
                if wait_press(cancel_PIN):
                    log(3, "返回")
                    return

            self.sleep(0.01)

    # 设置菜单的实现
    def settings(self):
        log(3, "进入设置")

        menu_list = [
            "亮度设置"
        ]
        menu_i = 0
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "设置")
                self.write_menu(draw, menu_list, menu_i)
                write_foot(draw, left_text="确定")
                if wait_press(ok_PIN) or wait_press(KEY_press_PIN):
                    if menu_i == 0:
                        self.settings_Lcd()
                if wait_press(cancel_PIN):
                    log(3, "返回")
                    return
                menu_i = self.key_Auto(menu_i, len(menu_list))
                self.write_head(draw)

    # 设置OLED亮度
    def settings_Lcd(self):  # 设置亮度界面
        log(3, "设置OLED亮度")
        tml_dl = self.display_level
        menu_list = [
            "亮度",
        ]
        menu_i = 0
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "背光")
                self.write_menu(draw, menu_list, menu_i)
                write_foot(draw, left_text="确定")
                device.contrast(tml_dl * 10)
                draw.text((127, 27), "%s" % tml_dl, font=font, fill="white")
                if press_key(ok_PIN) or press_key(KEY_press_PIN):
                    self.display_level = tml_dl
                    device.contrast(self.display_level * 10)
                    wait_release(KEY_press_PIN)
                    wait_release(ok_PIN)
                    log(3, "保存亮度设置:%s" % self.display_level)
                    return
                if press_key(cancel_PIN):
                    device.contrast(self.display_level * 10)
                    wait_release(cancel_PIN)
                    log(3, "取消设置，原设置亮度:%s" % self.display_level)
                    return
                if press_key(KEY_left_PIN):
                    tml_dl = tml_dl - 1 if tml_dl > 0 else 0
                    wait_release(KEY_left_PIN, 100)
                if press_key(KEY_right_PIN):
                    tml_dl = tml_dl + 1 if tml_dl < 25 else 25
                    wait_release(KEY_right_PIN, 100)
                self.write_head(draw)
            self.sleep(0.01)


    def wait_select(self, title="", selects=[]):
        log(3, "进入通用选择菜单")
        i = 0
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, title)
                self.write_head(draw)
                write_foot(draw, left_text="选择", right_text="取消")
                # 通用菜单选择项调整
                i = self.key_Auto(i, len(selects))
                # 写菜单到显示器
                self.write_menu(draw, selects, i)

                # 选择当前选择项
                if wait_press(ok_PIN) or wait_press(KEY_press_PIN):
                    log(3, "当前选择的选项为:%s " % selects[i])
                    return i
                if press_key(cancel_PIN):
                    wait_release(cancel_PIN)
                    log(3, "返回")
                    return -1

    # 主菜单的实现
    def menu(self):
        log(3, "进入主菜单")
        menu_list = ["系统信息", "Wi-Fi", "系统设置", "重启"]
        menu_i = 0
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "主菜单")
                self.write_head(draw)
                self.write_menu(draw, menu_list, menu_i)
                write_foot(draw, left_text="确定")
                if wait_press(KEY_press_PIN) or wait_press(ok_PIN):
                    if menu_i == 0:
                        self.msg()
                    elif menu_i == 1:
                        self.wifi_menu()
                    elif menu_i == 2:
                        self.settings()
                    elif menu_i == 3:
                        # os.system("sudo poweroff")
                        # return
                        self.poweroff()
                menu_i = self.key_Auto(menu_i, len(menu_list))
                if press_key(cancel_PIN):
                    wait_release(cancel_PIN)
                    log(3, "返回")
                    return
                # self.write_head(draw)
            self.sleep(0.01)

    def write_bg(self, draw, info):
        draw.rectangle((0, 0, 240, 240), fill="#1d232a")
        # 外侧浅蓝色背景宽度
        line_width = 2
        # 画出浅蓝色外层
        draw.polygon(
            [(0, 0),
             (90, 0),
             (110, 20),
             (215, 20),
             (235, 40),
             (235, 215),
             (20, 215),
             (0, 195),
             (0, 0)],
            fill="#75f4fd")
        # 画出深蓝色内层
        draw.polygon(
            [(line_width, line_width),
             (90 - line_width, line_width),
             (110 - line_width, 20 + line_width),
             (215 - line_width, 20 + line_width),
             (235 - line_width, 40 + line_width),
             (235 - line_width, 215 - line_width),
             (20 + line_width, 215 - line_width),
             (line_width, 195 - line_width),
             (line_width, line_width)],
            outline="#75f4fd", fill="#132238")

        # 两个反斜杠
        draw.polygon([(83, 8), (88, 8), (98, 18), (93, 18)], fill="#75f4fd")
        draw.polygon([(73, 8), (78, 8), (88, 18), (83, 18)], fill="#75f4fd")
        # 右上，左下，两个角的颜色
        draw.polygon([(220, 20), (235, 20), (235, 35)], fill="#75f4fd")
        # draw.polygon([(0, 200), (0, 215), (15, 215)], fill="#75f4fd")

        # 界面左侧菜单名称前图标
        draw.rectangle((6, 6, 18, 20), fill="#e2fa70")
        draw.polygon([(8, 8), (16, 8), (16, 18), (8, 18), (8, 16), (14, 14), (14, 12), (8, 10), (14, 10), (14, 8)],
                     fill="#132238")

        # 菜单文字
        draw.text((20, 4), info, font=font, fill="#75f4fd")
        # 上方右侧小时间
        draw.text((193, 1), time.strftime("%H:%M", time.localtime()), font=font_head, fill="white")

    def writr_area(self, draw, left=5, top=20, width=0, height=0, p=10, color="#375e94"):
        draw.polygon(
            [(left, top), (left + width - p, top), (left + width, top + p), (left + width, top + height),
             (left + p, top + height), (left, top + height - p), (left, top)],
            fill=color)

    # 主机信息展示页面
    def msg(self):
        log(3, "进入系统信息")
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "信息")
                self.write_head(draw)
                write_foot(draw)
                ip, cpu, mem, disk, wifi, c = self.msg_info
                self.writr_area(draw, 8, 27, 219, 180, 16, "#375e94")
                draw.text((10, 20 + 12), "IP: %s" % ip, font=font, fill="white")
                draw.text((10, 20 + 32), "温度: %s °C" % c, font=font, fill="white")
                draw.text((10, 20 + 52), cpu, font=font, fill="white")
                draw.text((10, 20 + 72), mem, font=font, fill="white")
                draw.text((10, 20 + 92), disk, font=font, fill="white")
                draw.text((10, 20 + 112), wifi, font=font, fill="white")
                if press_key(cancel_PIN) or press_key(KEY_press_PIN):
                    wait_release(cancel_PIN)
                    wait_release(KEY_press_PIN)
                    log(3, "返回")
                    return
            self.sleep(0.01)

    # 主页面
    def main(self):
        log(3, "进入主线程,显示主页面")
        while True:
            with canvas(device) as draw:
                self.write_bg(draw, "首页")
                self.write_head(draw)
                write_foot(draw, left_text="菜单", right_text="系统信息")
                # 时间背后的方块背景
                draw.polygon(
                    [(50, 46), (180, 46), (190, 56), (190, 116), (60, 116), (50, 106), (50, 46)],
                    fill="#375e94")
                # 时间日期显示
                draw.text((63, 46), time.strftime("%H:%M", time.localtime()), font=font_b, fill="#FFFFFF")
                draw.text((74, 94), time.strftime("%Y-%m-%d", time.localtime()), font=font, fill="#FFFFFF")
                self.writr_area(draw, 8, 143, 220, 37, 30)
                draw.text((67, 144), "微雪电子", font=font_b_c, fill="#75f4fd")

                if press_key(main_PIN):
                    rc = wait_release(main_PIN)
                    log(3, "主界面按下main按钮,时间:%s 毫秒(不准确)" % rc)
                    if rc > 1000:
                        self.poweroff()
                if wait_press(ok_PIN) or wait_press(KEY_press_PIN):
                    self.menu()
                if wait_press(cancel_PIN):
                    self.msg()
            self.sleep(0.01)


wifi_obj.stop_airodump()

while True:
    try:
        log(3, "开始运行")
        Oled(device).main()
    except (SystemExit, KeyboardInterrupt) as e:
        break
    except Exception as e:
        import traceback

        traceback.print_exc()
        log(4, "出现了一点问题:", traceback.format_exc())

GPIO.cleanup()
