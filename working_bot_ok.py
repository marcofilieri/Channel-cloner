import configparser
import json
import time
import traceback
from datetime import datetime

from telethon import TelegramClient
from telethon import *
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import (GetHistoryRequest)
from telethon.tl.types import (
    PeerChannel
)

# some functions to parse json date
from telethon.tl.types.messages import Messages


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


# Reading Configs
config = configparser.ConfigParser()
config.read("config.ini")

# Setting configuration values
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

api_hash = str(api_hash)

phone = config['Telegram']['phone']
username = config['Telegram']['username']

# Create the client and connect
client = TelegramClient(username, api_id, api_hash)


async def main(phone):
    await client.start()
    print("Client Created")
    # Ensure you're authorized
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))

    me = await client.get_me()

    user_input_channel = input('enter source entity(telegram URL or entity id):')
    user_output_channel = input('enter destination entity(telegram URL or entity id):')
    if user_input_channel.isdigit():
        source_entity = PeerChannel(int(user_input_channel))
        destination_entity = PeerChannel(int(user_output_channel))
    else:
        source_entity = user_input_channel
        destination_entity = user_output_channel


    source_channel_entity = await client.get_entity(source_entity)
    destination_channel_entity = await client.get_entity(destination_entity)

    offset_id = 0
    limit = 1
    all_messages = []
    total_messages = 0
    total_count_limit = 0

    all_errors = []

    while True:

        history = []

        async for item in client.iter_messages(
                entity=source_channel_entity,
                limit=limit,
                offset_date=None,
                offset_id=offset_id,
                max_id=0,
                min_id=0,
                add_offset=0,
                search=None,
                filter=None,
                wait_time=None,
                ids=None,
                reverse=True
        ):
            try:
                history.append(item)
            except:
                print("Cannot iterate object with id: %s" % (item['id']))
                all_errors.append("Cannot iterate object with id: %s" % (item['id']))

        if not history:
            break

        for message in history:
            all_messages.append(message.to_dict())
            try:
                await client.send_message(destination_channel_entity, message)
                print("Message sent. Id:" + str(message.to_dict()['id']))
            except:
                print("Error occurred on message id:" + str(message.to_dict()['id']))
                all_errors.append("Error occurred on message id:" + str(message.to_dict()['id']))
                # traceback.print_exc()
            time.sleep(5)
        offset_id = history[len(history) - 1].id
        total_messages = len(all_messages)
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break

    with open('channel_messages.json', 'w') as outfile, open('errors.txt', 'w') as errors_output:
        json.dump(all_messages, outfile, cls=DateTimeEncoder)
        for line in all_errors:
            errors_output.write(line)


with client:
    client.loop.run_until_complete(main(phone))
