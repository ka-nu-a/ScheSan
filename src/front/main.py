import os
import random
import discord
import datetime
from dateutil import parser

MODE_LIST = {'TEST':'TEST', 'PROD':'PROD'}
MODE = MODE_LIST['TEST']
PREFIX = '?'
ADMIN_ID = os.environ['DISCORD_ADMIN_ID']
TOKEN = os.environ['DISCORD_BOT_TOKEN']

client = discord.Client()
OUTPUT_CHANNEL = None
EMOJI_LIST = {1:'\U00000031\U0000fe0f\U000020e3', 2:'\U00000032\U0000fe0f\U000020e3', 3:'\U00000033\U0000fe0f\U000020e3', 4:'\U00000034\U0000fe0f\U000020e3', 5:'\U00000035\U0000fe0f\U000020e3', 6:'\U00000036\U0000fe0f\U000020e3', 7:'\U00000037\U0000fe0f\U000020e3', 8:'\U00000038\U0000fe0f\U000020e3', 9:'\U00000039\U0000fe0f\U000020e3', 10:'\U0001F51F', 'close':'\U00002705', 'chancel':'\U0000274C'}
INDEX_LIST = {1:'①', 2:'②', 3:'③', 4:'④', 5:'⑤', 6:'⑥', 7:'⑦', 8:'⑧', 9:'⑨', 10:'⑩'}

def isTestMode():
	return MODE == MODE_LIST['TEST']

class schedule:
	capa = None # 募集定員
	owner = None # 募集者
	limit = None # 募集期限
	channel = None # 募集をかけるチャンネル
	#choosen = None # list 各選択肢の選ばれている数
	message = None # 募集メッセージ本文
	messageByBot = None # 募集メッセージ(bot投稿)のID
	fncSendMessage = None # メッセージ送信関数
	isClosed = False # Close済みかどうか
	
	def __init__(self, owner, message, fncSendMsg, channel=OUTPUT_CHANNEL, limit=None, *args):
		self.owner = owner
		self.message = message
		self.fncSendMessage = fncSendMsg
		self.channel = channel
		self.parse(message)
		debug(f'owner is {self.owner}')
	
	def parse(self, message):
		# メッセージ内容をパースして、class内の引数に代入(initでやっているようなことをする)
		tmpStr = message.split('\n')
		self.message = tmpStr[0]
		self.capa = int(tmpStr[0][tmpStr[0].find('@')+1])+1 if tmpStr[0].find('@') != -1 else 99999
		for i,c in enumerate(tmpStr[1:],1):
			if(c[0] == '〆'):
				debug('find 〆!')
				self.limit = parser.parse(c[1:].strip(':').strip(' ').strip(':'))
				break
			self.message += f'\n{INDEX_LIST[i]}: {c}'
			if(i>=10):
				debug('max choose')
				break
		debug(f'capa: {self.capa}\nmessage: {self.message}')
		#if self.limit == None:
			#self.limit = datetime.datetime.today()+datetime.timedelta(days=1)
	
	async def send(self):
		if(self.capa < 1):
			debug('ERROR: 有効な募集人数を入力してください。')
			await self.chancel()
		self.messageByBot = await self.fncSendMessage(self.message+f'\n\n{"〆:"+self.limit.strftime("%m/%d %H:%M") if self.limit != None else ""}', channel=self.channel, reactions = self.reactionCreater(self.message.count('\n')))
	
	def reactionCreater(self, n):
		reactionList = []
		for n in range(n):
			reactionList.append(EMOJI_LIST[n+1])
		reactionList.append(EMOJI_LIST['close'])
		reactionList.append(EMOJI_LIST['chancel'])
		return (reactionList)
	
	async def close(self):
		#await self.messageByBot.clear_reactions()
		self.isClosed = True
		await self.notifiction()
		debug('close done.')
	
	async def notifiction(self): # 募集完了した際に、参加者にメンション＆決定した選択肢を伝える
		pass
	
	async def chancel(self):
		await self.messageByBot.delete()
		debug('delete done.')

schedules = []

async def createSchedule(owner, message, channel=OUTPUT_CHANNEL):
	if OUTPUT_CHANNEL is not None:
		debug('use advance output channel')
		channel = OUTPUT_CHANNEL
	schedules.append(schedule(owner, ' '.join(message[1:]), sendMessage, channel))
	await schedules[-1].send()
	return ''

async def addReactions(message, reactions):
	for reaction in reactions:
		await message.add_reaction(reaction)

async def sendMessage(message, channel=OUTPUT_CHANNEL, reactions=''):
	if message == '':
		return
	if channel == '':
		debug(f'ERROR: cant send message ({message})')
		return
	debug(f'[SEND_MESSAGE]\n{message}')
	sendedMsg = await channel.send(str(message))
	if reactions != '':
		await addReactions(sendedMsg, reactions)
	return sendedMsg

def debug(message):
	print(message+'\n')

def isAdmin(author):
	#return (author.id == ADMIN_ID) or (author.top_role.permissions.administrator)
	return (author.id == ADMIN_ID)

async def doEval(message):
	debug('doEval')
	if isAdmin(message.author):
		await eval(message.content[3:])
		return 'Success.'
	else:
		return 'ERROR: This Command can only Administrator.'

async def setOutputChannel(message):
	debug('set output Channel')
	if isAdmin(message.author):
		global OUTPUT_CHANNEL
		channel = client.get_channel(int(message.content[3:]))
		if(channel is None):
			return f'ERROR: channel {message.content[3:]} is Invalid!'
		OUTPUT_CHANNEL = channel
		return f'Set Output Channel is {OUTPUT_CHANNEL.name}'
	else:
		return 'ERROR: This Command can only Administrator.'

@client.event
async def on_ready():
	print(f'Bot Booting "{MODE}" Mode...')

@client.event
async def on_message(message):
	if message.author.bot:
		return
	if message.content == '': # 画像をアップロードしただけの場合など
		return
	
	if message.content[0] == PREFIX:
		COMMAND_LIST = {
			'b': lambda m,c: createSchedule(m.author.id, c, m.channel),
			'e': lambda m,c: doEval(m),
			's': lambda m,c: setOutputChannel(m),
	}
		
		command = message.content[1:].split(' ')
		if command[0] in COMMAND_LIST:
			await sendMessage(await COMMAND_LIST[command[0]](message, command), message.channel)
		else:
			await sendMessage('Message is ' + str(command), message.channel, reactions = [EMOJI_LIST['1'], EMOJI_LIST['2'], EMOJI_LIST['close'], EMOJI_LIST['chancel']])

@client.event
async def on_reaction_add(reaction, user):
	if reaction.count >= 2:
		for s in schedules:
			if reaction.message.id == s.messageByBot.id:
				if s.isClosed and (reaction.emoji != EMOJI_LIST['close'] and reaction.emoji != EMOJI_LIST['chancel']):
					debug('isClosed')
					await reaction.remove(user)
					return
				elif reaction.emoji == EMOJI_LIST['close']:
					if user.id == s.owner:
						debug('close...')
						await s.close()
					else:
						debug('invalid user')
						await reaction.remove(user)
				elif reaction.emoji == EMOJI_LIST['chancel']:
					if user.id == s.owner:
						debug('delete...')
						await s.chancel()
						del s
					else:
						debug('invalid user')
						await reaction.remove(user)
				elif reaction.count >= s.capa:
					if reaction.emoji in EMOJI_LIST:
						debug('Max Capa close...')
						await s.close()
				return
		debug(f'\
		@Reaction: {reaction}@{user}\
		')

client.run(TOKEN)
