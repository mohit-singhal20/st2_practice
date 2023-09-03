'''
    .SYNOPSIS
        This Script is for Fetching Catalog Variables from Ticket.
        
    .DESCRIPTION
        This Script is for Fetching Catalog Variables from Ticket (RITM or SCTASK).

    .Input 
        1. InstanceName                 :   ServiceNow Instance name
        2. UserName                     :   ServiceNow User name
        3. Password                     :   ServiceNow Password
        4. TicketNumer                  :   ServiceNow Ticket Number (RITM or SCTASK)
        5. variableNames                :   Comma seperated variables to fetcch from catalog task

    .OUTPUT
        1. retCode                      :   Return Code (0-Success , 1-Failed)            
        2. retDesc                      :   Return Description (error Messae in case of failure)
        3. result                       :   Result Message (Success/Failed)
        4. data                         :   Key value pair of variables from catalog Task

'''

# IMPORTING ALL REQUIRED MODULES 
import requests,json
from st2common.runners.base_action import Action

class Mytestfunction(Action):
    output = dict()

    # Header Details
    headers = {"Content-Type":"application/json","Accept":"application/json"}

    TABLE_API = '/api/now/table'

    def run(self,InstanceName,UserName,Password,TicketNumer,variableNames):
        try:
            # ServiceNow Instance URl
            Url = 'https://'+ InstanceName +'.service-now.com'

            # checking Ticket type (RITM or SCTASK) based on that secleting table name
            if(TicketNumer.startswith('RITM')):
                TABLE_NAME = 'sc_req_item'
            elif(TicketNumer.startswith('SCTASK')):
                TABLE_NAME = 'sc_task'
            else:
                self.output['retCode'] = "1"
                self.output['retDesc'] = "No table found for - {0}".format(TicketNumer)
                self.output['result'] = "Failed"
                return (False, json.loads(json.dumps(self.output))) 

            result = self.get_catalog_variables(Url,TicketNumer,UserName,Password,TABLE_NAME,variableNames)

            if(result['retCode'] == "0"):
                self.output['retCode'] = "0"
                self.output['retDesc'] = "Details Fetched from Catalog Task"
                self.output['result'] = "Success"
                self.output['data'] = result['retDesc']
                return (True, json.loads(json.dumps(self.output))) 
            else:
                self.output['retCode'] = "1"
                self.output['retDesc'] = "Attachment downloaded Failure- {0} - {1}".format(TicketNumer,result['retDesc'])
                self.output['result'] = "Failure"
                self.output['data'] = ""
                return (False, json.loads(json.dumps(self.output))) 
    
        except Exception as err:
            Msg=str(err)
            Msg=Msg.split('\n')[0]
            self.output['retCode'] = "1"
            self.output['retDesc'] = "Catalog Variable Fetch Exception - {0}".format(Msg)
            self.output['result'] = "Failed"
            self.output['data'] = ""
            return (False, json.loads(json.dumps(self.output)))  

    def get_table_data(self,Url,table_name, param,UserName,Password):
        try:
            url = Url + self.TABLE_API + '/' + table_name + '?' + param
            response = requests.get(url, auth=(UserName, Password), headers=self.headers)

            # Check for HTTP codes other than 200
            if response.status_code != 200:  # if error, then exit
                Msg=response.json()
                self.output['retCode'] = "1"
                self.output['retDesc'] = Msg
                self.output['result'] = "Failed"
                return json.loads(json.dumps(self.output))
            Msg=response.json()
            self.output['retCode'] = "0"
            self.output['retDesc'] = Msg
            self.output['result'] = "Success"
            return json.loads(json.dumps(self.output))
        except Exception as err:
            Msg=str(err)
            Msg=Msg.split('\n')[0]
            self.output['retCode'] = "1"
            self.output['retDesc'] = Msg
            self.output['result'] = "Failed"
            return json.loads(json.dumps(self.output))

    def get_catalog_variables(self,Url,record_number,UserName,Password,TABLE_NAME,variableNames):
        try:
            # Creating Query for Fetching Record SYS_ID
            param = 'sysparm_query=number=' + record_number + '&sysparam_limit=1'

            # Function call to fetch Record SYS_ID
            file_info = self.get_table_data(Url,TABLE_NAME, param,UserName,Password)

            if(file_info['retCode'] == "0"):        # if no error while fetching Record SYS_ID
                if len(file_info['retDesc']['result']) < 1:     # if no record found 
                    self.output['retCode'] = "1"
                    self.output['retDesc'] = "There is no record found for : {0}".format(record_number)
                    self.output['result'] = "Failed"
                    return json.loads(json.dumps(self.output))
                else:                                           # if record found
                    record_sys_id = file_info['retDesc']['result'][0]['sys_id']

                    # Splitting variable using comma
                    varList = variableNames.split(",")      
                    QueryData = ''

                    # Loop for creating Query for fetching Catalog variables value
                    for i in range(len(varList)):
                        if(i != 0):
                            QueryData = QueryData + '%2Cvariables.'+varList[i]
                        else:
                            QueryData = QueryData + 'variables.'+varList[i]
            
                    url = Url + self.TABLE_API + '/' + TABLE_NAME + '/' + record_sys_id +'?sysparm_display_value=true&sysparm_fields='+QueryData

                    # Calling Api for fetching Catalog variables value 
                    response = requests.get(url, auth=(UserName, Password), headers=self.headers)

                    # Check for HTTP codes other than 200
                    if response.status_code != 200: 
                        Msg=response.json()
                        self.output['retCode'] = "1"
                        self.output['retDesc'] = Msg
                        self.output['result'] = "Failed"
                        return json.loads(json.dumps(self.output))

                    Msg=response.json()
                    finalresult = dict()
                    finalresultList = []
                    for key in Msg['result'].keys():
                        finalresult[key.split(".")[1]]=Msg['result'][key]
                    finalresultList.append(finalresult)
                    self.output['retCode'] = "0"
                    self.output['retDesc'] = finalresultList
                    self.output['result'] = "Success"
                    return json.loads(json.dumps(self.output))
            else:                                   # if any error while fetching Record SYS_ID
                return file_info
        except Exception as err:
            Msg=str(err)
            Msg=Msg.split('\n')[0]
            self.output['retCode'] = "1"
            self.output['retDesc'] = Msg
            self.output['result'] = "Failed"
            return json.loads(json.dumps(self.output))


