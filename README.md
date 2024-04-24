# Threading API Over view
This api is meant to make it so that the user doesn't have to worry about the complexities of threading when they wish to add new task, thread, operations, and functionality to cse projects that leverage this api. 

!["Api overview"](threadingAPI.png)

## Task Handler
This class is the bin that holds all the threads. It keeps a dictionary that holds the class object, thread, and a name for each thread that the system is running. It also allows for communication between threads. 

### Functions
1. `__init__`: This function sets up the basic class structure. One thing to note is that it expects to receive a `coms` variable with is the `messageHandler` class from the `logging_system_display_python_api`. It will automatically add this as a thread that needs to be run. 
2. `add_thread`: adds a thread to the dictionary. It does allow for args to be passed in if the user desire. 
3. `start`: starts the threads if the dictionary if they haven't been started yet. 
4. `get_thread_status`: check all threads to see how things are going.
5. `kill_Tasks`: sets threads `__RUNNING` vars to false. It is up to the user to make sure this ends the task.
6. `pass_request`: takes in a thread name and a list of args, the first index in the list should be the function name that the user wants to call. In additional args can be store after that first index in the list. It returns a request id. 
7. `pass_return`: takes in a thread name and a request id. Then checks to see if there is a return value for that request. If there is it returns that. Otherwise it returns None. 
8. `check request`: checks to see if a request has been completed. 
9. `add_thread_request_func` : you can call this function form other class (most often with the coms class) to add a new thread to the thread pool. 
Example:
```python
    self.__coms.send_request('task_handler', ['add_thread_request_func', self.process_gps_packets, f'processing data for {self.__name} ', self, [data_ready_for_processing]]) #start a thread to process data

```
10. `add_thread_request_no_report` : same as the function above, but turns off reporting.
Example:
```python
self.__coms.send_request('task_handler', ['add_thread_request_no_report', self.send_data, f'sending data for {self.__thread_name} ', self, [data_dict_copy]]) #start a thread to process data                            

```

## Thread Wrapper
This class is meant to be inherited by users class. It provides the implementations that `Task Handler` needs in order to run. 

### Functions
1. `__init__`: sets up locks and class structure. NOTE: this class does not use the `messageHandler`. That is left up to the user to decided if and how they would like to handling logging for their threads. 
2. `get_status`: Returns the status of the current thread. Notice the mutex lock, as multiple threads may request the status.
3. `set_status`: the child class calls this and passes the thread a status.
4. `get_running`: This returns the boolean `__RUNNING`, this is used to communicate if the thread should be active or not.
5. `kill_task`: sets `__RUNNING` to false, the user is responsible for making sure the task finishes. 
6. `make_request`: This function wants the function name to be called in the class. Then it adds it to the list of 
task to be done.
7. `get_request`: takes a request id, then checks to see if it has been completed. If it has it returns any return value from that task. Otherwise it returns none. 
8. `get_next_request`: Returns the next thing in the FIFO queue.
9. `complete_request`: adds the completed task to the dictionary `__completed_requests` with the `return_val` (what that task returned when completed) as the value in that dictionary.
10. `run`: repeatedly checks to see if there are task to be executed. If there are it executes them. 

# How To
This api is built to just work in as many cases as possible. (Or as many as Shawn could think of when writing it. So probably not that many...) Anyways, lets talk about a basic use case and move to more complex ones. 
## General use
If you want to just use the basic implementation of this just simple have your class inherit the `Thread Wrapper`. Just make sure to call `super().__init__()` so that the parent classes construct will be called. NOTE: if you want to have a class that runs continuously, you DO NOT have to implement a `run` function. A continuous `run` function is implemented by `Thread Wrapper`. However in many cases it may not be desirable to have a continuous `run` function. Thus the `run` function needs to be implemented by the users class. 
### Example of user class (Continuous run)
```python
from threading_python_api.threadWrapper import threadWrapper


class usersClass (threadWrapper):
    def __init__(self, coms=None):
        super().__init__()
        self.__coms = coms # The user will probably want a messageHandler class, but it is not strictly required.
        #Users code after this point.   
    def users_function:
        #user defines any number of functions.     
```
### Example of how to call user class  (Continuous run)
```python
from logging_system_display_python_api.messageHandler import messageHandler
from threading_python_api.taskHandler import taskHandler
from usersClass import usersClass

def main():
    coms = messageHandler() #make the message handler for internal coms

    threadPool = taskHandler(coms) #make the thread pool.

    userObj = usersClass(coms)

    threadPool.add_thread(userObj.run, 'Users class', userObj) # add the users class to the thread pool.

    threadPool.start()

    #keep the main thread alive for use to see things running. 
    running = True
    while running:
        try:
            threadPool.get_thread_status()
            time.sleep(0.35)
        except KeyboardInterrupt:
            running = False
        
    
    threadPool.kill_tasks()

```
Things to note about the example
1. to call the `users_function` some where in the code, and assuming that the the `messageHandler` class is call `self.__coms`, the function call would be: `self.__coms.send_request('Users class', ['users_function'])`
2. That the main thread needs to stay alive while other threads are running. In other words the main thread does not wait for all child threads to finish execution. That is the purpose of the `while running` loop.
3. `userObj.run` doesn't have to be the function that is pass to the `Task Handler`. Any function can be passed, for easy of reading the code I usually name it run. 

### Example of over riding parent class functions
```python
from threading_python_api.threadWrapper import threadWrapper


class usersClass (threadWrapper):
    def __init__(self, coms=None):
        super().__init__()
        self.__coms = coms # The user will probably want a messageHandler class, but it is not strictly required.
        #Users code after this point.   
    def users_function_with_args(args):
        #user defines any number of functions.   
    def run(args):
        #some desired user function
```
```python
from logging_system_display_python_api.messageHandler import messageHandler
from threading_python_api.taskHandler import taskHandler
from usersClass import usersClass

def main():
    coms = messageHandler() #make the message handler for internal coms

    threadPool = taskHandler(coms) #make the thread pool.

    userObj = usersClass(coms)

    threadPool.add_thread(userObj.run, 'Users class', userObj, args=args) # add the users class to the thread pool.

    threadPool.start()

    #keep the main thread alive for use to see things running. 
    running = True
    while running:
        try:
            threadPool.get_thread_status()
            time.sleep(0.35)
        except KeyboardInterrupt:
            running = False
        
    
    threadPool.kill_tasks()

```
Things to note about the example
1. This now overrides the `Thread Wrapper run` function. The user is now free to decide how to implement run.
2. The implementation of `main()` does not change, except for one parameter on the `add_thread` function call.
3. To call the `users_function_with_args` some where in the code, and assuming that the the `messageHandler` class is call `self.__coms`, the function call would be: `self.__coms.send_request('Users class', ['users_function_with_args',arg1, arg2, arg3, ...])`

## Compiling README.md with pandocs
    To compile .md to a pdf: pandoc -s README.md -V geometry:margin=1in -o README.pdf
    To compile to a stand alone html doc: pandoc  --metadata title="README" -s --self-contained README.md -o README.html

## Linting
This is the method that is used to check the code and make sure it fits coding stander and best practice. The package is called `pylint` and can be installed with \
``` python
    pip install pylint  
```
or 
```python
    pip3 install pylint 
```
depending on context. The command to run `pylint` is:
```python
    python3 -m pylint --jobs 0 --rcfile .pylintrc <name of python file or folder>
```