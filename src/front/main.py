import os
import discord
import datetime
from dateutil import parser

MODE_LIST = {'TEST':'TEST', 'PROD':'PROD'}
MODE = MODE_LIST[os.environ['DISCORD_BOT_MODE']]
PREFIX = os.environ['DISCORD_BOT_PREFIX']
ADMIN_ID = int(os.environ['DISCORD_ADMIN_ID'])
TOKEN = os.environ['DISCORD_BOT_TOKEN']

client = discord.Client()
OUTPUT_CHANNEL = {}
DEFAULT_OUTPUT_CHANNEL_NAME = {'すけさん', '募集Bot'}
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
	
	def __init__(self, message, fncSendMsg, channel=None , limit=None, *args):
		self.owner = message.author
		self.message = message.content
		self.fncSendMessage = fncSendMsg
		if channel is None:
			self.channel = OUTPUT_CHANNEL[message.guild.id]
		else:
			self.channel = channel
		self.parse(message.content[1:])
		debug(f'owner is {self.owner}')
		log(f'[{message.guild.name}]: create schedule [{message.channel.name}] by message.author.name')
	
	def parse(self, message):
		# メッセージ内容をパースして、class内の引数に代入
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

async def createSchedule(message, channel=None):
	if message.guild.id in OUTPUT_CHANNEL:
		channel = OUTPUT_CHANNEL[message.guild.id]
	schedules.append(schedule(message, sendMessage, channel))
	await schedules[-1].send()
	return ''

async def addReactions(message, reactions):
	for reaction in reactions:
		await message.add_reaction(reaction)

async def sendMessage(message, channel, reactions=''):
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
	if isTestMode:
		print(message + '\n')

def log(message):
	print(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + ': '  + message + '\n')

def isAdmin(author):
	return (author.id == ADMIN_ID) or (author.top_role.permissions.administrator)
	#return (author.id == ADMIN_ID)

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
		debug(f'message: {message}\nmessage.guild: {message.guild}\nmessage.guild.id: {message.guild.id}')
		log(f'[message.guild.name]: set output channel [{channel.name}] by {message.author.name}')
		OUTPUT_CHANNEL[message.guild.id] = channel
		return f'Set Output Channel is {OUTPUT_CHANNEL[message.guild.id].name}'
	else:
		return 'ERROR: This Command can only Administrator.'

@client.event
async def on_ready():
	log(f'Bot Booting "{MODE}" Mode...')
	for guild in client.guilds:
		await on_guild_join(guild)

@client.event
async def on_message(message):
	if message.author.bot:
		return
	if message.content == '': # 画像をアップロードしただけの場合など
		return
	
	if message.content[0] == PREFIX:
		COMMAND_LIST = {
			'b': lambda m,c: createSchedule(m, m.channel),
			'e': lambda m,c: doEval(m),
			's': lambda m,c: setOutputChannel(m),
	}
		
		command = message.content[1:].split(' ')
		if command[0] in COMMAND_LIST:
			await sendMessage(await COMMAND_LIST[command[0]](message, command), message.channel)
		else:
			debug(f'Invalid Message "{str(message.content)}"')

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
					if user.id == s.owner.id:
						debug('close...')
						await s.close()
					else:
						await reaction.remove(user)
				elif reaction.emoji == EMOJI_LIST['chancel']:
					if user.id == s.owner.id:
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

async def on_guild_join(guild):
	log(f'[{guild.name}]: join')
	for channel in guild.channels:
		for defaultChannelName in DEFAULT_OUTPUT_CHANNEL_NAME:
			if defaultChannelName == channel.name:
				OUTPUT_CHANNEL[guild.id] = channel
				debug(f'set default output channel at {channel.name}')

async def on_guild_channel_create(channel):
	pass

client.run(TOKEN)
