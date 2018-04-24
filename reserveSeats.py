import requests
# import aiohttp
# import asyncio


class WhuLibReserv():
    stu_id = ''
    pwd = ''
    token = ''
    headers = {
            'user-agent': 'Dalvik/2.1.0 (Linux; U; Android 7.0; SM-G9250 Build/NRD90M)',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    host = 'https://seat.lib.whu.edu.cn:8443'

    def __init__(self, stu_id, pwd):
        """
        :param stu_id: student id used to login
        :type stu_id: str
        :param pwd: student password w.r.t stu_id
        :type pwd: str
        :return:
        """
        self.stu_id = stu_id
        self.pwd = pwd

    @staticmethod
    def time_to_minute(time):
        """
        trans time to minute eg. 16:00 -> 960
        :param time: format: hh:mm
        :type time: str
        :return :
        :rtype : int
        """

        time = time.split(':')
        hh, mm = int(time[0]), int(time[1])
        return 60*hh + mm

    def login(self):
        """
        login using self.stu_id and self.pwd, got token from server
        :param:
        :return login_status: true as success false as failure
        :rtype login_status: bool
        """
        url = '%s/rest/auth' % self.host
        headers = self.headers

        payload = {
            'username': self.stu_id,
            'password': self.pwd
        }

        login_request = requests.get(url=url, headers=headers, params=payload)
        response_json = login_request.json()
        login_status = response_json["status"] == 'success'
        self.token = response_json["data"]["token"]

        return login_status

    def query_lib(self, lib_loc):
        """
        query
        :param lib_loc: int
        :return status: true as success false as failure
        :rtype status: bool
        :return data: json data of loc
        :rtype data: dict
        """

        # lib_loc = {'1': '信图', '2': '工图', '3': '医图', '4': '总图'}
        url = '%s/rest/v2/room/stats2/%s' % (self.host, lib_loc)
        headers = self.headers
        headers['token'] = self.token

        query_request = requests.get(url=url, headers=headers)
        response_json = query_request.json()
        status = response_json["status"] == 'success'
        data = response_json['data']

        # exhibit
        from prettytable import PrettyTable
        titles = [title for title in data[0]]
        titles = sorted(titles, reverse=True)
        table = PrettyTable(titles)
        table.padding_width = 2
        for each in data:
            table.add_row([each[title] for title in titles])
        print(table)

        return status, data

    def query_seat(self, room_id, date_str):
        """
        query specific room
        :param room_id: room
        :type room_id: int
        :param date_str: date string formatted as "yyyy-mm-dd"
        :type date_str: str
        :return status: true as success false as failure
        :rtype status: bool
        :return data: json data of seats
        :rtype data: dict
        """

        # lib_loc = {'1': '信图', '2': '工图', '3': '医图', '4': '总图'}
        url = '%s/rest/v2/room/layoutByDate/%s/%s' % (self.host, room_id, date_str)
        headers = self.headers
        headers['token'] = self.token

        query_request = requests.get(url=url, headers=headers)
        response_json = query_request.json()
        status = response_json["status"] == 'success'
        data = response_json["data"]

        return status, data

    def book_seat(self, lib_id, room_name, seat_name, date, start_time, end_time):
        """
        book seat
        :param lib_id: lib id from 1 to 4
        :type lib_id: int
        :param room_name: loc name eg. B1
        :type room_name: str
        :param seat_name: seat name eg. 68
        :type seat_name: str
        :param date: date of booking
        :type date: str
        :param start_time: format as hh:mm
        :type start_time: str
        :param end_time: format as hh:mm
        :type end_time: str
        :return: whether successful
        :rtype: bool
        :return message: result message
        :rtype message: str
        """
        query_loc_status, loc_data = self.query_lib(lib_id)
        if not query_loc_status:
            return False, 'Invalid Lib Id'

        rooms_candidate = list(filter(lambda each: each['room'] == room_name, loc_data))
        if not rooms_candidate:
            return False, 'Invalid Room Name'

        room_id = int(rooms_candidate[0]['roomId'])

        query_seat_status, seat_data = self.query_seat(room_id, date)
        if not query_seat_status:
            return False, 'Invalid date'

        seat_name = '0'*(3-len(seat_name))+seat_name
        seat_candidate = [v for k, v in seat_data['layout'].items()
                          if v['type'] == 'seat' and v['name'] == seat_name]
        if not seat_candidate:
            raise ValueError
            return False, 'Invalid Seat Name'

        seat_id = seat_candidate[0]['id']

        url = '%s/rest/v2/freeBook' % self.host
        headers = self.headers
        headers['token'] = self.token
        # headers['expect'] = '100-continue'

        body = '\"t=1&startTime=%s&endTime=%s&seat=%s&date=%s&t2=2\"' %(
            self.time_to_minute(start_time), self.time_to_minute(end_time), seat_id, date
        )

        # 之前怀疑错误是因为expect: 100-continue的二步post
        # 本来抓包发现有expect: 100-continue, 然后google发现requests不支持这个操作
        # 然后发现 aiohttp client里面可以支持expect100
        # 最后发现，原来坑在两个地方：一是data里面有个引号，二是header content type里面要指定charset
        # fuck
        # 以下代码也可以运行，但是def要改成async然后main里面用loop
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(url=url, headers=headers, data=body, expect100=True) as resp:
        #         print(resp.status)
        #         print(await resp.text())

        book_request = requests.post(url=url, headers=headers, data=body)
        print(book_request.text)
        result = book_request.json()
        return result['status'], result['message']


def main():
    user_id = ''
    user_pwd = ''
    lib_reserv = WhuLibReserv(user_id, user_pwd)
    assert lib_reserv.login() is True
    print(lib_reserv.query_lib(4))
    # res = lib_reserv.book_seat(4, 'A1-座位区', '168', '2018-04-23', '21:00', '21:30')
    # print(res)
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(res)
    # loop.close()


if __name__ == '__main__':
    main()
