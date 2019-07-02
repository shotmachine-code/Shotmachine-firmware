import os
import datetime
import time


################


FullSyncFromOnline = 'pt-table-sync --execute --verbose -t takenshots,photos,users h=134.209.174.145, -u root, -pAardslappel987, h=127.0.0.1, -u root, -pAardslappel987'
LastSyncToOnline = 'pt-table-sync --execute --verbose --set-vars wait_timeout=10000 --where "created_at > CURDATE() - INTERVAL 1 DAY" -t takenshots,photos h=127.0.0.1, -u root, -pAardslappel987, h=134.209.174.145, -u root, -pAardslappel987'
LastSyncFromOnline = 'pt-table-sync --execute --verbose --set-vars wait_timeout=10000 --where "created_at > CURDATE() - INTERVAL 1 DAY" -t users h=134.209.174.145, -u root, -pAardslappel987, h=127.0.0.1, -u root, -pAardslappel987'


print("Starting sync for database")
curr_time = datetime.datetime.now().strftime("%Y-%m-%m %H:%M:%S")
# print(curr_time)
last_sync_time = curr_time


# full sync from online to local
print("Perform full sync from online DB to local DB")
answer = os.popen(FullSyncFromOnline).read()
print(answer)

while True:
    # update sync to online database since last sync
    curr_time = datetime.datetime.now().strftime("%Y-%m-%m %H:%M:%S")
    #print(curr_time)
    print("Perform update sync from local DB to online DB")
    print(curr_time)
    answer = os.popen(LastSyncToOnline).read()
    print(answer)
    print("Perform update sync from online DB to local DB")
    answer = os.popen(LastSyncFromOnline).read()
    print(answer)
    #last_sync_time = curr_time
    time.sleep(10)

