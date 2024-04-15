'''
    This class is built to be inherited by other classes. Any class that wants to use 
    `taskHandler` needs to use this class.
'''

import time
import threading

class threadWrapper():
    '''
        This class is used as a way to make any other class meet the min requirements to work with 
        taskHandler. The user can override any of the function if they wish. Also long as the base
        functionality is implemented. In addition when you inherit this class, YOU MUST call the
        constructor. (super().__init__())

        ARGS:
            function_dict : a dictionary, that has the name the system will call to call a function, then the value is the actual function to call. 
            event_dict: a dictionary the key is the event name, and the value is the function to call when the event happens. 
    '''
    def __init__(self, function_dict:dict, event_dict:dict = None):
        self.__status = "NOT STARTED"
        self.__RUNNING = True
        self.__lock_status = threading.Lock()
        self.__lock_running = threading.Lock()
        self.__request = []
        # this is how we handle task in this class, the format is a list [func name, list of args, bool to mark when its been served, returned time, request num]
        self.__request_lock = threading.Lock()
        # this is how we keep track of requests
        self.__request_num = 0
        self.__completed_requests = {}
        self.__function_dict = function_dict #this dictionary contains the list of function from the parent class that can be run in this context


        ###### Set up events ######
        self.__event_dict = {}
        if event_dict is not None:
            for event in event_dict:
                self.__event_dict[event] = [threading.Event(), event_dict[event]] # key event name, value [event object (threading.Event()), function to call.]
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
        '''
            Shut down the task when this is called. 
        '''
        with self.__lock_running:
            self.__RUNNING = False
    
    def make_request(self, type_request, args = []): #pylint: disable=w0102
        '''
            Make a request to to the THREAD, it then returns the task number that you can pass to get Request to see if your task has been completed. 
        '''
        with self.__request_lock:
            self.__request_num += 1
            self.__request.append([type_request, args, False, None, self.__request_num])
            temp = self.__request_num # set a local var to the request num so we can release the mutex
        return temp
    
    def check_request(self, requestNum):
        '''
            This function is for the small set of case where it is necessary to check and see if the request has completed as
            apposed to checking the return val. 

            Input:
                requestNum
            output:
                true/false
        '''
        with self.__request_lock:
            try :
                # pylint: disable=W0104
                self.__completed_requests[requestNum] #this check to see if it is complete or not, because if it is not it just fails and goes to the except block. 
                return True
            except : # pylint: disable=W0702
                return False 
    def get_request(self, requestNum):
        '''
            Check to see if the task has been complete, if it returns None then it has not been completed. 
        '''
        with self.__request_lock:
            try :
                temp = self.__completed_requests[requestNum] #this check to see if it is complete or not, because if it is not it just fails and goes to the except block. 
                del self.__completed_requests[requestNum] # delete the completed task to save space
                return temp
            except : # pylint: disable=W0702
                return None 
    def get_next_request(self):
        # pylint: disable=missing-function-docstring
        with self.__request_lock: 
            if len(self.__request) > 0:
                temp = self.__request.pop(0) # set a local var to the request num so we can release the mutex
            else :
                temp = None
        return temp
    def complete_request(self, key, returnVal):
        # pylint: disable=missing-function-docstring
        self.__completed_requests[key] = returnVal
    def run(self):
        '''
            This function is for multi threading purpose. It works by using a FIFO queue to process Task assigned to it by other threads.
        '''
        self.set_status("Running")
        sleep = False
        while self.get_running():
            ##### Check Events #####
            #check every event that we know about
            for event in self.__event_dict: # pylint: disable=C0206
                if self.__event_dict[event][0].is_set():
                    self.__event_dict[event][1](event) #call the event function
                    self.clear_event(event=event) #clear the event

            #### Handle request made to this class #####
            request = self.get_next_request()
            # check to see if there is a request
            if request is not None:
                if len(request[1]) > 0: 
                    request[3] = self.__function_dict[request[0]](request[1])
                else : 
                    request[3] = self.__function_dict[request[0]]()
                self.complete_request(request[4], request[3])
            else :
                sleep = True

            ##### sleep if no task are needed. #####
            if sleep: # This lowers over all system usage. 
                time.sleep(0.1)
                sleep = False 
    def set_event(self, event):
        '''
            this function lets the class know that an event has happened
        '''
        self.__event_dict[event][0].set()

    def clear_event(self, event):
        '''
            Clear the event.
        '''
        self.__event_dict[event][0].clear()
