from src.databases.query import QueryOperation

class CheckUser():
    def checkUser(self,username,password)->tuple[bool,str,None]:
        #check presence of the data
        if not all((username,password)):
            return False,"Username & Password Field Cannot Be Empty!",None
        
        success,dMessage,result = self.__getting_user_credentials()

        if not success:
            return success,dMessage,None
        
        for item in result:
            if (
                (username==item["username"] and password==item["password"])
            ):
                #if access level need to return then need to change None here
                return True,"User matched !",None
            
        return False,"Username & Password didn't match with the Creadentials!",None
        

    def __getting_user_credentials(self):
        #create query instance
        qOperation = QueryOperation()

        try:
            query = "SELECT username,password FROM users;"
            success,dMessage,result = qOperation.readSQL(query=query)

            if not success:
                return success,dMessage,None
            
            formated_data = []
            for item in result:
                formated_data.append({
                    "username":item["username"],
                    "password":item["password"]
                })

            return success,dMessage,formated_data
        
        except Exception as e:
            return False, "Error : " + str(e), None