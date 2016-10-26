#coding:utf-8
import sqlite3



class dbOperator(object):
	'''more abstract api to db'''
	def __init__(self,dbPath='PhyLabMS.db'):
	    self.conn=sqlite3.connect(dbPath,check_same_thread=False)
	    self.cu = self.conn.cursor() 
		# to connect to the database as start

	def commit(self): #just a shortcut
		self.conn.commit()

	def finish(self):#finish this process
	    print('Finish, thanks for using.')
	    self.conn.commit()
	    self.conn.close()

	    #This function
	def cvt(self,a): #cvt a is str or int, convert str to 'str', int to str(int)
	    if type(a)==int:
	        return str(a)
	    else:
	        return '\''+str(a)+'\''


	def refresh(self): # Refresh the cursor to avoid the 'database locked' bug
		self.cu.close()
		self.cu=self.conn.cursor()

	def select(self,tblName):
	    self.refresh()
		# return all the records from the table in the form of a list of tuples
	    self.cu.execute("select * from "+tblName)
	    return self.cu.fetchall()

	def insert(self,tblName,values=[],headers=[]):
		self.refresh()
		if headers==[]:
			#no headers means all headers
			headerStr=''
		else:
		    headerStr='(' #start from left bracket
		    for d in headers:
		    	headerStr+=self.cvt(d)+',' # add the converted string with ','
		    headerStr=headerStr[:-1] # delete the last ','
		    headerStr+=')' # and finish with )
		insertStr="("  #same as above
		for d in values:
		    insertStr+=self.cvt(d)+','
		insertStr=insertStr[:-1]
		insertStr+=')'
		Query='insert into '+tblName+headerStr+' values '+insertStr
		try:
			self.cu.execute(Query)
		except Exception as e:
			print(e)
		self.commit()


	def update(self,tblName,updateName,updateValue,pkVal,pkName='name'):
		self.refresh()
		Query='update '+tblName+' set '+updateName+'='+self.cvt(updateValue)+' where '+pkName+'='+self.cvt(pkVal)
		try:
			self.cu.execute(Query)
		except Exception as e:
			print(e)
		self.commit()


	def delete(self,tblName,pkVal,pkName='name'): #name is pk value
	    #print 'update '+tblName+' set '+valName+'='+cvt(value)+' where name='+cvt(name)
	    self.cu.execute('delete from '+tblName+' where '+pkName+'='+self.cvt(pkVal))
	    self.commit()

dbp=dbOperator()


# name is always the primaryKey
class appliance(object): 
	'''
	appliance: name-num-pos
	ORM from table 'appliance' to a class

	'''
	def __init__(self,name,num=0,pos='free'):
		self.name=name
		self.num=num
		self.pos=pos # init the fields
		self.db=dbp
		
	def insert(self):	
		self.db.insert('appliance',[self.name,self.num,self.pos])
		# if this object is new created, it will be inserted

	def __repr__(self):
		return self.name+str(self.num)
		# represent itself
		# mainly used for test

class query(object):
	'''
	query:qid-user-time-state

	'''
	def __init__(self,user,time=0.0,state=0):
		self.db=dbp
		#just means auto-increment, this way is not elegent and will being deleted
		# self id is auto-increment
		self.user=user
		self.time=time
		self.state=state
		self.qid=-1 #initialize this value
		found=False

		for i in self.db.select('query'):
			if i[1]==self.user and i[2]==self.time:
				self.qid=int(i[0])
				found=True
				# check if the query is already in table and get the queryID of it
		if not found:
			# bug comes from this position
			self.insert()
			self.qid=self.db.select('query')[-1][0] #must be inserted in the last one so the qid can be get this way



	def insert(self):
		self.db.insert('query',[self.user,self.time,self.state],['user','time','state']) #do not add headers becaz it will make qid not generated

	def check(self):
		IU=self.db.select('queryIU')
		ready=self.db.select('ready')
		for iu in IU:# search for ready, if not found, false, if found and not enough, false, else, true
			if iu[0]==self.qid:
				name=iu[1]
				num=iu[2]
				found=False
				for r in ready:
					if r[0]==name:
						found=True 
						if r[1]<=num:
							return False # If not enough, return false 
				if not found:
					return False # If not found return false
		return True # Else, if no condition with 'return false', then return true

	def update(self): #update the state to true
		self.db.update('query','state','1',pkVal=self.qid,pkName='qid')
		self.state=1 #added

	def check_and_update(self):
		if self.check():
			self.update() # Check whether state is 1 and update the query







