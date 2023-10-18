'''
    This class is ment to be inherited by other classes. Any class that wants to use 
    `taskHandler` needs to use this class.
'''

import time
import threading
import random

class threadWrapper():
    '''
        This class is used as a way to make any other class meet the min requirements to work with 
        taskHandler. The user can override any of the function if they wish. Also long as the base
        fucntionality is implemented. In addition when you inherite this class, YOU MUST call the
        construtor. (super().__init__())
    '''
    def __init__(self):
        self.__status = "NOT STARTED"
        self.__RUNNING = True
        self.__lock_status = threading.Lock()
        self.__lock_running = threading.Lock()
        self.__request = []
        # this is how we handle task in this class, the format is a list [func name, list of args, bool to mark when its been served, returned time, request num]
        self.__request_lock = threading.Lock()
        # this is how we keep track of requsts
        self.__requet_num = 0
        self.__completed_requestes = {}

    def get_status(self):
        # pylint: disable=missing-function-docstring
        with self.__lock_status:
            return self.__status
    def set_status(self, status):
        # pylint: disable=missing-function-docstring
        with self.__lock_status:
            self.__status = status

    def get_running(self):
        # pylint: disable=missing-function-docstring
        with self.__lock_running:
            return self.__RUNNING
    def kill_Task(self):
        with self.__lock_running:
            self.__RUNNING = False
    
    def make_request(self, type, args=[]):
        '''
            Make a request to to the THREAD, it then returns the task number that you can pass to get Request to see if your task has been completed. 
        '''
        with self.__request_lock:
            self.__requet_num += 1
            self.__request.append([type, args, False, None, self.__requet_num])
            temp = self.__requet_num # set a local var to the reqest num so we can relase the mutex
        return temp
    
    def check_request(self, requestNum):
        '''
            This function is for the small set of case where it is nessary to check and see if the request has completed as
            aposed to checking the return val. 

            Input:
                requestNum
            output:
                true/false
        '''
        with self.__request_lock:
            try :
                self.__completed_requestes[requestNum] #this check to see if it is complete or not, because if it is not it just fails and goes to the except block. 
                return True
            except :
                return False 
    
    
    def get_request(self, requestNum):
        '''
            Check to see if the task has been complete, if it returns None then it has not been completed. 
        '''
        with self.__request_lock:
            try :
                temp = self.__completed_requestes[requestNum] #this check to see if it is complete or not, because if it is not it just fails and goes to the except block. 
                del self.__completed_requestes[requestNum] # delete the completed task to save space
                return temp
            except :
                return None 
    
    def get_next_request(self):
        # pylint: disable=missing-function-docstring
        with self.__request_lock: 
            if(len(self.__request) > 0):
                temp = self.__request.pop(0) # set a local var to the reqest num so we can relase the mutex
            else :
                temp = None
        return temp
    
    def complet_request(self, key, returnVal):
        # pylint: disable=missing-function-docstring
        self.__completed_requestes[key] = returnVal

   
    def run(self):
        '''
            This function is for multi threading purpose. It works by using a FIFO queue to process Task assigned to it by other threads.
        '''
        self.set_status("Running")
        sleep = False
        while(self.get_running()):
            request = self.get_next_request()
            # check to see if there is a request
            if(request != None):
                if(len(request[1]) > 0): request[3] = eval("self." + request[0])(request[1])
                else : request[3] = eval("self." + request[0])()
                self.complet_request(request[4], request[3])
            else :
                sleep = True      
            if(sleep): #sleep if no task are needed. 
                time.sleep(0.1)
                sleep = False  
