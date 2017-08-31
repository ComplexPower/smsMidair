import hexchat
from twilio.rest import TwilioRestClient
from twilio import TwilioRestException

__module_name__ = 'smsMidair'
__module_author__ = 'b3d'
__module_version__ = '0.1'
__module_description__ = 'Notifies users via SMS when a Midair pickup game has started in #midair.pug on QuakeNet.'

client = TwilioRestClient(hexchat.get_pluginpref("ACCOUNT_SID"), hexchat.get_pluginpref("AUTH_TOKEN"))

def sendSMS(nick,phNumber,gameType) :
	try :
		client.messages.create(to=phNumber, from_=hexchat.get_pluginpref("twilioPh")[1:14],
			body=__module_name__ + ": " + gameType + " game starting for " + nick)
		hexchat.command("msg " + nick + " " + gameType + " game started, SMS sent, removed from queue. Temptest")
	except TwilioRestException :
		hexchat.command("msg " + nick + " Game started, but your phone number returned an error.\
		Consider !validate once you have added your phone number, or refer to the example in !help or !commands.")
	return hexchat.EAT_NONE

def validateSMS(nick,phNumber) :
	try :
		client.messages.create(to=phNumber, from_=hexchat.get_pluginpref("twilioPh")[1:13],
			body=__module_name__ + ": phone number verified for " + nick)
		hexchat.command("msg " + nick + " Phone number validated, SMS successfully sent.")
	except TwilioRestException :
		hexchat.command("msg " + nick + " Phone number returned an error. Refer to example by typing !help or !commands.")
	return hexchat.EAT_NONE

def chanParse_cb(word, word_eol, userdata) :	
	text = word[1].split()
	if word[0].startswith('Xenia') & (len(word) > 2) :				# *** Parses for Xenia to start a game and initiates texting
		if word[2] == "@" :											# Verifies Xenia is op'ed. word[2] won't exist if Xenia is not op'ed. 
			if (text[0] == 'Game') & (text[3] == 'starting') :
				for x in hexchat.list_pluginpref() :				# Cycle through stored names/numbers and send the texts
					if word[1].find(x) > 0 :						# Verifies user is in echoed queue when game starts
						y = hexchat.get_pluginpref(x)[1:14]			# Removes the necessary period from the stored string 
						sendSMS(x,y,text[1])						# (nick, phNumber, gameType)
						hexchat.del_pluginpref(x)					# Cleanup to remove the notified players from the queue
			elif word[1].find('has not returned and has lost their space in the queue.') > 0 :
				for x in hexchat.list_pluginpref() :					 
					if text[0] == x :		
						hexchat.del_pluginpref(x)					# *** Auto-removal from queue on user game queue timeout		
	elif word[1].startswith('!del'): 								# *** Auto-removal from queue and PM notification on user !del		
		for x in hexchat.list_pluginpref() :						
			if word[0] == x :		
				hexchat.del_pluginpref(x)
				hexchat.command("msg " + word[0] + " Channel !del detected, you are no longer queued for a SMS.")
	return hexchat.EAT_NONE

def msgParse_cb(word, word_eol, userdata) :
	if word[1].startswith('!add') :									# *** Registers	user into SMS queue
		text = word[1].split() 										# Splits up the text argument of msg into manageable words
		i=0															# Temp variable necessary due to funky logic
		j = text[1]
		if j[0] == '<' :											# This is to alleviate confusion with the !help example
			hexchat.command("msg " + word[0] + " Omit the angle brackets '<' & '>' when adding your phone number.")
		else :														# The 'meat' of storing a users phone number.
			for x in hexchat.list_pluginpref() :					# For all active users in queue...
				if word[0] == x :									# If they typed !add..
					y = hexchat.get_pluginpref(x)[1:13]				# If user exists we'll just update the phone number.
					if y == text[1] :
						hexchat.command("msg " + word[0] + " Phone number confirmed.")
					else :
						hexchat.command("msg " + word[0] + " Phone number updated.") 
					i = i+1
			if i == 0 :
				hexchat.command("msg " + word[0] + " You are now queued for a SMS once the next game starts.")		
			hexchat.set_pluginpref(word[0], ('.'+text[1]))    		# No matter what, stores nick with (possibly new) phone number. 
																	# Period added to force str, as hexchat.get_pluginprefs() returns int 			
	elif word[1].startswith('!remove') :							# *** Removes user from SMS queue
		i = 0
		for x in hexchat.list_pluginpref() :						
			if word[0] == x :										
				hexchat.del_pluginpref(x)
				hexchat.command("msg " + word[0] + " You have been manually removed from the queue.")
				i = i+1
		if i == 0 :
			hexchat.command("msg " + word[0] + " You are not queued for a SMS.")		
	elif word[1].startswith('!query') : 							# *** Checks whether user is in SMS queue	 
		i = 0
		for x in hexchat.list_pluginpref() :						# If user exists logic
			if word[0] == x :										
				hexchat.command("msg " + word[0] + " You are queued for a SMS once the next game starts.") 
				i = i+1
		if i == 0 :
			hexchat.command("msg " + word[0] + " You are not queued for a SMS.") 
	elif word[1].startswith('!help') : 								 
		helpInstr(word[0])
	elif word[1].startswith('!info') :						
		infoInstr(word[0])
	elif word[1].startswith('!validate') :						
		i = 0
		for x in hexchat.list_pluginpref() :						# Ensures user is in the queue before attempting to validate ph no.		
			if word[0] == x :										
				validateSMS(x,hexchat.get_pluginpref(x))
				i = i+1
		if i == 0 :
			hexchat.command("msg " + word[0] + " You are not queued for a SMS.")		
	elif word[1].startswith('!commands') : 								 
		commandsInstr(word[0])	
	else :		
		hexchat.command("msg " + word[0] + " Command not understood. /msg " +\
		hexchat.get_info("nick") + " !help for more information.")
	return hexchat.EAT_NONE

