#!user/bin/env python3
# -*- coding: UTF-8 -*-
import requests
import json
from station_names import station_names
from prettytable import PrettyTable
import urllib.parse
import re
import time
import pickle
import datetime

def get_city_code(city_name_x):
    # 制作包含各个城市的字典,city_name['BXP']输出城市站点名,city_code['北京']输出城市三字码
    city_name = {}
    city_code = {}
    for i in station_names.split('@'):
        if i:
            city_code[i.split('|')[1]] = i.split('|')[2]  # 1为城市名，2为城市三字码
    return city_code[city_name_x]


def get_city_name(city_code_x):
    # 制作包含各个城市的字典,city_name['BXP']输出城市站点名,city_code['北京']输出城市三字码
    city_name = {}
    city_code = {}
    for i in station_names.split('@'):
        if i:
            city_name[i.split('|')[2]] = i.split('|')[1]
    return city_name[city_code_x]


def getList():
    url = 'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=' + date_tour + '&leftTicketDTO.from_station=' + station_start + '&leftTicketDTO.to_station=' + station_arrive + '&purpose_codes=ADULT'
    print(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
    }

    html = requests.get(url, headers=headers)
    print(html.status_code)
    results = html.json()
    return results['data']['result']


def output_info():
    table = PrettyTable(['车次', '出发站名', '到达站名', '出发时间', '到达时间', '一等座', '二等座', '硬座', '硬卧'])
    results = getList()
    train_info = {}
    for result in results:
        xx = result.split('|')
        #数据结构详细：secretstr  |  预订 | 24000014611T | 1461 | BJP | SHH | BJP | XCH | 11: 54 | 22:47 | 10: 53 |
        #数据结构详细：          |       |  详细车次 | 车次 | 始发 | 终到| 从哪| 到哪| 发时   |  到时  |  历时  |
        # print(xx)
        # 序号30,31,32分别为高铁的二等座，一等座，特等座
        # 序号23,26,28,29分别为普通车次的软卧，无座，硬卧，硬座
        if (xx[0]):
            secert_str = urllib.parse.unquote(xx[0])
            train_number = xx[3]
            start_station = get_city_name(xx[6])
            arrive_station = get_city_name(xx[7])
            start_time = xx[8]
            arrive_time = xx[9]
            first_seats = xx[31]
            second_seats = xx[30]
            hard_seats = xx[29]
            hard_berth = xx[28]
            train_info[train_number] = {
                'secert_str_info': secert_str,
                'train_code_info': xx[2],
                'from_station_code': xx[6],
                'to_station_code': xx[7],
                'hard_berth': hard_berth,
                'hard_seats': hard_seats,
            }
            table.add_row(
                [train_number, start_station, arrive_station, start_time, arrive_time, first_seats, second_seats,
                 hard_seats, hard_berth])
        else:
            pass
    print(table)
    return train_info

def get_codeimg():
    response = requests.get(captcha_img)
    img_data = response.content
    with open('xx.jpg','wb') as f:
        f.write(img_data)
    cookies = response.cookies
    return cookies

#获取验证码坐标----通过获取用户输入的序号，获得包含验证码坐标的列表
def get_code_coordinate(code_number):
    code_number = code_number.split(',')
    # 验证码坐标集
    code_list = ['35,38', '112,38', '188,44', '261,43', '36,117', '110,114', '186,117', '260,118']
    code = []
    for i in code_number:
        code.append(code_list[int(i)])
    codes = ','.join(code)
    return codes

def check_code():
    code_coordinate = get_code_coordinate(code_number)
    print('此次提交的验证码坐标为：', code_coordinate)
    # 验证码提交的form数据
    captcha_data = {
        'answer': code_coordinate,
        'login_site': 'E',
        'rand': 'sjrand',
    }
    captcha_result = requests.post(captcha_url, cookies=cookies, data=captcha_data)
    captcha_result_json = captcha_result.json()
    captcha_result_code = captcha_result_json['result_code']
    print('验证码验证结果result_code为',captcha_result_code)
    return captcha_result_code

