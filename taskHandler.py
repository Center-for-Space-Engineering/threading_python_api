'''
    This module handles all the threads and running them. 
'''
import threading
import datetime
from logging_system_display_python_api.logger import loggerCustom # pylint: disable=import-error


class taskHandler():
    '''
        This class is what collects all the task and then runs them. It also checks on the status of every class. 
        The status is set by using the following command: super().setStatus("Running"). When ever a task is created it 
        is given the status of "NOT STARTED". When it is finished it is given the status of "Complete". If the task every 
        crashes it should return a status of "Error". Remeber that the status of "Running" and "Complete" should be set 
        by the user. With the one excetion of "Running" when the users just uses the prebuilt run function implemented in 
        `threadWrapper`.

        The general function of this class is that it implements a threading api as follows. First a thread is added use 
        add_thread. NOTE: This only adds the thread to a dictionary. It DOES NOT start the thread at this time. To start
        all the threads the user then calls the `start` function. This will start all threads in the dictionary. It
        can all be called multiple times with out fear of conflict. 

        For messaging there are the `pass_request` and `pass_return` functions. These functions are implemented by the 
        `messageHandler` in the `logging_system_display_python_api`. However if the user  wish to not use that api, or 
        implement theself here is how they work. The `pass_request` takes in a thread name and then access that thread
        and pass the function name and args to it. The `pass_return` return then checks to see if the task has completed 
        the request and returns None or the value from the task.
    '''
    def __init__(self, coms):
        self.__threads = {}
        self.__coms = coms 
        self.__logger = loggerCustom("logs/taskHandler.txt")
        self.add_thread(self.__coms.run, "Coms/Graphics_Handler", self.__coms)
        self.__completed_taskes = {}
        self.__request_lock = threading.Lock()


    
    def add_thread(self, runFunction, taskID, wrapper, args = None):
        ''''
            This function takes a taskID (string) and a run function (function to start the thread)
            It then starts a theard and adds it to the dictionary of threads. 
            In side the dictionary it holds the threads. 
        '''
        if args is None:
            self.__threads[taskID] = (threading.Thread(target=runFunction), wrapper)
            self.__coms.print_message(f"Thread {taskID} created with no args. ")
            self.__logger.send_log(f"Thread {taskID} created with no args. ")
        else :
            self.__threads[taskID] = (threading.Thread(target=runFunction, args=args), wrapper)
            self.__coms.print_message(f"Thread {taskID} created with args {args}. ")
            self.__logger.send_log(f"Thread {taskID} created with args {args}. ")

    
    
    def start(self):
        '''
            starts all the threads in the threads dictinary
        '''
        for thread in self.__threads: #pylint: disable=C0206
            if self.__threads[thread][1].get_status() == "NOT STARTED":
                self.__threads[thread][0].start() #start thread
                self.__coms.print_message(f"Thread {thread} started. ")
                self.__logger.send_log(f"Thread {thread} started. ")

    def get_thread_status(self):
        '''
            Gets the thread status, then sends message to the `Message handler class`
        '''
        reports = [] # we need to pass a list of reports so the all get displayed at the same time. 
        for thread in self.__threads: #pylint: disable=C0206
            if self.__threads[thread][0].is_alive():
                reports.append((thread, "Running", f"[{datetime.datetime.now()}]"))
                self.__logger.send_log(f"Thread {thread} is Running. ")
            else :
                if self.__threads[thread][1].get_status() == "Complete":
                    try:
                        doneTime = self.__completed_taskes[thread]
                    except : # pylint: disable=w0702
                        self.__completed_taskes[thread] = datetime.datetime.now()
                        doneTime = self.__completed_taskes[thread]

                    reports.append((thread, "Complete", f"[{doneTime}]"))
                    self.__logger.send_log(f"Thread {thread} is Complete. ")
                else :
                    reports.append((thread, "Error", f"[{datetime.datetime.now()}]"))
                    self.__logger.send_log(f"Thread {thread} had an Error. ")
        self.__coms.report_thread(reports)

    def kill_tasks(self):
        '''
            This function is set running to false. It is up to the user to makes sure the task stops running after that. 
        '''
        for thread in self.__threads: #pylint: disable=C0206
            self.__threads[thread][1].kill_Task() 
            self.__logger.send_log(f"Thread {thread} has been killed. ")

    def pass_request(self, thread, request):
        '''
            This function is ment to pass information to other threads with out the two threads knowing about each other.
            Bassically the requester say I want to talk to thread x and here is my request. This funct then pass on that requeset. 
            NOTE: threads go by the same name that you see on the display, NOT their class name. This is ment to be easier for the user,
            as they could run the code and see the name they need to send a request to.

            ARGS: 
                thread: The name of the thread as you see it on the gui, or as it is set in main.py
                request: index 0 is the function name, 
                        index 1 to the end is the args for that function.
                NOTE: even if  you are only passing one thing it needs to be a list! 
                    EX: ['funcName']
        '''
        with self.__request_lock:
            if len(request) > 0:
                temp = self.__threads[thread][1].makeRequest(request[0], args = request[1:])
            else :
                temp = self.__threads[thread][1].makeRequest(request[0])
        return temp
            
    def pass_return(self, thread, requestNum):
        '''
            This function is ment to pass the return values form a thread to another thread, without the threads having explicit knowlage of eachother. 
            ARGS:
                thread: The name of the thread as you see it on the gui, or as it is set in main.py
                requestNum: the number that you got from passReequests, this is basically your ticket to map info back and forth.
        '''
        with self.__request_lock:
            temp = self.__threads[thread][1].getRequest(requestNum)
        return temp
