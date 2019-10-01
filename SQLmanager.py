import pymysql
from datetime import datetime
import pyqrcode

HOST = "HOSTNAME-HERE"
USER = "USER-HERE"
PASS = "PASSWORD-HERE"
DATABASE = "DATABASE-NAME-HERE"

NUMBER_SPACES = 10

#CREATE TABLE reservation_table (
#    id INT AUTO_INCREMENT PRIMARY KEY, 
#    userid INTEGER, 
#    starttime CHAR(45), 
#    endtime CHAR(45), 
#    priority INTEGER, 
#    available INTEGER
#);" 

def init_db():
    now = datetime.now()

    reserve_space(1, now.replace(hour=8).replace(minute=0).replace(second=0), now.replace(hour=16).replace(minute=0).replace(second=0))
    reserve_space(2, now.replace(hour=8).replace(minute=0).replace(second=0), now.replace(hour=16).replace(minute=0).replace(second=0))
    reserve_space(3, now.replace(hour=8).replace(minute=0).replace(second=0), now.replace(hour=14).replace(minute=0).replace(second=0))
    reserve_space(3, now.replace(hour=15).replace(minute=30).replace(second=0), now.replace(hour=18).replace(minute=0).replace(second=0))

def get_availability(starttime, endtime):

    string_init = starttime.strftime('%Y-%m-%d %H:%M:%S')
    string_end = endtime.strftime('%Y-%m-%d %H:%M:%S')

    db = pymysql.connect(HOST, USER, PASS, DATABASE)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    cursor3 = db.cursor()

    sql1 = "SELECT COUNT(*) FROM reservation_table WHERE starttime <= '%s' AND endtime >= '%s' AND available = 1" % (string_init, string_end)
    sql2 = "SELECT COUNT(*) FROM reservation_table WHERE endtime > '%s' AND endtime < '%s' AND available = 1" % (string_init, string_end)
    sql3 = "SELECT COUNT(*) FROM reservation_table WHERE starttime > '%s' AND starttime < '%s' AND available = 1" % (string_init, string_end)

    result = 0

    try:
        cursor1.execute(sql1)
        cursor2.execute(sql2)
        cursor3.execute(sql3)

        result = cursor1.fetchone()[0]
        result += cursor2.fetchone()[0]
        result += cursor3.fetchone()[0]

    except:
        print("Error: unable to fetch data")
        return -1

    db.close()
    return NUMBER_SPACES - result

def check_duplication(user_id, starttime, endtime):

    string_init = starttime.strftime('%Y-%m-%d %H:%M:%S')
    string_end = endtime.strftime('%Y-%m-%d %H:%M:%S')

    db = pymysql.connect(HOST, USER, PASS, DATABASE)
    cursor1 = db.cursor()
    cursor2 = db.cursor()
    cursor3 = db.cursor()

    sql1 = "SELECT COUNT(*) FROM reservation_table WHERE starttime <= '%s' AND endtime >= '%s' AND userid='%d'" % (string_init, string_end, user_id)
    sql2 = "SELECT COUNT(*) FROM reservation_table WHERE endtime > '%s' AND endtime < '%s' AND userid='%d'" % (string_init, string_end, user_id)
    sql3 = "SELECT COUNT(*) FROM reservation_table WHERE starttime > '%s' AND starttime < '%s' AND userid='%d'" % (string_init, string_end, user_id)

    result = 0

    try:
        cursor1.execute(sql1)
        cursor2.execute(sql2)
        cursor3.execute(sql3)

        result = cursor1.fetchone()[0]
        result += cursor2.fetchone()[0]
        result += cursor3.fetchone()[0]

    except:
        print("Error: unable to fetch data")
        return -1

    db.close()
    return result


def reserve_space(user_id, starttime, endtime):

    string_init = starttime.strftime('%Y-%m-%d %H:%M:%S')
    string_end = endtime.strftime('%Y-%m-%d %H:%M:%S')

    db = pymysql.connect(HOST, USER, PASS, DATABASE)
    cursor = db.cursor()

    sql = "INSERT INTO reservation_table (userid, starttime, endtime, priority) VALUES (%d, '%s', '%s', 0);" % \
          (user_id, string_init, string_end)

    try:
       cursor.execute(sql)
       db.commit()

    except:
        db.rollback()
        print("Error: unable to write data")
        return -1

    qr_result = pyqrcode.create(string_init + str(cursor.lastrowid))
    qr_result.png('qrcode.png', scale=8)
    db.close()
    return 1


