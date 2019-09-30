import requests
from bs4 import BeautifulSoup as bs
import json
import time
import os

'''
发送请求，返回数据
'''


def request_grade(student_id):
    url = "http://jwxt.wust.edu.cn/whkjdx/services/whkdapp"
    headers = {"Content-Type": "application/xml"}
    body = '''<v:Envelope xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns:d="http://www.w3.org/2001/XMLSchema" xmlns:c="http://schemas.xmlsoap.org/soap/encoding/" xmlns:v="http://schemas.xmlsoap.org/soap/envelope/">
        <v:Header />
        <v:Body>
            <getxscj xmlns="http://webservices.qzdatasoft.com" id="o0" c:root="1">
                <in0 i:type="d:string">%s</in0>
                <in1 i:type="d:string">2019-05-03 01:04:42</in1>
                <in2 i:type="d:string">c61a4c8cc546056465c54d70a891f6</in2>
            </getxscj>
        </v:Body>
    </v:Envelope>'''

    return requests.post(url, (body % student_id), headers=headers).text


'''
处理数据，保存文件
'''


def save_grade_json(student_id):
    text = request_grade(student_id)
    data = bs(text, "lxml").find("ns1:out").get_text()
    grade_json = json.loads(data)
    with open('grade/%s.json' % student_id, 'w') as f:
        json.dump(grade_json, f, ensure_ascii=False)
        print("%s 已写入文件" % student_id)


def get_student_id_list():
    student_id_list = []
    with open("namelist.txt", 'r') as f:
        for line in f:
            student_id_list.append(line.strip())
    return student_id_list


def load_grade(student_id):
    with open("grade/%s.json" % student_id) as f:
        data = json.load(f)
        print(data)


def multiply_process():
    json_files = os.listdir("grade")
    for json_file in json_files:
        print("处理 %s"%json_file)
        student = process_single_file(json_file)
        result_list[student.student_id] = student


def process_single_file(filename):
    with open("grade/%s" % filename) as f:
        courses = json.load(f)
        student_grade = Student_Grade(filename.split(".")[0], courses[0]['xm'])
        for course in courses:
            grade = Grade(course)
            # 去除公选课
            if grade.course_type == "通识教育平台课程" and grade.is_must == "选修":
                continue
            if grade.remarks is not None:
                print("remarkkkkkkkkkk:" + str(grade.__dict__))

            if grade.test_type != "正常考试":
                print("errorrrrrrrrrr" + str(grade.__dict__))

            if grade.grade in class_to_grade:
                grade.grade = class_to_grade[grade.grade]

            if int(grade.grade)<60:
                print("grade below 60",str(grade.__dict__))

            # 该门课为培养方案上的课程 第一次
            if student_grade.course_list.get(grade.course_name) is None:
                student_grade.course_list[grade.course_name]= grade
            else:
                # 重修
                print("--------------------")
                print(student_grade.student_id,student_grade.student_name)
                print(str(student_grade.course_list[grade.course_name].__dict__))
                print(str(grade.__dict__))

                if grade.grade_point > student_grade.course_list[grade.course_name].grade_point or (
                        grade.grade_point > student_grade.course_list[grade.course_name].grade_point and grade.grade >
                        student_grade.course_list[grade.course_name].grade):
                    student_grade.course_list[grade.course_name] = grade

    for c in student_grade.course_list:
        c_grade = student_grade.course_list.get(c)
        student_grade.all_add+=int(c_grade.credit)*int(c_grade.grade)
        student_grade.all_creadit+=int(c_grade.credit)
    student_grade.average = student_grade.all_add/student_grade.all_creadit
    return student_grade


class Grade:
    '''
      {

    "cjbsmc": null,
    "zxs": 32,
    '''

    def __init__(self, data):
        self.test_type = data['ksxzmc']
        self.course_type = data['kcxzmc']
        self.is_must = data['kclbmc']
        self.grade_point = data['jd']
        self.grade = data['zcj']
        self.remarks = data['cjbsmc']
        self.course_name = data['kcmc']
        self.credit = data['xf']


class Student_Grade:
    def __init__(self, student_id, student_name):
        self.student_id = student_id
        self.student_name = student_name
        self.course_list = {}
        self.average = 0
        self.all_creadit = 0
        self.all_add = 0


if __name__ == '__main__':
    class_to_grade = {"A": 100, "A-": 89, "B+": 84, "B": 81, "B-": 77, "C+": 74, "C": 71, "C-": 67, "D": 63, "F": 59}
    all_courses = []
    result_list={}

    multiply_process()

    for name in result_list:
        student = result_list.get(name)
        print("%s\t%s\t%s"%(name,student.student_name,student.average))