def login():
    # 验证码验证成功后，用户登录页面提交的form数据
    user_data = {
        'username': '',#请输入12306用户名
        'password': '',#请输入12306密码
        'appid': 'otn',
    }
    response1 = requests.post(login_url, data = user_data, cookies = cookies)
    new_cookies = response1.cookies
    response1 = response1.json()
    result_message = response1['result_message']
    print('用户名密码已经已经验证,其结果为result_message is:',result_message)

    tk_url = 'https://kyfw.12306.cn/passport/web/auth/uamtk'
    tk_data = {
        'appid': 'otn'
    }
    response3 = requests.post(tk_url, data= tk_data, cookies = new_cookies)
    response3 = response3.json()
    print(response3)
    newapptk = response3['newapptk']
    auth_data = {
           'tk': newapptk,
    }

    auth_url = 'https://kyfw.12306.cn/otn/uamauthclient'
    response4 = requests.post(auth_url, data=auth_data, cookies = new_cookies)
    new_cookies2 = response4.cookies
    response4 = response4.json()
    print(response4)
    return new_cookies2



def check_user():
    check_url = 'https://kyfw.12306.cn/otn/login/checkUser'
    check_data = {
        '_json_att': '',
    }
    response = requests.post(check_url, data=check_data, cookies=login_cookie)


def submit_order(train_no):
    submit_url = 'https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest'
    submit_data = {
        'secretStr': train_info[train_no]['secert_str_info'],
        'train_date': date_tour,
        'back_train_date': back_date,
        'tour_flag': 'dc',
        'purpose_codes': 'ADULT',
        'query_from_station_name': city_start,
        'query_to_station_name': city_arrive,
        'undefined': '',
    }
    response = requests.post(submit_url, data=submit_data, cookies=login_cookie)
    print('the secret number is:', train_info[train_no]['secert_str_info'])
    print(response.text)


def init_dc():
    init_url = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
    init_data = {
        '_json_att': '',
    }
    response = requests.post(init_url, data = init_data, cookies=login_cookie)
    pattern1 = re.compile("globalRepeatSubmitToken.*?'(.*?)';")
    #pattern1 = re.compile(r"var globalRepeatSubmitToken = '(.*)'")
    submit_token = pattern1.findall(response.text)
    pattern2 = re.compile('ticketInfoForPassengerForm={(.*?)};')
    ticket_info_for_passenger = pattern2.findall(response.text)
    pattern3 = re.compile("'leftTicketStr':'(.*?)'")
    left_ticket_str = pattern3.findall(response.text)
    pattern4 = re.compile("'key_check_isChange':'(.*?)'")
    key_check_is = pattern4.findall(response.text)
    pattern5 = re.compile("'train_location':'(.*?)'")
    train_location = pattern5.findall(response.text)
    #ticket_info_for_passenger = ticket_info_for_passenger.replace("'", "\"")
    if submit_token and ticket_info_for_passenger:
        print('submit_token, ticket_info_for_passenger获取成功')
    return submit_token, ticket_info_for_passenger, left_ticket_str, key_check_is, train_location

def get_passengers(submit_token):
    passenger_url ='https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
    passenger_data =  {
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': submit_token,
    }
    response = requests.post(passenger_url, data = passenger_data, cookies=login_cookie)
    response = response.json()
    passengers_list = response['data']['normal_passengers']
    if passengers_list:
        print('passenger_list 获取成功！')
    return passengers_list


# 获取用户信息
def get_passengers_info():
    '''
    passengers_list = str(passengers_list)
    passengers_list = passengers_list.replace("'","\"")
    # 提取姓名
    name_pat = '"passenger_name":"(.*?)"'
    # 提取身份证
    id_pat = '"passenger_id_no":"(.*?)"'
    # 提取手机号
    mobile_pat = '"mobile_no":"(.*?)"'
    # 提取对应乘客所在的国家
    country_pat = '"country_code":"(.*?)"'
    name_all = re.compile(name_pat).findall(passengers_list)
    id_all = re.compile(id_pat).findall(passengers_list)
    mobile_all = re.compile(mobile_pat).findall(passengers_list)
    country_all = re.compile(country_pat).findall(passengers_list)
    '''
    passengers_list = get_passengers(submit_token)
    name_all =[]
    id_all = []
    mobile_all =[]
    country_all =[]
    for single in passengers_list:
        name_all.append(single['passenger_name'])
        id_all.append(single['passenger_id_no'])
        mobile_all.append(single['mobile_no'])
        country_all.append(single['country_code'])
    return name_all, id_all, mobile_all, country_all

