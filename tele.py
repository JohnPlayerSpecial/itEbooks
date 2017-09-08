from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import BaseFilter
from telegram.ext import (Updater, CommandHandler, Handler,MessageHandler, ShippingQueryHandler, Filters, ChosenInlineResultHandler, RegexHandler,ConversationHandler, CallbackQueryHandler, PreCheckoutQueryHandler)
from telegram import *
import logging
import sqlite3
from random import randint
import threading
import urllib
from urllib import *
from urllib.request import urlopen
import json
import os
import time
import threading
import re
import cgi
import telegram


TOKEN_TELEGRAM = os.environ['TOKEN_TELEGRAM']
TOKEN_TELEGRAM2 = os.environ['TOKEN_TELEGRAM2']
NGROK_URL =  os.environ['NGROK_URL']
MY_CHAT_ID =  [ int(x) for x in os.environ['MY_CHAT_ID'].split(",") ]
my_actual_chat_id = int( os.environ['my_actual_chat_id'] )

bot2 = telegram.Bot(TOKEN_TELEGRAM2)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
DATABASE_NAME = 'itebooks2erondata.db'

WAIT_FOR_USER_TO_PRESS_DOWNLOAD, WAIT_FOR_USER_TO_TRY_TO_BUY_DOWNLOAD, WAIT_FOR_USER_TO_BUY_DOWNLOAD = range(3)
MAX_FILESIZE_FREE_DOWNLOAD = 300

def search(bot, update):
    update.message.reply_text("What PDF are you searching...?")
    return 0

def start(bot, update):
    tkn = ""
    surplus = ""
    if update.message.chat_id  in MY_CHAT_ID:
        surplus = "\nYou are in the whitelist and can proceed to use the bot!"
        tkn = ""
        text = "Welcome.\n\nUse /search to search for PDFs." + surplus
    else:
        surplus = "\nERROR: You are NOT in the whitelist and hence can not proceed to use the bot!"
        tkn = "not"
        text =  surplus
    update.message.reply_text(text)
    if 
    text2 = "User {} with chat_id:{}  started the bot\nUser is {} authorized".format(username, update.message.chat_id, tkn) 
    username = update.message.from_user.name
    bot2.sendMessage(chat_id = my_actual_chat_id, text = text2)


def sendResults(bot,update, page = 0):
	chat_id = update.message.chat_id
	conn = sqlite3.connect( DATABASE_NAME ) 
	cursor = conn.cursor()
	query = update.message.text
	
	string = "SELECT * FROM itEbooks WHERE description MATCH '{}'".format(query)
	cursor.execute( string )           
	conn.commit()
	allResults = cursor.fetchall()
	conn.close()
	
	if len(allResults) == 0:
		bot.sendMessage(chat_id = update.message.chat_id, text = "No results were found.", parse_mode = "Html")
		return ConversationHandler.END
	AVANZAMENTO = 5
	page = 0
	string = "<b>Found {} results.</b>\nShowing {}-{}\n\n".format(len(allResults), page+1,(page+1)*AVANZAMENTO)
	for i in range(min(len(allResults),5)):
		bookName = allResults[i][1]
		idResult = allResults[i][0]
		publisher = allResults[i][6]
		numberOfPages = allResults[i][9]
		fileSize = allResults[i][11]
		string += """<b>{}. {}</b>\nby <i>{}</i>.\n{} pages, {}\n/info_{}\n\n""".format( i + 1, bookName, publisher, numberOfPages,fileSize, idResult )
	
	keyboard = [ 
	            [
	              InlineKeyboardButton("<<", callback_data="begin_"),
	              InlineKeyboardButton("<", callback_data="EDITMESSAGEpage={},query='{}'".format(page-1,query) ),
	              InlineKeyboardButton(">", callback_data="EDITMESSAGEpage={},query='{}'".format(page+1,query) ),
	              InlineKeyboardButton(">>", callback_data="end_")
	            ] 
	          ]
	reply_markup = InlineKeyboardMarkup( keyboard )
	#print( "EDITMESSAGEpage={},query='{}'".format(page-1,query) )
	bot.sendMessage(chat_id = chat_id, text = string, parse_mode = "Html", reply_markup = reply_markup)
	username = update.message.from_user.name
	text2 = "User {} with chat_id:{} requested PDFs using this keyword: '{}'. Sending {} results.".format(username,chat_id,query, len(allResults) )
	bot2.sendMessage(chat_id = my_actual_chat_id, text = text2)
	return ConversationHandler.END 

