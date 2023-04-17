import time
import hashlib
from functools import reduce
import keyboard
import math
import random


intercept = lambda data, bit: int(data - (data // (2**bit))*(2**bit))

def state_refresh_func(pool):
    pool_size = len(pool)
    if pool_size == 128:
        feedback_poly = [128,103,76,51,25,1]
    elif pool_size == 32:
        feedback_poly = [32,26,20,14,7,1]
    new = sum([pool[i-1] for i in feedback_poly])
    new = intercept(new,32)
    pool = pool[:-1]
    pool.insert(0, new)
    return pool

def mixing_func(pool, sample):
    pool_size = len(pool)
    feedback_poly = [0, -1]
    for i in range(4):
        feedback_poly.append(random.randint(2,pool_size-1))
    new = sum([pool[i] for i in feedback_poly]) ^ sample
    new = intercept(new,32)
    pool = pool[:-1]
    pool.insert(0, new)
    return pool

def extract_func(pool):
    sha1 = hashlib.sha1()
    pool_size = len(pool)
    pool_in_bytes = bytearray()
    for i in range(0, pool_size):
        pool_in_bytes.append(pool[i] & 0xff)
    sha1.update(pool_in_bytes)
    five_word_hash = sha1.digest()
    new_pool = []
    for i in range(0, pool_size):
        new_pool.append(pool_in_bytes[i])
    for i in range(0, 20):
        pool = mixing_func(new_pool, int(five_word_hash[i]))
    ## end of feedback phase --> update of state
    second_sha1 = hashlib.sha1()
    for i in range(0, pool_size):
        pool_in_bytes.append(pool[i] & 0xff)
    iv = five_word_hash
    #tmp = int.from_bytes(iv, 'big') ^ int.from_bytes(pool_in_bytes[0:19], 'big')
    plaintext = pool_in_bytes
    second_sha1.update(plaintext)
    result_in_bytes = second_sha1.digest()
    result_unfold = []
    output = []
    for i in range(0, 20):
        result_unfold.append(result_in_bytes[i])
    for i in range(0, 8):
        output.append(result_unfold[i] ^ result_unfold[i+12])
    for i in range(8, 10):
        output.append(result_unfold[i] ^ result_unfold[i+2])
    ## end of extraction phase --> extract 10-byte output
    return pool, output



class noise_collector():
    def __init__(self,pool,entropy_count,entropy_thread, dif):
        self.entropy_count = entropy_count
        self.pool = pool
        self.entropy_thread = entropy_thread
        self.dif = dif
        self.collector()
        #print(self.pool)


    def entropy_estimation(self,time):
        if (self.entropy_count > self.entropy_thread):
            print("Entropy Count is enough, you can press ENTER to stop")
        else:
            dif_1 = self.dif[-1] - self.dif[-2]
            dif_2 = abs(dif_1 - (self.dif[-2] - self.dif[0]) )
            self.dif = self.dif[1:3]
            self.dif.insert(2, int(10000*time))
            self.pool = mixing_func(self.pool,int(10*self.dif[-1]))
            temp =  min(self.dif[-1],dif_1,dif_2)
            entropy_adding = lambda temp: 11 if (temp > 2**12) else ( 0 if (temp<2)  else int(math.log(temp,2)) )
            self.entropy_count += entropy_adding(temp)


    def collector(self):
        keyboard.hook( lambda e: self.entropy_estimation(time.perf_counter()))
        keyboard.wait('return')
            

class input_pool():
    #####
    ## ------------------------------
    ## features in input pool:
    ##    size : 128*32 bit = 512 bytes
    ##    pool : a pool with size 512 bytes 
    ##    entropy count
    ##    entropy thread: default to be 1000
    ## ------------------------------
    ## functions in input pool:
    ##    __init__  : initialize the input pool with entropy count = entropy thread
    ##    diffusion(entropy_thread) : noise souce -> input pool
    ##    transfer  : input pool -> output pool
    ## 


    def __init__(self):
        print('--------------------------------')
        print('Let us initialize input pool----')
        self.size = 128  
        self.pool = [0 for i in range(self.size)]
        self.entropy_thread = 1000
        self.entropy_count = 0
        print('please stop if entropy counter > thread')
        self.collector = noise_collector(self.pool, 0, self.entropy_thread, dif = [0,0,0])
        self.pool = self.collector.pool
        self.entropy_count = self.collector.entropy_count
        self.dif = self.collector.dif


    
    def diffusion(self, entropy_add):
        print('Entropy count', self.entropy_count)
        self.collector.entropy_thread = self.entropy_count + entropy_add
        self.collector.collector()
        new = self.collector.pool
        for e in new:
            self.pool = mixing_func(self.pool, e)
        #print(self.pool)
        self.entropy_count += self.collector.entropy_count 
        #print("333",self.entropy_count)


    def transfer(self):
        while (self.entropy_count <= self.entropy_thread):
            print("You need to collect at least extra ",self.entropy_thread-self.entropy_count," entropy from noise source" )
            self.diffusion(self.entropy_thread-self.entropy_count)
        self.pool, output = extract_func(self.pool)
        self.entropy_count -= 80
        return output
    


class output_pool():
    #####
    ## ------------------------------
    ## features in output pool:
    ##    size : 32*32 bit = 128 bytes
    ##    pool : a pool with size 128 bytes
    ##    entropy count
    ##    entropy thread : default to be 600
    ## ------------------------------
    ## functions in output pool:
    ##    __init__ : initialize the output pool
    ##    receive : input pool -> output pool
    ##    output : output pool -> user
    ## 

    def __init__(self):
        self.size = 32  # 32*32 bit = 128 bytes
        self.pool = [0 for i in range(self.size)]
        self.entropy_count = 0
        self.entropy_thread = 600

    def receive(self, output):
        self.entropy_count += 80
        new_e = 0
        for i in range(10):
            new_e += output[i] << (8*i)
        self.pool.append(new_e)

    def output(self):
        if self.entropy_count < self.entropy_thread:
            print("You need to collect at least extra ", self.entropy_thread-self.entropy_count ,"entropy from input pool" )
            return None
        self.pool, final_output = extract_func(self.pool)
        self.entropy_count -= 80
        return final_output
        

class Linux_RNG():
    #####
    ## ---------------------------
    ## features in Linux RNG:
    ##    input pool
    ##    output pool
    ## ---------------------------
    ## functions in Linux RNG:
    ##    __init__
    ##    diffusion: noise source -> input pool
    ##    transfer: input pool -> output pool
    ##    output: output pool -> outside

   
    def __init__(self):
        self.inputPool = input_pool()
        self.outputPool = output_pool()

    def diffusion(self, entropy_add):
        print('--------------------------------')
        print("Now let us diffute entropy from noise source into input pool----")
        self.inputPool.diffusion(entropy_add)
        #print(self.inputPool.entropy_count)

    def transfer(self):
        print('--------------------------------')
        print("Now let us transfer entropy from input pool to output pool----")
        output= self.inputPool.transfer()
        #print(self.inputPool.entropy_count)
        self.inputPool.entropy_count += self.outputPool.entropy_count
        self.outputPool.receive(output)
        self.inputPool.entropy_count -= self.outputPool.entropy_count
        print("entropy count at input pool is", self.inputPool.entropy_count)
        return output

    def output(self):
        print('--------------------------------')
        print("Now let us output our entropy")
        final_output = self.outputPool.output()
        while not final_output:
            self.transfer()
            final_output = self.outputPool.output()
        return final_output

        
    def run(self,nums):
        for i in range(nums):
            final_output = self.output()
            print("Now we get the result ----------------------------------")
            print("Now the Input pool has entroy counter to be", self.inputPool.entropy_count)
            print("Now the output pool has entropy counter to be", self.outputPool.entropy_count)
            print("This is 10-byte final output", final_output)



if __name__ == "__main__":
    RNG = Linux_RNG()
    RNG.run(3)
    #RNG.run()

	