#下单环节第一步，确认订单信息
def check_order_info():
    check_order_url = 'https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo'
    check_order_data = {
        'cancel_flag': 2,#ticket_info_for_passenger['orderRequestDTO']['cancel_flag'] or '2'
        'bed_level_order_num': 000000000000000000000000000000,#ticket_info_for_passenger['orderRequestDTO']['bed_level_order_num'] or '000000000000000000000000000000',
        'passengerTicketStr': '1,0,1,'+str(name_all[choose_no])+',1,'+str(id_all[choose_no])+','+str(mobile_all[choose_no])+',N',
        #passengerTicketStr这个参数的组合方式为：1(seatType),0,1(车票类型:ticket_type_codes),张三(passenger_name),1(证件类型:passenger_id_type_code),320xxxxxx(passenger_id_no),151xxxx(mobile_no),N
        #如果有多个乘客，那么各个乘客之间用一个_分隔：seatType,0,ticket_type_codes,xxxx,mobile_no,N_seatType,0,ticket_type_codes,xxxx,mobile_no,N
        #seatType是代表座位性质的参数，商务座(9),特等座(P),一等座(M),二等座(O),高级软卧(6),软卧(4),硬卧(3),软座(2),硬座(1),无座(1)
        #random = 1512295210042
        'oldPassengerStr': str(name_all[choose_no])+',1,'+str(id_all[choose_no])+',1_',
        #oldPassengerStr这个参数的组合方式为：张三(passenger_name),1(证件类型:passenger_id_type_code),320xxxxxx(passenger_id_no),1_
        #如果有多个乘客，那么直接拼接到后面就可以了：name,1,identity,1_name2,1,identity2,1_
        'tour_flag': 'dc',#ticket_info_for_passenger['tour_flag'] or 'dc'
        'randCode': '',
        'whatsSelect': 1,
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': submit_token,
    }
    response = requests.post(check_order_url, data = check_order_data, cookies=login_cookie)
    response = response.json()
    print('check_order_info result is:',response)
    return response

#下单第二步，获取余票和排队信息
def get_greentime(date_tour):
    date_tour = datetime.datetime.strptime(date_tour, "%Y-%m-%d").date()
    # 再转为对应的格林时间
    gmt = '%a %b %d %Y 00:00:00 GMT+0800'
    date_tour_gmt = date_tour.strftime(gmt)+ ' (中国标准时间)'
    return date_tour_gmt

def get_queue_count(date_tour_gmt):
    queue_url = 'https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount'
    queue_data = {
        'train_date': str(date_tour_gmt),
        'train_no': train_info[train_no]['train_code_info'],
        'stationTrainCode': train_no,
        'seatType': 1,
        'fromStationTelecode': train_info[train_no]['from_station_code'],
        'toStationTelecode': train_info[train_no]['to_station_code'],
        'leftTicket': left_ticket_str,
        'purpose_codes':  00,
        'train_location': train_location,
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': submit_token,
    }
    response = requests.post(queue_url, data = queue_data, cookies = login_cookie)
    queue_msg = response.json()
    queue_count = queue_msg['data']['count']#当前排队人数
    queue_ticket = queue_msg['data']['ticket']#当前剩余票数
    print('您前面还有',queue_count,'人在排队','当前还有余票',queue_ticket,'张')
    print('get_queue_count result is:',response.text)

#下单第三步，订单入队确认
def confirm_queue():
    confirm_queue_url = 'https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue'
    confirm_queue_data = {
        "passengerTicketStr": "1,0,1," + str(name_all[choose_no]) + ",1," + str(id_all[choose_no]) + "," + str(mobile_all[choose_no]) + ",N",
        "oldPassengerStr": str(name_all[choose_no]) + ",1," + str(id_all[choose_no]) + ",1_",
        "tour_flag": "dc",
        "randCode": "",
        "purpose_codes": "00",
        "key_check_isChange": key_check_is,
        "leftTicketStr": left_ticket_str,
        "train_location": train_location,
        "choose_seats": "",
        "seatDetailType": "000",
        "whatsSelect": "1",
        "roomType": "00",
        "dwAll": "N",
        "_json_att": "",
        "REPEAT_SUBMIT_TOKEN": submit_token,
    }
    response = requests.post(confirm_queue_url, data = confirm_queue_data, cookies = login_cookie)
    print('confirm queue result is:',response.text)

