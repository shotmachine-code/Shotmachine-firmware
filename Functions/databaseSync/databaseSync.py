import os
import datetime
import time
import pymysql
import sys


################

machine_id= 1
party_id = 2

FullSyncFromOnline =    'pt-table-sync --execute --verbose ' + \
                        '-t error_logs,error_types,machines,parties,party_has_shots,photos,shots,takenshots,users ' + \
                        'h=134.209.174.145, -u root, -pAardslappel987, h=127.0.0.1, -u root, -pAardslappel987'
LastSyncToOnline = 'pt-table-sync --execute --verbose --set-vars wait_timeout=60 --where "created_at > CURDATE() - INTERVAL 1 DAY" ' + \
                   '-t takenshots,photos,machines,error_logs ' + \
                   'h=127.0.0.1, -u root, -pAardslappel987, h=134.209.174.145, -u root, -pAardslappel987'
LastSyncTimeToOnline = 'pt-table-sync --execute --verbose --set-vars wait_timeout=60 --where "id = {}" ' + \
                       '-t machines ' + \
                       'h=127.0.0.1, -u root, -pAardslappel987, h=134.209.174.145, -u root, -pAardslappel987'
LastSyncFromOnline = 'pt-table-sync --execute --verbose --set-vars wait_timeout=60 --where "party_id = {}" ' + \
                     '-t users ' + \
                     'h=134.209.174.145, -u root, -pAardslappel987, h=127.0.0.1, -u root, -pAardslappel987'
LastSyncToOnline = 'pt-table-sync --execute --verbose --set-vars wait_timeout=60 --where "created_at > CURDATE() - INTERVAL 1 DAY" ' + \
                   '-t takenshots,photos,machines,error_logs ' + \
                   'h=127.0.0.1, -u root, -pAardslappel987, h=134.209.174.145, -u root, -pAardslappel987'
sql = "UPDATE machines SET last_sync = NOW() WHERE machine_name = 'Prototype 1'"

db = pymysql.connect("localhost","root","Aardslappel987","shotmachine" )
cursor = db.cursor()
cursor.execute("SELECT VERSION()")
data = cursor.fetchone()
print ("Database version : %s " % data)

# full sync from online to local
print("Perform full sync from online DB to local DB")
answer = os.popen(FullSyncFromOnline).read()
print(answer)

try:
    while True:
        try:
            cursor.execute(sql)
            db.commit()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            db.rollback()
            print("Error in sql")
        # update sync to online database since last sync
        curr_time = datetime.datetime.now().strftime("%Y-%m-%m %H:%M:%S")
        print("Perform update sync from local DB to online DB")
        print(curr_time)
        answer = os.popen(LastSyncToOnline).read()
        print(answer)
        print("Perform update sync from online DB to local DB")
        answer = os.popen(LastSyncFromOnline.format(party_id)).read()
        print(answer)
        print("Sync last synctime to online DB")
        answer = os.popen(LastSyncTimeToOnline.format(machine_id)).read()
        print(answer)
        time.sleep(1)

finally:
    db.close()
    print("Closed program")
