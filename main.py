import discord
from discord.ext import commands
import aiohttp
import asyncio
import re
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

API_URL = "http://78.154.103.25:14187/api/bypass?url="

if not TOKEN:
    raise ValueError("Missing TOKEN in .env")


intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=commands.when_mentioned,
    intents=intents,
    help_command=None
)


class CopyButton(discord.ui.Button):
    def __init__(self, result):
        super().__init__(
            label="Mobile Copy",
            style=discord.ButtonStyle.primary
        )
        self.result = result

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            self.result,
            ephemeral=True
        )


class SourceCodeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Get Bot Source Code",
            style=discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "https://github.com/public-account-7/auto-bypass-discord-bot",
            ephemeral=True
        )


class ProcessingView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    "# Processing..."
                ),
                discord.ui.Separator(),
                discord.ui.TextDisplay(
                    "Please wait while I bypass the link."
                )
            )
        )


class SuccessView(discord.ui.LayoutView):
    def __init__(self, result):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    "# Success!"
                ),
                discord.ui.Separator(),
                discord.ui.TextDisplay(
                    f"```\n{result}\n```"
                ),
                discord.ui.Separator(),
                discord.ui.ActionRow(
                    CopyButton(result),
                    SourceCodeButton()
                )
            )
        )


class FailedView(discord.ui.LayoutView):
    def __init__(self, message):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay(
                    "# Failed!"
                ),
                discord.ui.Separator(),
                discord.ui.TextDisplay(
                    message
                )
            )
        )


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if (
        message.guild
        and message.guild.id == GUILD_ID
        and message.channel.id == CHANNEL_ID
    ):
        urls = re.findall(
            r"https?://[^\s]+",
            message.content
        )

        for url in urls:
            msg = await message.reply(
                view=ProcessingView()
            )

            try:
                encoded = urllib.parse.quote(
                    url,
                    safe=""
                )

                timeout = aiohttp.ClientTimeout(
                    total=120
                )

                async with aiohttp.ClientSession(
                    timeout=timeout
                ) as session:

                    async with session.get(
                        API_URL + encoded
                    ) as res:

                        data = await res.json(
                            content_type=None
                        )

                        status = data.get("status")

                        if status == "success":
                            result = data.get("result")

                            await msg.edit(
                                view=SuccessView(result)
                            )

                        elif status == "failed":
                            await msg.edit(
                                view=FailedView(
                                    data.get(
                                        "message",
                                        "Failed to bypass"
                                    )
                                )
                            )

                        elif status == "error":
                            await msg.edit(
                                view=FailedView(
                                    data.get(
                                        "message",
                                        "Unknown error"
                                    )
                                )
                            )

                        else:
                            await msg.edit(
                                view=FailedView(
                                    "Invalid API response."
                                )
                            )

            except asyncio.TimeoutError:
                await msg.edit(
                    view=FailedView(
                        "API request timed out."
                    )
                )

            except Exception as e:
                print("Error:", e)

                await msg.edit(
                    view=FailedView(
                        str(e)
                    )
                )


bot.run(TOKEN)