#获取下单结果,如订单号：orderid
def query_order(time_stamp):
    order_id_url = 'https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime'
    order_id_data = {
        'random': time_stamp,
        'tourFlag': 'dc',
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': submit_token,
    }
    response = requests.post(order_id_url, data = order_id_data, cookies = login_cookie)
    query_order_result = response.json()
    print('查询订票id的结果是:',response.text)
    query_order_id = query_order_result['data']['orderId']
    return query_order_id

#查询这个订单号是不是最终成功下单
def result_order_queue():
    result_url = "https://kyfw.12306.cn/otn/confirmPassenger/resultOrderForDcQueue"
    result_data = {
        "orderSequence_no=" : query_order_id,
        "_json_att": "",
        "REPEAT_SUBMIT_TOKEN" : submit_token,
    }
    response = requests.post(result_url, data = result_data, cookies = login_cookie)
    print('查询订单是否订购成功:',response.text)

#获取订单详细信息：queryMyOrderNoComplete
def query_my_order_no():
    query_my_order_url = 'https://kyfw.12306.cn/otn/queryOrder/queryMyOrderNoComplete'
    query_my_order_data = {
        '_json_att': '',
    }
    response = requests.post(query_my_order_url, data = query_my_order_data, cookies = login_cookie)
    print('查询我的订单详细结果为：',response.text)

def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)


def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

if __name__ == "__main__":

    # 登录地址
    login_url = 'https://kyfw.12306.cn/passport/web/login'
    # 验证码验证地址
    captcha_url = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
    # 验证码图片地址
    captcha_img = 'https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand'
    while True:
        cookies = get_codeimg()
        code_number = input('请输入验证码序号，范围从0~7，用","隔开：')
        captcha_result_code = check_code()
        if captcha_result_code == '4':
            print('____验证码验证成功____')
            break
        else:
            print('____验证码未通过____')
            continue
    login_cookie = login()
    # save登录后的cookies
    filename = '12306_cookie.txt'
    save_cookies(login_cookie, filename)
    # 1、load cookies and do a request
    #2、login_cookie = load_cookies(filename)
    #3、print('login_cookie is:', login_cookie)
    city_start = input("请输入始发车站：")
    station_start = get_city_code(city_start)
    city_arrive = input("请输入到达车站:")
    station_arrive = get_city_code(city_arrive)
    date_tour = input("请输入出发日期，格式如2018-01-01")
    back_date = time.strftime("%Y-%m-%d", time.localtime())
    train_info = output_info()
    train_no = input('请输入预定车次：')
    while True:
        train_info = output_info()
        if train_info[train_no]['hard_seats']:
            print('当前有余票，正在下单')
            break
        else:
            continue
    # 订票环节
    submit_order(train_no)
    submit_token, ticket_info_for_passenger, left_ticket_str, key_check_is, train_location = init_dc()
    name_all, id_all, mobile_all, country_all = get_passengers_info()
    # # 输出乘客信息，由于可能有多位乘客，所以通过循环输出
    print('总共有'+str(len(name_all))+'位用户')
    for i in range(0, len(name_all)):
        print("第" + str(i) + "位用户,姓名:" + str(name_all[i]))

    # 选择乘客
    choose_no = int(input("请输入用户序号，此处只能选择一位:"))
    check_order_info()
    date_tour_gmt =get_greentime(date_tour)#将车票乘车时间转换为标准时间格式
    get_queue_count(date_tour_gmt)
    confirm_queue()
    while True:
        time_stamp = '%10d' % (time.time() * 1000)  # 获取当前时间的时间戳
        query_order_id = query_order(time_stamp)
        if query_order_id:
            print('____获取订单号成功，订单号为：',query_order_id)
            break
        else:
            print('____获取订单号未成功____')
            continue
    result_order_queue()
