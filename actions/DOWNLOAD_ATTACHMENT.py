# IMPORTING ALL REQUIRED MODULES
import requests, json, os
from st2common.runners.base_action import Action

class donwloadAttachments(Action):
    output = dict()

    # Header Details
    REQUEST_HEADER = {"json": {"Content-Type": "application/xml", "Accept": "application/json"},
                      "png": {"Content-Type": "application/xml", "Accept": "application/png"},
                      "xml": {"Content-Type": "application/xml", "Accept": "application/xml"},
                      }

    ATTACHMENT_API = '/api/now/attachment'
    TABLE_API = '/api/now/table'

    def run(self, InstanceName, UserName, Password, DOWNLOAD_DIR, CERT_FILE_NAME, TicketNumer):
        try:
            # ServiceNow Instance URl
            Url = 'https://' + InstanceName + '.service-now.com'

            # checking Ticket type based on that secleting table name
            if (TicketNumer.startswith('INC')):
                TABLE_NAME = 'incident'
            elif (TicketNumer.startswith('REQ')):
                TABLE_NAME = 'sc_request'
            elif (TicketNumer.startswith('RITM')):
                TABLE_NAME = 'sc_req_item'
            elif (TicketNumer.startswith('SCTASK')):
                TABLE_NAME = 'sc_task'
            elif (TicketNumer.startswith('CHG')):
                TABLE_NAME = 'change_request'
            else:
                self.output['retCode'] = "1"
                self.output['retDesc'] = "No table found for - {0}".format(TicketNumer)
                self.output['result'] = "Failed"
                return (False, json.loads(json.dumps(self.output)))

            DOWNLOAD_DIR = DOWNLOAD_DIR + "/Netscaler_SSL_CERT_Renewal/" + TicketNumer
            # DOWNLOAD_DIR = DOWNLOAD_DIR + "\\Netscaler_SSL_CERT_Renewal\\" + TicketNumer
            isExist = os.path.exists(DOWNLOAD_DIR)
            if not isExist:
                os.makedirs(DOWNLOAD_DIR)

            result = self.get_file_attachment(Url, TicketNumer, UserName, Password, TABLE_NAME, DOWNLOAD_DIR, CERT_FILE_NAME)
            if (result['retCode'] == "0"):
                self.output['retCode'] = "0"
                self.output['CERT_PATH'] = DOWNLOAD_DIR
                self.output['retDesc'] = "Attachment downloaded - {0} - {1}".format(TicketNumer, result['retDesc'])
                self.output['result'] = "Success"
                return (True, json.loads(json.dumps(self.output)))
            else:
                self.output['retCode'] = "1"
                self.output['CERT_PATH'] = "NA"
                self.output['retDesc'] = "Attachment downloaded Failure- {0} - {1}".format(TicketNumer, result['retDesc'])
                self.output['result'] = "Failure"
                return (False, json.loads(json.dumps(self.output)))

        except Exception as err:
            Msg = str(err)
            Msg = Msg.split('\n')[0]
            self.output['retCode'] = "1"
            self.output['CERT_PATH'] = "NA"
            self.output['retDesc'] = "Attachment Download Exception - {0}".format(Msg)
            self.output['result'] = "Failed"
            return (False, json.loads(json.dumps(self.output)))

    def get_table_data(self, Url, table_name, param, UserName, Password):
        try:
            url = Url + self.TABLE_API + '/' + table_name + '?' + param
            response = requests.get(url, auth=(UserName, Password), headers=self.REQUEST_HEADER.get('json'))

            # Check for HTTP codes other than 200
            if response.status_code != 200:  # if error, then exit
                Msg = response.json()
                self.output['retCode'] = "1"
                self.output['CERT_PATH'] = "NA"
                self.output['retDesc'] = Msg
                self.output['result'] = "Failed"
                return json.loads(json.dumps(self.output))

            Msg = response.json()
            self.output['retCode'] = "0"
            self.output['CERT_PATH'] = "NA"
            self.output['retDesc'] = Msg
            self.output['result'] = "Success"
            return json.loads(json.dumps(self.output))
        except Exception as err:
            Msg = str(err)
            Msg = Msg.split('\n')[0]
            self.output['retCode'] = "1"
            self.output['CERT_PATH'] = "NA"
            self.output['retDesc'] = Msg
            self.output['result'] = "Failed"
            return json.loads(json.dumps(self.output))

    def get_attachment(self, Url, att_sys_id, file_type, download_dir, UserName, Password):
        try:
            url = Url + '/' + self.ATTACHMENT_API + '/' + att_sys_id + '/file'

            response = requests.get(url, auth=(UserName, Password), headers=self.REQUEST_HEADER.get(file_type))

            # Check for HTTP codes other than 200
            if response.status_code != 200:  # if error, then exit
                Msg = response.json()
                self.output['retCode'] = "1"
                self.output['CERT_PATH'] = "NA"
                self.output['retDesc'] = Msg
                self.output['result'] = "Failed"
                return json.loads(json.dumps(self.output))
            # print(download_dir)
            with open(download_dir, 'wb') as f:
                for chunk in response:
                    f.write(chunk)
        except Exception as err:
            Msg = str(err)
            Msg = Msg.split('\n')[0]
            self.output['retCode'] = "1"
            self.output['CERT_PATH'] = "NA"
            self.output['retDesc'] = Msg
            self.output['result'] = "Failed"
            return json.loads(json.dumps(self.output))

    def get_file_attachment(self, Url, record_number, UserName, Password, TABLE_NAME, DOWNLOAD_DIR, CERT_FILE_NAME):
        try:
            # Creating Query for Fetching Record SYS_ID
            param = 'sysparm_query=number=' + record_number + '&sysparam_limit=1'

            # Function call to fetch Record SYS_ID
            file_info = self.get_table_data(Url, TABLE_NAME, param, UserName, Password)

            if (file_info['retCode'] == "0"):  # if no error while fetching Record SYS_ID
                if len(file_info['retDesc']['result']) < 1:  # if no record found
                    self.output['retCode'] = "1"
                    self.output['CERT_PATH'] = "NA"
                    self.output['retDesc'] = "There is no record found for : {0}".format(record_number)
                    self.output['result'] = "Failed"
                    return json.loads(json.dumps(self.output))

                table_sys_id = file_info['retDesc']['result'][0]['sys_id']
                param = 'sysparm_query=table_sys_id=' + table_sys_id + '&sysparam_limit=1'
                attachments = self.get_table_data(Url, 'sys_attachment', param, UserName, Password)

                if (attachments['retCode'] == "0"):
                    result = attachments['retDesc']['result']
                    if (len(result) >= 1):
                        for attach_file in result:
                            attach_sys_id = attach_file.get('sys_id')
                            content_type = attach_file.get('content_type').split('/')
                            file_ext = content_type[1]
                            #print(file_ext)
                            file_name = attach_file.get('file_name')
                            if(file_name.split('.')[-1]=='zip'):
                                file_name = CERT_FILE_NAME
                                x = DOWNLOAD_DIR + "/" + file_name  #original code
                            # x = DOWNLOAD_DIR + "\\" + file_name
                                self.get_attachment(Url, attach_sys_id, file_ext, x, UserName, Password)
                        self.output['retCode'] = "0"
                        self.output['CERT_PATH'] = "NA"
                        self.output['retDesc'] = "{0} attachment found ".format(len(result))
                        self.output['result'] = "Certificate downloaded Successfully"
                        return json.loads(json.dumps(self.output))
                    else:
                        self.output['retCode'] = "1"
                        self.output['CERT_PATH'] = "NA"
                        self.output['retDesc'] = "There is no attachment found for {0} ".format(record_number)
                        self.output['result'] = "Certificate downloaded Successfully from Incident."
                        return json.loads(json.dumps(self.output))
                else:
                    return attachments
            else:
                return file_info
        except Exception as err:
            Msg = str(err)
            Msg = Msg.split('\n')[0]
            self.output['retCode'] = "1"
            self.output['CERT_PATH'] = "NA"
            self.output['retDesc'] = Msg
            self.output['result'] = "Failed"
            return json.loads(json.dumps(self.output))


