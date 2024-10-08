'''
    This module handles all the threads and running them. 
'''
import threading
import time
import datetime
from logging_system_display_python_api.logger import loggerCustom # pylint: disable=import-error

#import DTO for communicating internally
from logging_system_display_python_api.DTOs.logger_dto import logger_dto # pylint: disable=import-error
from logging_system_display_python_api.DTOs.print_message_dto import print_message_dto # pylint: disable=e0401


class taskHandler():
    '''
        This class is what collects all the task and then runs them. It also checks on the status of every class. 
        The status is set by using the following command: super().setStatus("Running"). When ever a task is created it 
        is given the status of "NOT STARTED". When it is finished it is given the status of "Complete". If the task every 
        crashes it should return a status of "Error". Remember that the status of "Running" and "Complete" should be set 
        by the user. With the one exception of "Running" when the users just uses the prebuilt run function implemented in 
        `threadWrapper`.

        The general function of this class is that it implements a threading api as follows. First a thread is added use 
        add_thread. NOTE: This only adds the thread to a dictionary. It DOES NOT start the thread at this time. To start
        all the threads the user then calls the `start` function. This will start all threads in the dictionary. It
        can all be called multiple times with out fear of conflict. 

        For messaging there are the `pass_request` and `pass_return` functions. These functions are implemented by the 
        `messageHandler` in the `logging_system_display_python_api`. However if the user  wish to not use that api, or 
        implement themselves here is how they work. The `pass_request` takes in a thread name and then access that thread
        and pass the function name and args to it. The `pass_return` return then checks to see if the task has completed 
        the request and returns None or the value from the task.
    '''
    def __init__(self, coms, task_handler_name = 'task_handler', coms_name:str = 'coms'):
        self.__threads = {}
        self.__coms = coms 
        self.__logger = loggerCustom("logs/taskHandler.txt")
        self.__thread_dict_lock = threading.Lock()
        self.add_thread(self.__coms.run, coms_name, self.__coms)
        self.__completed_tasks = {}
        self.__name = task_handler_name
        self.__func_map = {
            'add_thread_request_func' : self.add_thread_request_func,
            'add_thread_request_no_report' : self.add_thread_request_no_report
        }
    def add_thread(self, runFunction, taskID, wrapper, args = None, report = True):
        ''''
            This function takes a taskID (string) and a run function (function to start the thread)
            It then starts a thread and adds it to the dictionary of threads. 
            In side the dictionary it holds the threads. 
        '''

        if self.__thread_dict_lock.acquire(timeout=10): # pylint: disable=R1732
            copy_thread_dict = self.__threads.copy()
            self.__thread_dict_lock.release()
        else :
            raise RuntimeError('Could not aquire thread dict lock')
        if args is None:
            copy_thread_dict[taskID] = (threading.Thread(target=runFunction), wrapper, report)
            dto = print_message_dto(f"Thread {taskID} created with no args. ")
            self.__coms.print_message(dto)
            self.__logger.send_log(f"Thread {taskID} created with no args. ")
        else :
            copy_thread_dict[taskID] = (threading.Thread(target=runFunction, args=args), wrapper, report)
            dto = print_message_dto(f"Thread {taskID} created. ")
            self.__coms.print_message(dto)
            self.__logger.send_log(f"Thread {taskID} created. ")
        if self.__thread_dict_lock.acquire(timeout=10): # pylint: disable=R1732
            self.__threads = copy_thread_dict.copy()
            self.__thread_dict_lock.release()
        else :
            raise RuntimeError("Could not aquire thread dict lock")
    def start(self, check=True, thread = ''):
        '''
            starts all the threads in the threads dictionary
        '''
        if self.__thread_dict_lock.acquire(timeout=10): # pylint: disable=R1732
            copy_thread_dict = self.__threads.copy()
            self.__thread_dict_lock.release()
        else : 
            raise RuntimeError("Could not aquire thread dict lock")
        if check :
            for thread_stored in copy_thread_dict: #pylint: disable=C0206
                if copy_thread_dict[thread_stored][1].get_status() == "NOT STARTED":
                    copy_thread_dict[thread_stored][0].start() #start thread
                    copy_thread_dict[thread_stored][1].set_status('STARTED')
                    dto = print_message_dto(f"Thread {thread_stored} started. ")
                    self.__coms.print_message(dto)
                    self.__logger.send_log(f"Thread {thread_stored} started. ")
        else :
            self.__threads[thread][0].start()
    def get_thread_status(self):
        '''
            Gets the thread status, then sends message to the `Message handler class`
        '''
        if self.__thread_dict_lock.acquire(timeout=10): # pylint: disable=R1732
            temp_thread_dict = self.__threads.copy()
            self.__thread_dict_lock.release()
        else : 
            raise RuntimeError("Could not acquire thread dict lock")
        reports = [] # we need to pass a list of reports so the all get displayed at the same time. 
        for thread in temp_thread_dict: #pylint: disable=C0206 disable=R1702
            if temp_thread_dict[thread][2]: #check to see if the thread wants to be reported
                if temp_thread_dict[thread][0].is_alive():
                    dto = logger_dto(time=datetime.datetime.now(), message="Is Running")
                    reports.append((thread, dto, "Running"))
                else :
                    if temp_thread_dict[thread][1].get_status() == "Complete":
                        try:
                            doneTime = self.__completed_tasks[thread]
                            # print(f"{datetime.datetime.now().timestamp()} {doneTime.timestamp()}")
                            if (int (datetime.datetime.now().timestamp()) - int (doneTime.timestamp())) > 5 : # five second time out
                                del self.__completed_tasks[thread]
                        except : # pylint: disable=w0702
                            self.__completed_tasks[thread] = datetime.datetime.now()
                            doneTime = self.__completed_tasks[thread]
                        
                        dto = logger_dto(time=doneTime, message="Complete")
                        reports.append((thread, dto, 'Complete'))
                    else :
                        dto = logger_dto(time=datetime.datetime.now(), message="Error Occurred")
                        reports.append((thread, dto, 'Error'))
                        self.__logger.send_log(f"Thread {thread} had an Error. ")
        self.__coms.report_thread(reports)
    def kill_tasks(self):
        '''
            This function is set running to false. It is up to the user to makes sure the task stops running after that. 
        '''
        if self.__thread_dict_lock.acquire(timeout=10): # pylint: disable=R1732
            temp_thread_dict = self.__threads.copy()
            self.__thread_dict_lock.release()
        else : 
            raise RuntimeError("Could not acquire thread dict lock")
        for thread in temp_thread_dict: #pylint: disable=C0206
            temp_thread_dict[thread][1].kill_Task()
            while temp_thread_dict[thread][0].is_alive():
                print(f" Killing thread: {thread} If the thread doesn't shut down make sure it is not a zombie thread. A.K.A the thread had an earlier error, and then kept running but is no longer responding to commands from the system. ")
                time.sleep(1)
            self.__logger.send_log(f"Thread {thread} has been command to be killed. ")
    def pass_request(self, thread, request):
        '''
            This function is meant to pass information to other threads with out the two threads knowing about each other.
            Basically the requester say I want to talk to thread x and here is my request. This func then pass on that request. 
            NOTE: threads go by the same name that you see on the display, NOT their class name. This is meant to be easier for the user,
            as they could run the code and see the name they need to send a request to.

            ARGS: 
                thread: The name of the thread as you see it on the gui, or as it is set in main.py
                request: index 0 is the function name, 
                        index 1 to the end is the args for that function.
                NOTE: even if  you are only passing one thing it needs to be a list! 
                    EX: ['funcName']
        '''
        if self.__thread_dict_lock.acquire(timeout=10): # pylint: disable=R1732
            copy_thread_dict = self.__threads.copy()
            self.__thread_dict_lock.release()
        else : 
            raise RuntimeError("Could not aquire thread dict lock")
        try :
            if len(request) > 0:
                if self.__name == thread:
                    temp = self.__func_map[request[0]](request[1:])
                else : 
                    temp = copy_thread_dict[thread][1].make_request(request[0], args = request[1:])
            else :
                if self.__name == thread: 
                    temp = self.__func_map[request[0]]()
                else : 
                    temp = copy_thread_dict[thread][1].make_request(request[0])
        except Exception as e: #pylint: disable=W0718
            temp = f"Error in calling thread {request[0]}: {e}"
        return temp 
    def pass_return(self, thread, requestNum):
        '''
            This function is meant to pass the return values form a thread to another thread, without the threads having explicit knowledge of each other. 
            ARGS:
                thread: The name of the thread as you see it on the gui, or as it is set in main.py
                requestNum: the number that you got from passRequests, this is basically your ticket to map info back and forth.
        '''
        if self.__thread_dict_lock.acquire(timeout=10): # pylint: disable=R1732
            copy_thread_dict = self.__threads.copy()
            self.__thread_dict_lock.release()
        else : 
            raise RuntimeError("Could not aquire thread dict lock")
        try : 
            temp = copy_thread_dict[thread][1].get_request(requestNum)
        except Exception as e: #pylint: disable=W0718
            temp = f"Error in calling thread {thread}: {e}"
        return temp 
    def check_request(self, thread, requestNum):
        '''
            This function is for the small set of case where it is necessary to check and see if the request has completed as
            apposed to checking the return val. 

            Input:
                thread
                requestNum
            output:
        '''
        if self.__thread_dict_lock.acquire(timeout=10): # pylint: disable=R1732
            copy_thread_dict = self.__threads.copy()
            self.__thread_dict_lock.release()
        else : 
            raise RuntimeError("Could not aquire thread dict lock")
        try :
            temp = copy_thread_dict[thread][1].check_request(requestNum)
        except Exception as e: #pylint: disable=W0718
            temp = f"Error in calling thread {thread}: {e}"
        return temp
    def add_thread_request_func(self, args):
        '''
            This function is so that other class who dont know about the thread handler can send a request to start a new thread. (The gui display uses this.)

            ARGS:
                args[0] : function to run
                args[1] : the name you want the thread to have
                args[2] : the class object of the thread. (Must inherit form the threadWrapper class)
                args[3] : any args to be passed into the thread. 
        '''
        runFunction = args[0]
        taskID = args[1]
        wrapper = args[2] 
        if len(args) > 3 : 
            thread_args = args[3]
        else : 
            thread_args = None

        #add the thread 
        self.add_thread(runFunction, taskID, wrapper, args = thread_args)      
        #start the thread
        self.start(check=False, thread=taskID) 
        return True #this is 
    def add_thread_request_no_report(self, args):
        '''
            This function is so that other class who dont know about the thread handler can send a request to start a new thread. (The gui display uses this.)
            The thread added with this function will not be reported on the threading report.

            ARGS:
                args[0] : function to run
                args[1] : the name you want the thread to have
                args[2] : the class object of the thread. (Must inherit form the threadWrapper class)
                args[3] : any args to be passed into the thread. 
        '''
        runFunction = args[0]
        taskID = args[1]
        wrapper = args[2] 
        if len(args) > 3 : 
            thread_args = args[3]
        else : 
            thread_args = None

        if self.__thread_dict_lock.acquire(timeout=10): # pylint: disable=R1732
            if taskID in self.__threads:
                raise RuntimeError(f"Thread with id {taskID} already exists.")
            self.__thread_dict_lock.release()
        else : 
            raise RuntimeError("Could not aquire thread dict lock")
        
        #add the thread 
        self.add_thread(runFunction, taskID, wrapper, args = thread_args, report=False)      
        #start the thread
        self.start(check=False, thread=taskID) 
        return True #this is 