class queryIU(object):
	'''
	queryIU: qid-name-num

	'''

	def __init__(self,qid,name,num):
		self.qid=qid # foreign key to Query
		self.db=dbp
		self.name=name
		self.num=int(num)

	def insert(self):
		self.db.insert('queryIU',[self.qid,self.name,self.num])

class mission(object):

	'''
	mission: name-num-type

	'''

	def __init__(self,name,num,mType):
		self.db=dbp
		self.name=name
		self.num=num
		self.type=mType	
		
	def insert(self):
		self.db.insert('mission',[self.name,self.num,self.type])
    

	def missionFinished(self):
		if self.type=='Ready': # for ready, appliance come to ready
			self.getReady()

		elif self.type=='Buy': # for buy, delete from buy and come to ready, also update the Tappliances
			self.getReady()
			self.db.delete('buy',self.name)
 #adding new to database
			self.db.update('appliance','num',self.num,self.name)

		elif self.type=='Back': # for back, remove from ready
			self.db.delete('ready',self.name)
			
	def getReady(self): # update the 'ready' table according to the mission finished
		found=False
		ready=self.db.select('ready')
		for r in ready:
			if r[0]==self.name:
				self.db.update('ready','num',self.num+int(r[1]),self.name)
				found=True # If the appliances are already here, then just update the number
		if not found:
			self.db.insert('ready',[self.name,self.num]) # Else, insert a new value into table 'ready'



	def __repr__(self):
		return self.name+str(self.num)+self.type # used for blackbox testing








class user(object):
	'''
	user:username-passwd-admin

	'''

	def __init__(self,userID,passwd=0,admin=0): # default value of passwd=0 which means this user do not have passwd
		self.name=userID #ID is your name
		self.passwd=passwd#Teacher do not have a  passwd
		self.admin=admin #0 is false,1 is true
		self.db=dbp

	def insert(self):
		self.db.insert('user',[self.name,self.passwd,self.admin])
		# access: 0teacher,1administrator


#class finished


def manualEntryApp(name,num,pos): # for manual entering the appliances
	added=appliance(name,num,pos)
	added.insert()

def userSignUp(userID):  # Sign up a user as a teacher
	userAdded=user(userID)
	userAdded.insert()


def userLogIn(userID,password=0): #First enter the userID
	i=dbp.cu.execute('select * from user where name='+dbp.cvt(userID)).fetchall()
	if len(i)==0:
		return 0

	try:
		u=user(i[0],i[1],i[2])
	except:
		u=user(i[0])
	if u.name==userID:
		if u.admin==1:
			if password==u.passwd:
				currentUser=u
				return 1
			else:
				return 0

	else:
		currentUser=u
		return 1



def queryEntry(time,qIU):#qiu=[[],[]]
	queryA=query(currentUser,time,0) #A=added
	returnVal=queryIUEntry(queryA.qid,qIU)
# Do not forget default values in init, this is not SQL
	#test

	if returnVal==1:
		print('Successfully added.')
	else:
		print('Query input error.')



def queryIUEntry(qid,qIU):
	# qiu, a list of list or tuple which in form [name,num]
	for qiu in qIU:
		if qiu[1].isdigit():
			this=queryIU(qid,qiu[0],qiu[1])
			this.insert()
		else:
			return 0 # If an input error is catched, return 0
	return 1 # If no error catched, return 1


def formIR(): # form Ideal_Ready
	TqueryIU=[]
	TqIU=dbp.select('queryIU')
	
	for tq in TqIU:
		TqueryIU.append(queryIU(tq[0],tq[1],tq[2]))
	ideal_ready=[]
	# this list is formed then all items in this list are inputed in database
	dbp.cu.execute('drop table ideal_ready') # start the table with truncate
	dbp.cu.execute('create table ideal_ready(name varchar(20),num int)')

	# if the appliance is already in ideal_ready, just update the number of it
	for qiu in TqueryIU:
		found=False
		for aim in ideal_ready:
			if aim[0]==qiu.name:
				aim[1]+=qiu.num #update the number
				found=True 
		if not found:
			ideal_ready.append([qiu.name,qiu.num]) # Just adding
	
	#finally, update the database
	for r in ideal_ready:
		dbp.insert('ideal_ready',r)



