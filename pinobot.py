import discord
import time
import random
import datetime
import asyncio
import aiohttp
import tempfile
import json
import io
import re
import base64
import threading
import traceback
import os 
import os.path

import logging

client = discord.Client()

HELP = """\
.
*Set channel for pins*
<@{bot_id}> channel {channel_name}

*Set threshold of pin emoji reactions to pin a message, set to 0 to disable (default: 5)*
<@{bot_id}> threshold {threshold}  

*Force archive all pins right now*
<@{bot_id}> archive  

*Repository*
<https://github.com/nuukedo29/pinobot>
"""

db = {
	"server_settings": {}
}

def commit():
	with open("data.json", "w") as file:
		file.write(json.dumps(db, indent="\t", ensure_ascii=False))

if not os.path.exists("./data.json"):
	commit()

with open("data.json", "r") as file:
	db = json.loads(file.read())

async def download(url):
	async with aiohttp.ClientSession() as session:
		response = await session.get(url)
		return io.BytesIO(await response.read())

@client.event
async def on_ready():
	print(f'Logged in as {client.user.name} ({client.user.id})' )
	print(f'Invite https://discord.com/oauth2/authorize?client_id={client.user.id}&permissions=75776&scope=bot' )
	print( "="*20 )

@client.event
async def on_message(message):

	if message.author.id == client.user.id or message.author.bot:
		return 

	command = re.findall(r"\<\@[\!\&]?{}\>\s*(.*)".format(client.user.id), message.content)

	if command:

		server_settings = db["server_settings"].get(str(message.guild.id), {})
		pin_channel = None

		if server_settings.get("channel"):
			pin_channel = client.get_channel(int(server_settings.get("channel")))

		if command[0]:

			command, arguments = re.findall(r"([^\s]+)\s*(.*)", command[0])[0]
			command = command.lower()

			if command in ["channel", "threshold", "archive"]:
				if not message.author.guild_permissions.administrator:
					return await message.channel.send("You must have administrator permissions")
				else:
					if not server_settings:
						db["server_settings"][str(message.guild.id)] = {}
						commit()


			if command == "channel":

				channel_id = re.findall(r"\<\#(.*?)\>", arguments)[0]

				if not channel_id:
					return await message.channel.send("Invalid channel specified")
				
				channel = client.get_channel(int(channel_id))

				if channel.guild.id != message.guild.id:
					return await message.channel.send("https://www.youtube.com/watch?v=mmCzTJTK1H8")

				db["server_settings"][str(message.guild.id)]["channel"] = channel_id
				commit()

				return await message.channel.send(f'Successfully updated channel to <#{channel_id}>')

			if command == "threshold":

				threshold = int(re.findall(r"(\d+)", arguments)[0])

				db["server_settings"][str(message.guild.id)]["threshold"] = threshold
				commit()

				return await message.channel.send(f'Successfully updated threshold to {threshold}')

			if command == "archive":

				channel_id = db["server_settings"][str(message.guild.id)].get("channel")

				if not channel_id:
					return await message.channel.send("Pin channel is not set")

				channel = client.get_channel(int(channel_id))

				if not channel:
					return await message.channel.send("Pin channel doesn't exist anymore")
				
				for pin_message in await message.channel.pins():

					files = []

					for attachment in pin_message.attachments:
						files.append(discord.File(await download(attachment.url), attachment.filename))
					
					await channel.send(
						content=f"**{pin_message.author.name}#{pin_message.author.discriminator}** " + pin_message.content,
						files=files	
					)

					await pin_message.unpin()
					
				return await message.channel.send("Successfully archived pins")

		return await message.channel.send(HELP.format(
			bot_id=client.user.id,
			channel_name=f'<#{pin_channel.id}>' if pin_channel else "#example",
			threshold=server_settings.get("threshold", "5")
		))


@client.event
async def on_raw_reaction_add(reaction):

	if reaction.emoji.name == "📌":
		server_settings = db["server_settings"].get(str(reaction.guild_id), {})
		threshold = server_settings.get("threshold", 5)

		if threshold:
			message = await client.get_guild(reaction.guild_id).get_channel(reaction.channel_id).fetch_message(reaction.message_id)
			pin_count = 0

			for reaction in message.reactions:
				if reaction.emoji == "📌":
					pin_count = reaction.count
					break 
			
			if pin_count >= threshold:
				await message.pin() 

@client.event
async def on_guild_channel_pins_update(channel, last_pin):
	# TODO: Self-run archiving based on amount of pinned messages 
	pass
	
while True:
	try:
		asyncio.get_event_loop().run_until_complete(client.start(os.environ.get("DISCORD_TOKEN")))
	except: 
		pass
		
	time.sleep(1)
