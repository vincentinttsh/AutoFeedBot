from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import logging
import requests
import json
import configparser
from datetime import datetime, timedelta
from threading import Timer
import pigpio
import time


USERSTATUS = {}
SCHEDULECHANGING = False
START_TIME = None
END_TIME = None
STEP_TIME = None
FEED_TIME = None
SCHEDULE_PERSON = None
NEXT_FEED = None
NEWSCHEDULE = [i for i in range(5)]
BOT = None
PWM_CONTROL_PIN = 18
PWM_FREQ = 50
CLOSE = 170
OPEN = 135
FEEDING = False
PWM = None

config = configparser.ConfigParser()
config.read('config.ini')

format_config = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(
    format=format_config, level=logging.INFO, filename='run.log')
logger = logging.getLogger()
try:
    PWM = pigpio.pi()
except Exception as e:
    logger.error("Error starting PWM" + str(e))

updater = Updater(token=config['TELEGRAM']['ACCESS_TOKEN'], use_context=True)
dispatcher = updater.dispatcher


def angle_to_duty_cycle(angle=0):
    duty_cycle = int((500 * PWM_FREQ + (1900 * PWM_FREQ * angle / 180)))
    return duty_cycle


def unchanging(chat_id):
    global USERSTATUS, SCHEDULECHANGING
    if chat_id in USERSTATUS:
        if USERSTATUS[chat_id] in ['START_TIME', 'STEP_TIME', 'END_TIME']:
            SCHEDULECHANGING = False


# start指令
def start(update, context):
    global USERSTATUS
    chat_id = update.message.chat_id
    unchanging(chat_id)
    if chat_id not in USERSTATUS:
        USERSTATUS[chat_id] = None
    reply = "有以下指令：\n /help：請求協助\n /feed：餵食幾匙\n /schedule：規劃啥時餵食\n"
    context.bot.send_message(chat_id=chat_id, text=reply)


# 新增這個指令
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


# help指令
def help(update, context):
    global USERSTATUS
    chat_id = update.message.chat_id
    unchanging(chat_id)
    # 發送所有指令用以參考
    USERSTATUS[chat_id] = None
    reply = "有以下指令：\n /help：請求協助\n /feed：餵食幾匙\n /schedule：規劃啥時餵食\n"
    context.bot.send_message(chat_id=chat_id, text=reply)


# 新增指令help
help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)


# feed指令：要開幾次
def feed_command(update, context):
    global USERSTATUS
    chat_id = update.message.chat_id
    unchanging(chat_id)
    USERSTATUS[chat_id] = 'FEED_COMMAND'
    reply = "你希望開幾匙？"
    context.bot.send_message(chat_id=chat_id, text=reply)


feed_handler = CommandHandler('feed', feed_command)
dispatcher.add_handler(feed_handler)


def schedule_command(update, context):
    global USERSTATUS, SCHEDULECHANGING
    chat_id = update.message.chat_id
    unchanging(chat_id)
    if SCHEDULECHANGING:
        USERSTATUS[chat_id] = None
        reply = "有人正在修改"
        context.bot.send_message(chat_id=chat_id, text=reply)
    else:
        SCHEDULECHANGING = True
        USERSTATUS[chat_id] = 'START_TIME'
        reply = "開始時間？（格式：小時:分鐘（24時制））"
        context.bot.send_message(chat_id=chat_id, text=reply)


schedule_handler = CommandHandler('schedule', schedule_command)
dispatcher.add_handler(schedule_handler)


def schedule_do(start_time=None):
    global NEXT_FEED, FEED_TIME, SCHEDULE_PERSON, BOT, END_TIME, START_TIME
    if start_time is not None:
        if datetime.now() > END_TIME:
            START_TIME += timedelta(days=1)
            END_TIME += timedelta(days=1)
            next_time = START_TIME - datetime.now()
            start = START_TIME.strftime("%Y-%m-%d %H:%M")
            end = END_TIME.strftime("%H:%M")
            temp = start + "~" + end + ", step=" + str(STEP_TIME)
            logger.info("feed_schedule = " + temp + " times=" + str(FEED_TIME))
            NEXT_FEED = Timer(next_time.seconds+1, schedule_do)
            NEXT_FEED.start()
            return
        temp = start_time.replace(microsecond=0, second=0, minute=0)
        while temp < START_TIME or temp < datetime.now():
            temp += STEP_TIME
        secs = (temp - datetime.now()).seconds
        logger.info("start schedule")
        NEXT_FEED = Timer(secs+1, schedule_do)
        NEXT_FEED.start()
        return
    try:
        global OPEN, CLOSE, PWM_CONTROL_PIN, PWM_FREQ, PWM
        for i in range(FEED_TIME):
            dc = angle_to_duty_cycle(OPEN)
            PWM.hardware_PWM(PWM_CONTROL_PIN, PWM_FREQ, dc)
            time.sleep(0.25)
            dc = angle_to_duty_cycle(CLOSE)
            PWM.hardware_PWM(PWM_CONTROL_PIN, PWM_FREQ, dc)
            time.sleep(0.25)
    except Exception as e:
        reply = "can not feed"
        logger.error(reply + str(e))
        BOT.send_message(chat_id=SCHEDULE_PERSON, text=reply)
        return
    reply = "feed " + str(FEED_TIME) + " times"
    logger.info(reply)
    BOT.send_message(chat_id=SCHEDULE_PERSON, text=reply)
    if STEP_TIME + datetime.now() <= END_TIME:
        NEXT_FEED = Timer(STEP_TIME.seconds+1, schedule_do)
        NEXT_FEED.start()
    else:
        START_TIME += timedelta(days=1)
        END_TIME += timedelta(days=1)
        next_time = START_TIME - datetime.now()
        start = START_TIME.strftime("%Y-%m-%d %H:%M")
        end = END_TIME.strftime("%H:%M")
        temp = start + "~" + end + ", step=" + str(STEP_TIME)
        logger.info("feed_schedule = " + temp + " times=" + str(FEED_TIME))
        NEXT_FEED = Timer(next_time.seconds+1, schedule_do)
        NEXT_FEED.start()


