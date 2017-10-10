import json
import logging
import os
import time

from PIL import Image
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)

# setup logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

config = None

def start(bot, update):
    pass


def send_uses_count(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="I've created *%d* stickers for people so far!" % config['uses'], parse_mode='Markdown')


def main():
    get_config()
    updater = Updater(config['token'])
    global uses
    uses = config['uses']
    dispatcher = updater.dispatcher

    # register commands
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('uses', send_uses_count))

    # register media listener
    dispatcher.add_handler(MessageHandler((Filters.photo | Filters.sticker), image_sticker_received))

    # register variable dump loop
    updater.job_queue.run_repeating(dump_variables, 300, 300)

    # register error handler
    dispatcher.add_error_handler(error)

    updater.start_polling()

    updater.idle()


def image_sticker_received(bot, update):
    # feedback to show bot is processing
    time.sleep(.5)
    bot.send_chat_action(chat_id=update.message.chat_id, action='upload_photo')

    # get file id
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
    else:
        photo_id = update.message.sticker.file_id

    # download file
    file = bot.get_file(file_id=photo_id)
    ext = '.' + file.file_path.split('/')[-1].split('.')[1]
    download_path = photo_id + ext
    file.download(custom_path=download_path)

    # process image
    image = Image.open(download_path)
    width, height = image.size
    reference_length = max(width, height)
    ratio = 512 / reference_length
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    image = image.resize((new_width, new_height), Image.ANTIALIAS)
    formatted_path = photo_id + '_formatted.png'
    image.save(formatted_path)

    # send formated image as a document
    document = open(formatted_path, 'rb')
    bot.send_document(chat_id=update.message.chat_id, document=document, filename='sticker.png',
                      caption='Forward this to @Stickers')

    # delete local files
    os.remove(download_path)
    os.remove(formatted_path)

    # increase total uses count by one
    global config
    config['uses'] = config['uses'] + 1


def get_config():
    dir = os.path.dirname(__file__)
    path = os.path.join(dir, 'config.json')
    with open(path) as data_file:
        data = json.load(data_file)
    global config
    config = data


def dump_variables(bot, job):
    data = json.dumps(config)
    dir = os.path.dirname(__file__)
    path = os.path.join(dir, 'config.json')
    with open(path, "w") as f:
        f.write(data)

# logs bot errors thrown
def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    main()