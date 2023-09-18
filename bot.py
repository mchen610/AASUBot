import discord
import asyncio
import random
from os import path


intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
intents.message_content = True 

client.run("MTE1MjQ0NzU0ODg3NTg3ODUzMA.G0wcx7.l_GVcVLT7x2FOAyML-9Ulkdps32Uj0W6PHEZos")