def joins_cb(word, word_eol, userdata) :
	hexchat.command("notice " + word[0] + " " + __module_name__ + " active - Get a text when your pickup\
	game starts! - /msg " + hexchat.get_info("nick") + " !help for more info.")
	return hexchat.EAT_NONE
	
def nickChange_cb(word, word_eol, userdata) :
	for x in hexchat.list_pluginpref() :						
		if word[0] == x : 											# If user exists, create new entry with new nick, del old.
			hexchat.set_pluginpref(word[1],hexchat.get_pluginpref(word[0]))
			hexchat.del_pluginpref(word[0])
	return hexchat.EAT_NONE

def helpInstr(nick) :
	hexchat.command("msg " + nick + " **** Bot is in development // Send feedback to b3d ****")
	hexchat.command("msg " + nick + " " + __module_name__ + " Help")
	hexchat.command("msg " + nick + " This bot allows you to (God forbid) step away from your computer\
	when waiting for a queue to fill.")			
	hexchat.command("msg " + nick + " To receive a SMS once the game starts, type (without angle brackets):")	
	hexchat.command("msg " + nick + " /msg " + hexchat.get_info("nick") + " !add <cell phone no. in E.164\
	format, preceeded by a + symbol, e.g.: +18008675309>")
	hexchat.command("msg " + nick + " /msg " + hexchat.get_info("nick") + " !commands for more.") 
	return hexchat.EAT_NONE
	
def infoInstr(nick) :
	hexchat.command("msg " + nick + " " + __module_name__ + " version " + __module_version__ + " by " + __module_author__ + ".\
	Running on a Raspberry Pi.")
	hexchat.command("msg " + nick + " https://github.com/ComplexPower/smsMidair.")
	hexchat.command("msg " + nick + " Privacy: This bot responds only to private messages, to prevent public dissemination of\
	private phone numbers. By design, I do not log user phone numbers; this can be seen in the source code.")
	hexchat.command("msg " + nick + " Nevertheless, for your own protection, I recommend using a cost-free Google voice number\
	as an intermediary (https://voice.google.com/). Enable automatic text forwarding to your personal cell, but block\
	all incoming calls from this number on your cell. Remember you can always generate a new voice number if it is compromised.")	
	hexchat.command("msg " + nick + " Technicalities: Users who haven't started a game can manually drop with the !remove command,\
	however they will automatically be removed from the queue after typing !del in #midair.pug, or\
	after Xenia acknolwedges them timing out from the PUG queue. A typical user should only need to use one !add command\
	per game, unless he/she removes themselves from one of the queues while still waiting in another.\
	Bot does not differentiate queues.")
	return hexchat.EAT_NONE

def commandsInstr(nick) :
	hexchat.command("msg " + nick + " Available !commands:")		
	hexchat.command("msg " + nick + " !add +18008675309")
	hexchat.command("msg " + nick + " !validate")
	hexchat.command("msg " + nick + " !query")
	hexchat.command("msg " + nick + " !remove")
	hexchat.command("msg " + nick + " !info")
	hexchat.command("msg " + nick + " !help")
	return hexchat.EAT_NONE	

hexchat.hook_print('Channel Message', chanParse_cb)
hexchat.hook_print('Private Message', msgParse_cb) 
hexchat.hook_print('Private Message to Dialog', msgParse_cb) 		# Redundant / fail-safe
hexchat.hook_print('Join', joins_cb)
hexchat.hook_print('Change Nick', nickChange_cb)
print(__module_name__, 'version', __module_version__, 'loaded.')