def compareIR2R(): #means compare ideal-ready to ready and then form the table 'mission'
	dbp.cu.execute('drop table mission') # start the table with truncate
	dbp.cu.execute('create table mission(name varchar(20),num int,type varchar(10))')
	Tready=dbp.select('ready')
	Tiready=dbp.select('ideal_ready')
	for aim in Tiready:
		found=False # default not founded
		for ain in Tready:
			if ain[0]==aim[0]: # If the names are the same
				found=True
				if aim[1]>ain[1]:# if the numbers are not the same
					getReady(aim[0],aim[1]-ain[1]) 
		if not found:
			getReady(aim[0],aim[1]) # If not found, just prepare for them all


def getReady(name,num): #Function to form the mission table
	Tappliances=[appliance(i[0],i[1],i[2]) for i in dbp.select('appliance')]
	found=False # default not in appliances
	for a in Tappliances:
		if a.name==name:
			found=True
			if a.num>=num: # if the current appliances are enough
				newMission('Ready',a.name,a.num) # Just get ready
			else:# else if the current appliances are not enough
				if a.num!=0: # if num is 0, no ready mission is needed.
					newMission('Ready',a.name,a.num) # Get them allready and
				newMission('Buy',a.name,num-a.num) # Buy some
	if not found: # if not found, buy them
		newA=appliance(name,0) # first, entry this appliance to appliance table with number 0
		newA.insert()
		newMission('Buy',name,num) # Buy them all



def newMission(Type,name,num): # this function is just used for inserting a new mission in table 'mission'
	newM=mission(name,num,Type)
	newM.insert()
	if newM.type=='buy': # if the type of this mission is buy, then the name and number of appliance is inserted into table 'buy'
		mission.db.insert('buy',[name,num])

def missionGenerate():
	formIR()
	compareIR2R()







currentUser=user('Tester')




def test2():
	u=input()
	return userLogIn(u)

def test3():
	print('start test3')
	u=input('Name:')
	p=input('Passwd:')
	return userLogIn(u,p)

def test1():
	u=input()
	return userLogIn(u)

def test4():
	sets=int(input('num of query:'))
	for i in range(sets):
		quser=input('user:')
		qtime=float(input('time:'))
		q=query(quser,qtime) #query is self_inserted
		sets2=int(input('num of query IU:'))
		for i in range(sets2):
			qname=input('name:')
			qnum=int(input('num:'))
			qiu=queryIU(q.qid,qname,qnum)
			qiu.insert()
	for i in q.db.select('query'):
		print(i)
	print('')
	for i in q.db.select('queryIU'):
		print(i)

def test5():
	sets=int(input('num of query:'))
	for i in range(sets):
		quser=input('user:')
		qtime=float(input('time:'))
		q=query(quser,qtime)
		q.insert()
		sets2=int(input('num of query IU:'))
		for i in range(sets2):
			qname=input('name:')
			qnum=int(input('num:'))
			qiu=queryIU(q.qid,qname,qnum)
			qnum=int(input('num:'))
			qiu=queryIU(q.qid,qname,qnum)
	missionGenerate()
	for i in dbp.select('mission'):
		print(i)

def test6():
	missionList=[]
	index=0
	for i in dbp.select('mission'):
		print(index,i)
		index+=1
		missionList.append(mission(i[0],i[1],i[2]))
	sets=int(input('number of mission finished'))
	for i in range(sets):
		index=int(input('index of mission'))
		missionList[index].missionFinished()
	for i in dbp.select('ready'):
		print(i)
	for i in dbp.select('query'):
		i=query(i[1],i[2],i[3])
		i.check_and_update()
		print(i.qid,i.state)

# for i in dbp.select('user'):
# 	print(i)
# dbp.insert('user',['zhang','tagtag',1])
# print(test3())

# print('Start Test 1')
# test1()

def test7():
	print('Start Test7')
	time_testdata=0
	name=input()
	num=input()
	qiu=[[name,num]]
	queryEntry(time_testdata,qiu)

def test8():
	n=int(input('Enter the number of queryIUs:'))
	qiu=[]
	for i in range(n):
		name=input()
		num=input()
		qiu.append([name,num])
	queryEntry(0,qiu)
	missionGenerate()
	index=0
	for i in dbp.select('mission'):
		print(index,i)
		index+=1
		finish_or_not=input('finished?')
		if finish_or_not!='':
			i=mission(i[0],i[1],i[2])
			i.missionFinished()

	print('Now present contents in ready')
	for i in dbp.select('ready'):
		print(i)

	print('Now present the state of query')
	selected=dbp.select('query')[-1]
	selected_query=query(selected[1],selected[2])

	selected_query.check_and_update()
	print(selected_query.state)





















































