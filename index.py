import sys
import requests
import random
import config
from time import localtime
from datetime import datetime, date
from zhdate import ZhDate
import template


def get_love_day(today, config_data):
    # 获取在一起的日子的日期格式
    love_year = int(config_data["love_date"].split("-")[0])
    love_month = int(config_data["love_date"].split("-")[1])
    love_day = int(config_data["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    # 获取在一起的日期差
    love_days = str(today.__sub__(love_date)).split(" ")[0]
    return love_days


def get_date():
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    today_week = "{} {}".format(today, week)
    return today, today_week, year


def get_weather(region, config_data):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    key = config_data["weather_key"]
    region_url = "https://geoapi.qweather.com/v2/city/lookup?location={}&key={}".format(region, key)
    response = requests.get(region_url, headers=headers).json()
    if response["code"] == "404":
        print("推送消息失败，请检查地区名是否有误！")
        sys.exit(1)
    elif response["code"] == "401":
        print("推送消息失败，请检查和风天气key是否正确！")
        sys.exit(1)
    else:
        # 获取地区的location--id
        location_id = response["location"][0]["id"]
    weather_url = "https://devapi.qweather.com/v7/weather/now?location={}&key={}".format(location_id, key)
    response = requests.get(weather_url, headers=headers).json()
    # 天气
    weather = response["now"]["text"]
    # 当前温度
    temp = response["now"]["temp"] + u"\N{DEGREE SIGN}" + "C"
    # 风向
    wind_dir = response["now"]["windDir"]
    # 获取逐日天气预报
    url = "https://devapi.qweather.com/v7/weather/3d?location={}&key={}".format(location_id, key)
    response = requests.get(url, headers=headers).json()
    # 最高气温
    max_temp = response["daily"][0]["tempMax"] + u"\N{DEGREE SIGN}" + "C"
    # 最低气温
    min_temp = response["daily"][0]["tempMin"] + u"\N{DEGREE SIGN}" + "C"
    # 日出时间
    sunrise = response["daily"][0]["sunrise"]
    # 日落时间
    sunset = response["daily"][0]["sunset"]
    url = "https://devapi.qweather.com/v7/air/now?location={}&key={}".format(location_id, key)
    response = requests.get(url, headers=headers).json()
    if response["code"] == "200":
        # 空气质量
        category = response["now"]["category"]
        # pm2.5
        pm2p5 = response["now"]["pm2p5"]
    else:
        # 国外城市获取不到数据
        category = ""
        pm2p5 = ""
    id = random.randint(1, 16)
    url = "https://devapi.qweather.com/v7/indices/1d?location={}&key={}&type={}".format(location_id, key, id)
    response = requests.get(url, headers=headers).json()
    proposal = ""
    if response["code"] == "200":
        proposal += response["daily"][0]["text"]
    return weather, temp, max_temp, min_temp, wind_dir, sunrise, sunset, category, pm2p5, proposal


def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 获取农历生日的生日
        try:
            year_date = ZhDate(year, r_mouth, r_day).to_datetime().date()
        except TypeError:
            print("请检查生日的日子是否在今年存在")
            sys.exit(1)

    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    if today > year_date:
        if birthday_year[0] == "r":
            # 获取农历明年生日的月和日
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day


def get_birth_data(year, config_data, today):
    # 获取所有生日数据
    birthdays = {}
    for k, v in config_data.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    birthday_dict = {}
    for key, value in birthdays.items():
        # 获取距离下次生日的时间
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = "今天{}生日哦，祝{}生日快乐！".format(value["name"], value["name"])
        else:
            birthday_data = "距离{}的生日还有{}天".format(value["name"], birth_day)
        birthday_dict[key] = birthday_data
    return birthday_dict


def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    r = requests.get(url, headers=headers)
    note_en = r.json()["content"]
    note_ch = r.json()["note"]
    return note_ch, note_en


def get_tianhang(config_data):
    try:
        key = config_data["tian_api"]
        url = "http://api.tianapi.com/caihongpi/index?key={}".format(key)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'Content-type': 'application/x-www-form-urlencoded'

        }
        response = requests.get(url, headers=headers).json()
        if response["code"] == 200:
            chp = response["newslist"][0]["content"]
        else:
            chp = ""
    except KeyError:
        chp = ""
    return chp


def replace_txt(txt, weather, temp, max_temp, min_temp, wind_dir, sunrise, sunset, category, pm2p5, proposal, region,
                today_week, love_days, birthday_data, chp, note_ch, note_en):
    txt = txt.replace("region", region)
    txt = txt.replace("date", today_week)
    txt = txt.replace("weather", weather)
    txt = txt.replace("min_temp", min_temp)
    txt = txt.replace("max_temp", max_temp)
    txt = txt.replace("temp", temp)
    txt = txt.replace("wind_dir", wind_dir)
    txt = txt.replace("pm2p5", pm2p5)
    txt = txt.replace("pm_emoji", "")
    txt = txt.replace("category", category)
    txt = txt.replace("ca_emoji", "")
    txt = txt.replace("sunrise", sunrise)
    txt = txt.replace("sunset", sunset)
    txt = txt.replace("proposal", proposal)
    txt = txt.replace("love_day", love_days)
    txt = txt.replace("birthday1", birthday_data["birthday1"])
    txt = txt.replace("birthday2", birthday_data["birthday2"])
    txt = txt.replace("chp", chp)
    txt = txt.replace("note_ch", note_ch)
    txt = txt.replace("note_en", note_en)

    return txt


def get_access_token(config_data):
    # 企业 corp_id
    corp_id = config_data["corp_id"]
    # secret
    secret = config_data["secret"]
    # access_token
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}".format(corp_id, secret)
    r = requests.get(url).json()
    if r["errcode"] == 0:
        accessToken = r["access_token"]
    else:
        print("获取access_token失败，请检查corp_id和secret是否正确")
        sys.exit(1)
    return accessToken


