import simpy
import random
class Resturant:
    def __init__(self,env):
        self.tables=simpy.Resource(env, capacity=2)
        self.jugs=simpy.Resource(env, capacity=4)
        self.dispenser=simpy.Container(env, init=3, capacity=5)
        self.mon_dispenser=env.process(self.switch_can(env))
        self.money=simpy.Container(env, init=0, capacity=100)

    def switch_can(obj,env):
        while True:
            if obj.dispenser.level<2:
                print("Refilling dispenser at ",env.now)
                amt=obj.dispenser.capacity-obj.dispenser.level
                obj.money.get(2)
                print(obj.money.level)
                yield obj.dispenser.put(amt)
                print(obj.dispenser.level)
                yield env.timeout(5)
            yield env.timeout(1)
        
    def mon_jug(obj,env,name):
            while True:
                yield env.timeout(8)
                print('A jug for customer',name,'is being refilled at', env.now)
                yield obj.dispenser.get(1)
            yield env.timeout(1)

    def run(obj, name, env):
            print('Customer',name,'coming at ',env.now)
            if obj.tables.count==obj.tables.capacity:
                 print("No tables free at ",env.now)
            with obj.tables.request() as tab:  
                yield tab
                env.process(obj.mon_jug(env,name))
                print('Customer', name, 'is being led to their table at',env.now)
                with obj.jugs.request() as jug:  
                    yield jug
                    yield env.timeout(1)
                    yield env.process(obj.order(name,env))
                    print('Customer',name,'paid the bill and is leaving at',env.now)

    def order(obj, name, env):
            alive=1
            bill=0
            od=1
            while True:
                print('Customer',name,' has started ordering at',env.now)
                yield env.timeout(10)
                print('Customer',name,'has finished ordering at',env.now)
                cl=random.randint(0,1)
                cl_time=random.randint(1,30)
                print(cl,cl_time)
                cancelling=env.process(obj.cancel(env,name,cl_time,od))
                food_arrived=env.process(obj.fd_arr(env,name,bill))

                if cl==1:
                    if cl_time>=10:
                        cancelling.interrupt('cannot cancel')
                        yield env.timeout(cl_time)
                        print('Customer',name,'wants to cancel order',od)
                        print('Customer',name,'order cannot be cancelled at',env.now)
                else:
                    cancelling.interrupt('cannot cancel')
                if (cl==1) & (cl_time<10):
                    yield cancelling|food_arrived
                else:
                    yield food_arrived
                     
                if food_arrived.triggered==False:
                    food_arrived.interrupt('Customer wants to cancel order')
                yield env.timeout(1)

                alive=random.randint(0,1)
                if alive==1:
                    print('Customer',name,'wants to order again at',env.now)
                    od=od+1
                    continue
                else:
                    print('Customer',name,'does not want to order anymore at',env.now)
                    yield env.process(obj.payment(env,name,food_arrived.value))
                    break

    def cancel(obj,env,name,cl_time,od):
        fl=0
        try:
            yield env.timeout(cl_time)
            print('Customer',name,'wants to cancel order',od,'at',env.now)
        except simpy.Interrupt as j:
            yield env.timeout(1)

    def fd_arr(obj,env,name,bill):
        try:
            yield env.timeout(20)
            print('Customer',name,' food arrived at',env.now)
            yield env.timeout(30)
            bill=bill+random.randint(1,3)
            return bill
        except simpy.Interrupt as i:
            print('Order for Customer',name,'has been interrupted because',i.cause)
            return bill
                     
    def payment(obj,env,name,sum):
        print('Customer', name, 'total bill is',sum,'at',env.now)
        if sum!=0:
            yield obj.money.put(sum)
            yield env.timeout(5)
     

def customer_gen(obj,env):
        for i in range (4):
            env.process(obj.run(i, env))
            yield env.timeout(5)

env=simpy.Environment()
obj = Resturant(env)
cust=env.process(customer_gen(obj,env))
env.run(until=200)