def editMessageSendMoreResults(bot,update):
	query = update.callback_query
	message_id = update.callback_query.message.message_id
	chat_id = update.callback_query.message.chat_id
	bot.answerCallbackQuery(callback_query_id = query.id)
	conn = sqlite3.connect( DATABASE_NAME ) 
	cursor = conn.cursor()
	if "EDITMESSAGEpage=-" in query.data:
		return
	else:
		page = int( re.findall(r"""^EDITMESSAGEpage=(\d),query=""", query.data )[0] )
	
	queryPDF = query.data.split("query='")[1][0:-1]
	i = 0
	
	string = "SELECT * FROM itEbooks WHERE bookName MATCH '{}'".format(queryPDF)
	cursor.execute( string )           
	conn.commit()
	allResults = cursor.fetchall()
	conn.close()

	if len(allResults) == 0:
		bot.sendMessage(chat_id = update.message.chat_id, text = "No results were found.", parse_mode = "Html")
	AVANZAMENTO = 5
	secondNumber = min(      len(  allResults  )  ,    (page+1) * AVANZAMENTO        )
	firstNumber = AVANZAMENTO * page + 1
	string = "<b>Found {} results.</b>\nShowing {}-{}\n\n".format( len( allResults ), firstNumber , secondNumber )
	if len(allResults[ page * AVANZAMENTO : (page + 1) * AVANZAMENTO ]) == 0:
		return
	for i in range(min(len(allResults[ page * AVANZAMENTO : (page + 1) * AVANZAMENTO ]),5)):
		j = (page * AVANZAMENTO) + i 
		bookName = allResults[j][1]
		idResult = allResults[j][0]
		publisher = allResults[j][6]
		numberOfPages = allResults[j][9]
		fileSize = allResults[j][11]
		string += """<b>{}. {}</b>\nby <i>{}</i>.\n{} pages, {}\n/info_{}\n\n""".format( (page*AVANZAMENTO) + i +1 , bookName, publisher, numberOfPages,fileSize, idResult,  )

	keyboard = [ 
	            [
	              InlineKeyboardButton("<<", callback_data="begin_"),
	              InlineKeyboardButton("<", callback_data="EDITMESSAGEpage={},query='{}'".format(int(page)-1,query.data.split("query='")[1][0:-1]) ),
	              InlineKeyboardButton(">", callback_data="EDITMESSAGEpage={},query='{}'".format(int(page)+1,query.data.split("query='")[1][0:-1])),
	              InlineKeyboardButton(">>", callback_data="end_")
	            ] 
	          ]   
	reply_markup = InlineKeyboardMarkup( keyboard )
	bot.editMessageText(chat_id = chat_id, text = string, parse_mode = "Html", message_id = message_id)
	bot.editMessageReplyMarkup(chat_id = chat_id, message_id = message_id, reply_markup = reply_markup)
	username = update.callback_query.from_user.name
	text2 = "User {} with chat_id:{} requested PDFs using this keyword: '{}'. User requested page:{}. Sending {} results.".format(username,chat_id,queryPDF, page,len(allResults) )
	bot2.sendMessage(chat_id = my_actual_chat_id, text = text2)

	
	

def done(bot,update):
	print("user pressed cancel")
	return ConversationHandler.END #importante altrimenti si blocca
	
def randomBook(bot,update):
	moreInfo(bot,update, random = True, chat_id = update.message.chat_id)
	return
	
	
	