def send_message(access_token, description, to_user, config_data):
    send_message_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(access_token)

    data = {
        "touser": to_user,
        "msgtype": "textcard",
        "agentid": config_data["agent_id"],
        "textcard": {
            "title": config_data["title"],
            "description": description,
            "url": "weixin.qq.com/download",
            "btntxt": "详情"
        },
        "enable_id_trans": 0,
        "enable_duplicate_check": 0,
        "duplicate_check_interval": 1800
    }
    r = requests.post(send_message_url, json=data).json()
    if r["errcode"] == 0:
        print("推送消息成功！")
    elif r["errcode"] == 60020:
        print("推送消息失败！ip未加入白名单")
        sys.exit(1)
    else:
        print("推送消息失败！")
        print(r)
        sys.exit(1)


def main_handler(event, context):
    config_data = config.data
    # 获取accessToken
    accessToken = get_access_token(config_data)
    # 获取日期
    today, today_week, year = get_date()
    # 传入地区获取天气信息
    region = config_data["region"]
    weather, temp, max_temp, min_temp, wind_dir, sunrise, sunset, category, pm2p5, proposal = get_weather(region,
                                                                                                          config_data)
    # 获取在一起的日期差
    love_days = get_love_day(today, config_data)
    note_ch = config_data["note_ch"]
    note_en = config_data["note_en"]
    if note_ch == "" and note_en == "":
        # 获取词霸每日金句
        note_ch, note_en = get_ciba()
    chp = get_tianhang(config_data)
    # 获取生日数据
    birthday_data = get_birth_data(year, config_data, today)
    # 替换模板内容
    txt = template.txt
    description = replace_txt(txt, weather, temp, max_temp, min_temp, wind_dir, sunrise, sunset, category, pm2p5,
                              proposal, region, today_week, love_days, birthday_data, chp, note_ch, note_en)
    try:
        to_user = config_data["to_user"] 
        if to_user == "":
            to_user = "@all"
    except KeyError:
        to_user = "@all"
    # 发送消息
    send_message(accessToken, description, to_user, config_data)