def update_reservation(user_id, starttime, endtime):
    string_init = starttime.strftime('%Y-%m-%d %H:%M:%S')
    string_end = endtime.strftime('%Y-%m-%d %H:%M:%S')

    db = pymysql.connect(HOST, USER, PASS, DATABASE)
    cursor = db.cursor()

    sql = "UPDATE reservation_table SET starttime = '%s', endtime = '%s' WHERE userid = %d;" % \
          (string_init, string_end, user_id)

    try:
        cursor.execute(sql)
        db.commit()

    except:
        db.rollback()
        print("Error: unable to write data")
        return -1

    db.close()
    return 1


def cancel_reservation(user_id, id):
    db = pymysql.connect(HOST, USER, PASS, DATABASE)
    cursor = db.cursor()
    count = -1

    sql = "DELETE from reservation_table WHERE userid = %d AND id = %d;" % (user_id, id)

    try:
        cursor.execute(sql)
        count = cursor.rowcount
        db.commit()

    except:
        db.rollback()
        print("Error: unable to delete data")
        return -1

    db.close()
    return count


def reserve_priority_space(user_id, unit_id, starttime, endtime, priority):
    string_init = starttime.strftime('%Y-%m-%d %H:%M:%S')
    string_end = endtime.strftime('%Y-%m-%d %H:%M:%S')

    db = pymysql.connect(HOST, USER, PASS, DATABASE)
    cursor = db.cursor()

    sql = "INSERT INTO reservation_table (userid, unitid, starttime, endtime, priority) VALUES (%d, %d, '%s', '%s', %d);" \
          % (user_id, unit_id, string_init, string_end, priority)

    print(sql)

    try:
       cursor.execute(sql)
       db.commit()

    except:
        db.rollback()
        print("Error: unable to write data")
        return -1

    db.close()
    return 1


def set_unavailable(reservation_id, unit_id, starttime):
    string_init = starttime.strftime('%Y-%m-%d %H:%M:%S')

    db = pymysql.connect(HOST, USER, PASS, DATABASE)
    cursor = db.cursor()

    sql = "UPDATE reservation_table SET unit_id = %d, starttime = '%s', available = %d WHERE reservation_id = %d;"\
          % (unit_id, string_init, 0, reservation_id)

    try:
        cursor.execute(sql)
        db.commit()

    except:
        db.rollback()
        print("Error: unable to write data")
        return -1

    db.close()
    return 1


def free_unit(reservation_id, endtime):
    string_end = endtime.strftime('%Y-%m-%d %H:%M:%S')

    db = pymysql.connect(HOST, USER, PASS, DATABASE)
    cursor = db.cursor()

    sql = "SELECT * FROM reservation_table WHERE id = %d;" % reservation_id

    try:
        cursor.execute(sql)
        result = cursor.fetchone()

    except:
        print("Error: unable to fetch data")
        return -1

    sql = "INSERT INTO history_table (userid, unitid, starttime, endtime, priority) VALUES (%d, %d, '%s', '%s', %d);" \
          % (result[1], result[4], result[2], string_end, result[5])

    try:
        cursor.execute(sql)
        db.commit()

    except:
        db.rollback()
        print("Error: unable to write data")
        return -1

    sql = "DELETE from reservation_table WHERE id = %d;" % reservation_id

    try:
        cursor.execute(sql)
        db.commit()

    except:
        db.rollback()
        print("Error: unable to delete data")
        return -1

    db.close()
    return 1


def get_reservation(user_id):

    string_init = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    db = pymysql.connect(HOST, USER, PASS, DATABASE)
    cursor = db.cursor()

    sql = "SELECT * FROM reservation_table WHERE userid = %d LIMIT 5;" \
          % (user_id)

    user_reservations = []

    try:
        cursor.execute(sql)
        results = cursor.fetchall()

        for row in results:

            user_reservations.append([row[0], row[2], row[3]])
    except:
        print("Error: unable to fetch data")

    db.close()
    return user_reservations

a = datetime(2019, 9, 29, 7, 25, 26, 936787)
b = datetime(2019, 9, 29, 9, 36, 24, 936787)
#print(reserve_space(2, a, b))