def moreInfo(bot,update,random = False, reshowPic = "", chat_id = ""):
	conn = sqlite3.connect( DATABASE_NAME ) 
	cursor = conn.cursor()
	if random == True:
		idResult = randint(0,7033)
		chat_id = chat_id
		username = update.message.from_user.name
	else:
		if reshowPic != "":
			idResult = reshowPic
			query = update.callback_query
			bot.answerCallbackQuery(callback_query_id = query.id)
			bot.deleteMessage(chat_id = update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id)
			chat_id = update.callback_query.message.chat_id
			username = update.callback_query.from_user.name
		else:
			idResult = update.message.text.split("/info_")[1]
			chat_id = update.message.chat_id
			username = update.message.from_user.name
	
	cursor.execute( """SELECT * FROM itEbooks WHERE id={}""".format( idResult ) )           
	conn.commit()
	allResults = cursor.fetchall()
	conn.close()

	bookName = allResults[0][1]
	publisher = allResults[0][6]
	#print(bookName,idResult)
	numberOfPages = allResults[0][9]
	fileSize = allResults[0][11]
	photoUrl = allResults[0][4]
	caption = bookName + "\n" + str(numberOfPages) + " pages." + "\n" + fileSize
	callback_data_more_info = 'RequestMoreInfo_{}'.format(idResult)
	callback_data_random = 'RequestRandom_{}'.format(randint( 0,7033 ))
	if True:
		url = NGROK_URL + "/" + urllib.parse.quote(cgi.escape(bookName)) + ".pdf"
		AVAILABLE = "Download"
	else:
		url = "127.0.0.1"
		AVAILABLE = "NOT AVAILABLE"
	if random == True:
		keyboard = [ 
	            [
	              InlineKeyboardButton(AVAILABLE, url = url),
	              InlineKeyboardButton("Info", callback_data=callback_data_more_info),
	              InlineKeyboardButton(">>", callback_data=callback_data_random)
	            ] 
	          ]
	else:
		keyboard = [ 
	            [
	              InlineKeyboardButton(AVAILABLE, url = url),
	              InlineKeyboardButton("Info", callback_data=callback_data_more_info)
	            ] 
	          ]
	reply_markup = InlineKeyboardMarkup( keyboard )
	bot.sendPhoto(chat_id = chat_id, photo = photoUrl, caption = caption,  reply_markup = reply_markup)
	if random == True:
		text2 = "User {} with chat_id:{} requested a random PDF. Serving PDF with  id: {}, {}".format(username, chat_id, idResult, bookName) 
		bot2.sendMessage(chat_id = my_actual_chat_id, text = text2)
	else:
		text2 = "User {} with chat_id:{} requested more info about PDF with id: {}, {}".format(username, chat_id, idResult, bookName) 
		bot2.sendMessage(chat_id = my_actual_chat_id, text = text2)
	return 2	
			
def editMessageReshowPicture(bot,update):
	idResult = update.callback_query.data.split("ReshowPicture_")[1]
	moreInfo(bot,update, reshowPic = idResult)

