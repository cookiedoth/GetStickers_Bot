import requests
import time
import json
import os
import imghdr
import atexit
from PIL import Image

def get_message(update):
	if ('message' in update):
		return update['message']
	else:
		return update['edited_message']

def get_chat_id(update):
	return get_message(update)['chat']['id']

class chat_with_bot:

	#init bot
	def __init__(self, _id, _url, _token):
		self.id = _id
		self.rev = 0
		self.url = _url
		self.token = _token

	#gets message, returns list of dictionaries {'id': id, 'text' : ..., etc}
	def send(self, message):
		if ('text' in message):
			txt = message['text']
			if (('/start' in txt) or ('/help' in txt)):
				return [{'command' : 'sendMessage', 'text' : 'Send me a sticker to get a file'}]

		if ('sticker' in message):
			file_id = message['sticker']['thumb']['file_id']
			_params = {'file_id' : file_id}
			response = requests.get(self.url + "getFile", params = _params).json()
			file_path = response['result']['file_path']
			download_url = "https://api.telegram.org/file/bot" + self.token + "/" + file_path
			os.system("wget -O sticker.webp " + download_url)
			im = Image.open("sticker.webp").convert("RGB")
			im.save("sticker.png","png")
			files = {'document' : open('sticker.png', 'rb')}
			requests.post("https://api.telegram.org/bot" + self.token + "/sendDocument?chat_id=" + str(self.id), files=files)

		return []

	def setparams(self, string):
		pass

	def __str__(self):
		return ""

class telegram_bot:

	def load_from_file(self):
		try:
			f = open(self.name + ".botconfig", 'r')
		except:
			return
		x = f.readlines()
		for i in range(len(x)):
			x[i] = x[i][:len(x[i]) - 1]
		self.last_update = int(x[1])
		founded_chats = json.loads(x[2])
		for chat in founded_chats:
			self.chats[chat[0]] = chat_with_bot(chat[0], self.url, self.token)
			self.chats[chat[0]].setparams(chat[1])

	def __init__ (self, _token, _name):
		self.token = _token
		self.name = _name
		self.url = "https://api.telegram.org/bot" + self.token + "/"
		self.chats = {}
		self.last_update = -1
		self.load_from_file()

	def get_updates(self):
		response = requests.get(self.url + "getUpdates")
		return response.json()['result']

	def get_new_updates(self):
		upd = self.get_updates()
		res = []
		for i in range(1, len(upd) + 1):
			if (upd[-i]['update_id'] > self.last_update):
				res.append(upd[-i])
				chat_id = get_chat_id(upd[-i])
				if (not(chat_id in self.chats)):
					self.chats[chat_id] = chat_with_bot(chat_id, self.url, self.token)
			else:
				break
		if (len(upd) > 0):
			self.last_update = upd[-1]['update_id']
		return res

	def send_one(self, response_element, id):
		command = response_element['command']
		response_element.pop('command')
		params = response_element
		params['chat_id'] = id
		requests.post(self.url + command, data = params)

	def send(self, response, defalut_id):
		for cur in response:
			if ('id' in cur):
				self.send_one(cur, cur['id'])
			else:
				self.send_one(cur, defalut_id)

	def update(self):
		updates = self.get_new_updates()[::-1]
		for upd in updates:
			chat_id = get_chat_id(upd)
			response = self.chats[chat_id].send(get_message(upd))
			self.send(response, chat_id)

	def save_to_file(self):
		f = open(self.name + ".botconfig", 'w')
		f.write("Configuration to bot " + self.name + "\n")
		f.write(str(self.last_update) + "\n")
		stringchats = '['
		it = []
		for x in self.chats.items():
			it.append(x)
		for i in range(len(it)):
			x = it[i]
			stringchats = stringchats + '[' + str(x[0]) + ', "' + str(x[1]) + '"]'
			if (i < len(it) - 1):
				stringchats += ', '
		stringchats += ']'
		f.write(stringchats + "\n")

bot = telegram_bot("<TOKEN>", "<NAME>")

def exit_handler():
	bot.save_to_file()

atexit.register(exit_handler)

while (True):
	try:
		bot.update()
		bot.save_to_file()
		time.sleep(1)
	except KeyboardInterrupt:
		break