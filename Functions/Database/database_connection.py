



class database_connection():

    def __init__(self):





    def getUserName(self, barcode):
        sql_check_username = "Select name FROM users WHERE (barcode = {} AND party_id = {})"
        try:
            cursor.execute(sql_check_username.format(barcode, party_id))
            result = cursor.fetchone()
            if result == None:
                print("User not found, scanned barcode: " + str(read_number))
            else:
                Username = result[0]
                print("Barcode scanner from user: " + Username + " With barcode: " + str(read_number))
         except:
            print("Unexpected error:", sys.exc_info()[0])
            db.rollback()
            print("Error in sql")