def new_schedule(data):
    global START_TIME, END_TIME, STEP_TIME, FEED_TIME, SCHEDULE_PERSON
    START_TIME = data[0]
    END_TIME = data[1]
    STEP_TIME = data[2]
    FEED_TIME = data[3]
    SCHEDULE_PERSON = data[4]


def echo(update, context):
    global USERSTATUS, SCHEDULECHANGING, START_TIME, END_TIME, STEP_TIME, BOT
    chat_id = update.message.chat_id
    text = update.message.text
    if chat_id not in USERSTATUS:
        return
    if USERSTATUS[chat_id] == 'FEED_COMMAND':
        try:
            times = int(text)
        except ValueError:
            USERSTATUS[chat_id] = 'FEED_COMMAND'
            reply = "請輸入數字"
            context.bot.send_message(chat_id=chat_id, text=reply)
            return
        USERSTATUS[chat_id] = None
        global FEEDING
        if FEEDING:
            reply = "正在餵食中"
            context.bot.send_message(chat_id=chat_id, text=reply)
        try:
            FEEDING = True
            global OPEN, CLOSE, PWM, PWM_CONTROL_PIN, PWM_FREQ, PWM
            for i in range(times):
                dc = angle_to_duty_cycle(OPEN)
                PWM.hardware_PWM(PWM_CONTROL_PIN, PWM_FREQ, dc)
                time.sleep(0.25)
                dc = angle_to_duty_cycle(CLOSE)
                PWM.hardware_PWM(PWM_CONTROL_PIN, PWM_FREQ, dc)
                time.sleep(0.25)
            FEEDING = False
        except Exception as e:
            reply = "can not feed"
            logger.error(reply + str(e))
            context.bot.send_message(chat_id=chat_id, text=reply)
            return
        reply = "已餵食" + text + "匙"
        logger.info(str(chat_id) + " feed " + text + "匙")
        context.bot.send_message(chat_id=chat_id, text=reply)
    if USERSTATUS[chat_id] == 'SCHEDULE_FEED':
        try:
            times = int(text)
        except ValueError:
            USERSTATUS[chat_id] = 'FEED_COMMAND'
            reply = "請輸入數字"
            context.bot.send_message(chat_id=chat_id, text=reply)
            return
        NEWSCHEDULE[3], NEWSCHEDULE[4] = times, chat_id
        USERSTATUS[chat_id] = None
        SCHEDULECHANGING = False
        new_schedule(NEWSCHEDULE)
        start = START_TIME.strftime("%Y-%m-%d %H:%M")
        end = END_TIME.strftime("%H:%M")
        temp = start + "~" + end + ", step=" + str(STEP_TIME)
        logger.info(str(chat_id) + " set feed_schedule")
        logger.info("feed_schedule = " + temp + " times=" + text)
        if NEXT_FEED is not None:
            NEXT_FEED.cancel()
        BOT = context.bot
        schedule_do(datetime.now())
        reply = "設定完成"
        context.bot.send_message(chat_id=chat_id, text=reply)
    if USERSTATUS[chat_id] == 'STEP_TIME':
        try:
            minute = int(text)
            NEWSCHEDULE[2] = timedelta(minutes=minute)
        except Exception:
            USERSTATUS[chat_id] = 'STEP_TIME'
            reply = "間隔時間？（分鐘）"
            context.bot.send_message(chat_id=chat_id, text=reply)
            return
        USERSTATUS[chat_id] = 'SCHEDULE_FEED'
        reply = "你希望開幾匙？"
        context.bot.send_message(chat_id=chat_id, text=reply)
    if USERSTATUS[chat_id] == 'END_TIME':
        try:
            hour, minute = map(int, text.split(':'))
            now = datetime.today()
            NEWSCHEDULE[1] = now.replace(second=0, minute=minute, hour=hour)
        except Exception:
            USERSTATUS[chat_id] = 'END_TIME'
            reply = "結束時間？（格式：小時:分鐘（24時制））"
            context.bot.send_message(chat_id=chat_id, text=reply)
            return
        if NEWSCHEDULE[0] >= NEWSCHEDULE[1]:
            USERSTATUS[chat_id] = 'END_TIME'
            reply = "結束時間小於開始時間"
            context.bot.send_message(chat_id=chat_id, text=reply)
            return
        USERSTATUS[chat_id] = 'STEP_TIME'
        reply = "間隔時間？（分鐘）"
        context.bot.send_message(chat_id=chat_id, text=reply)
    if USERSTATUS[chat_id] == 'START_TIME':
        try:
            hour, minute = map(int, text.split(':'))
            now = datetime.today()
            NEWSCHEDULE[0] = now.replace(second=0, minute=minute, hour=hour)
        except Exception:
            USERSTATUS[chat_id] = 'START_TIME'
            reply = "開始時間？（格式：小時:分鐘（24時制））"
            context.bot.send_message(chat_id=chat_id, text=reply)
            return
        USERSTATUS[chat_id] = 'END_TIME'
        reply = "結束時間？（格式：小時:分鐘（24時制））"
        context.bot.send_message(chat_id=chat_id, text=reply)


dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=echo))


if __name__ == "__main__":
    # 啟動指令
    updater.start_polling()
    updater.idle()
    if NEXT_FEED is not None:
        NEXT_FEED.cancel()
    if PWM is not None:
        PWM.set_mode(PWM_CONTROL_PIN, pigpio.INPUT)