def editMessagewithDescription(bot,update):
	chat_id = update.callback_query.message.chat_id
	idResult = update.callback_query.data.split("RequestMoreInfo_")[1]
	query = update.callback_query
	bot.answerCallbackQuery(callback_query_id = query.id)
	
	conn = sqlite3.connect( DATABASE_NAME ) 
	cursor = conn.cursor()
	cursor.execute( """SELECT * FROM itEbooks WHERE id={}""".format( idResult ) )           
	conn.commit()
	allResults = cursor.fetchall()
	conn.close()
	
	bookName = allResults[0][1]
	publisher = allResults[0][6]
	numberOfPages = allResults[0][9]
	fileSize = allResults[0][11]
	photoUrl = allResults[0][4]
	
	author = allResults[0][5]
	description = allResults[0][12]
	year = allResults[0][8]
	pages = allResults[0][9]
	text = "<b>{}</b>\nby <i>{}</i>\nPrinted by <i>{}</i> in {}.\n{} pages, {}.\n\n<b>Description:</b><i>{}</i>".format(bookName,author,publisher,year,pages, fileSize,description)
	bot.deleteMessage(chat_id = update.callback_query.message.chat_id, message_id=update.callback_query.message.message_id)
	callback_data_download = 'downloadAfterMoreInfo_{}'.format(idResult)
	callback_data_more_info = 'ReshowPicture_{}'.format(idResult)
	if True:
		url = NGROK_URL + "/" + urllib.parse.quote(cgi.escape(bookName)) + ".pdf"
		AVAILABLE = "Download"
	else:
		url = "127.0.0.1"
		AVAILABLE = "NOT AVAILABLE"
	keyboard = [ 
	            [
	              InlineKeyboardButton(AVAILABLE, url = url),
	              InlineKeyboardButton("Return to Pic", callback_data=callback_data_more_info)
	            ] 
	          ]
	reply_markup = InlineKeyboardMarkup( keyboard )
	bot.sendMessage(chat_id = chat_id, text = text , parse_mode = "Html", reply_markup = reply_markup)
	username = update.callback_query.from_user.name
	text2 = "User {} with chat_id:{} requested description of PDF with id: {}, {}".format(username, chat_id, idResult, bookName) 
	bot2.sendMessage(chat_id = my_actual_chat_id, text = text2)
	
class FilterAwesome(BaseFilter):
    def filter(self, message):
        return str(message.chat_id) in MY_CHAT_ID.split(",")

# Remember to initialize the class.
filter_awesome = FilterAwesome()

def main():
    updater = Updater(TOKEN_TELEGRAM) #ITEbooksBot
    dp = updater.dispatcher
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('random', randomBook, filters = Filters.user(MY_CHAT_ID ) ))
    updater.dispatcher.add_handler(RegexHandler('^/info_\d+', moreInfo) )
  
    updater.dispatcher.add_handler(CallbackQueryHandler( editMessageSendMoreResults, pattern = '^EDITMESSAGEpage=' ))
    
    updater.dispatcher.add_handler(CallbackQueryHandler( editMessagewithDescription, pattern = '^RequestMoreInfo_\d+' ))
    updater.dispatcher.add_handler(CallbackQueryHandler( editMessageReshowPicture, pattern = '^ReshowPicture_\d+' ))
    conv_handler = ConversationHandler(
                                       entry_points = [CommandHandler('search', search, filters = Filters.user(MY_CHAT_ID) )],
                                       states = {
                                                 0: [MessageHandler(Filters.text, sendResults)],
                                                },
                                       fallbacks=[CommandHandler('cancel', done)]
                                       )
    dp.add_handler(conv_handler)
    
    updater.start_polling()
    updater.idle()
 
if __name__ == '__main__':
    main()
    
    
'''
else:
		#send invoice
		print("i will make me pay the file")
		#print(dir(update.callback_query))
		provider_token = '284685063:TEST:ZmUxNWQzM2Y0YzU5'
		title = allResults[0][1]
		description = allResults[0][10]
		payload = "ciao"
		currency = "EUR"
		start_parameter = "START_PARAMETER"
		photo_url = allResults[0][4] 
		price = 2
		sconto = 0
		IVA = 22
		final_my_price = price * 100 -1 * price * sconto
		prices = [	
							LabeledPrice(title, price * 100),
							LabeledPrice("Sconto {}%".format(sconto), -1 * price * sconto   ),  
							LabeledPrice("IVA {}%".format(IVA), (IVA/100) * ( final_my_price ))          
				 ]

		bot.sendInvoice(
						chat_id = update.callback_query.message.chat_id, 
						title = title,
						description = description, 
						payload = payload, 
						currency = currency, 
						prices = prices, 
						start_parameter = start_parameter,
						provider_token = provider_token,
						photo_url = photo_url
						)

		return 3
'''
