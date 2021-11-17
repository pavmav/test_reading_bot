
import threading
import time
import pickle

def test_function(my_args):
    for i in range(5):
        print(time.time())
        time.sleep(2)

def my_inline_function():
    #do some stuff
    download_thread = threading.Thread(target=test_function, args=['my_args'])
    download_thread.start()
    #continue doing stuff
    print('Do some stuff')
    time.sleep(2)
    print('Do another stuff')

#my_inline_function()

#with open('OneCityDictOfUsers.pickle', 'wb') as f:
#    pickle.dump({}, f)