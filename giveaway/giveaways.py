import config
from nextcord import Interaction,SlashOption
import nextcord
from nextcord.ext import commands,tasks
import mysql.connector
import os
import datetime
import random
intents = nextcord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)




db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="giveaway"
)
cursor = db.cursor(dictionary=True)




@bot.event
async def on_ready():
        print("bot is ready")
        check_giveaways.start()
      
@tasks.loop(seconds=10)
async def check_giveaways():
        cursor.execute("SELECT * FROM giveaway")
        for row in cursor.fetchall():
            if float(row["end"]) - float(datetime.datetime.now(datetime.UTC).timestamp()) <= 0:
                try:
                    channel = await bot.fetch_channel(int(row["channel"]))
                    message = await channel.fetch_message(int(row["message"]))
                    host = await bot.fetch_user(int(row["host"]))
                    joins = []
                    for reaction in message.reactions:
                        if str(reaction.emoji) == "🎉":
                            users =  reaction.users()
                            async for user in users:
                                if not user.id == bot.user.id:
                                    joins.append(user.mention)
                            continue

                    if len(joins) == 0:
                        winnerslist = []
                    else:
                        if len(joins) <= int(row["winners"]):
                            winnerslist = random.sample(joins, len(joins))
                        else:
                            winnerslist = random.sample(joins, int(row["winners"]))

                    if len(winnerslist) == 0:
                        embed = nextcord.Embed(
                            title=f"giveaway by {host.name}",
                            description="Giveaway is ended but there are no winners",
                            color=nextcord.Color.dark_red()
                        )
                    else:
                        embed = nextcord.Embed(
                            title=f"giveaway by {host.name}",
                            description=f"Giveaway is ended, winners are:\n" + "\n".join(winnerslist),
                            color=nextcord.Color.dark_red()
                        )

                    await message.edit(embed=embed)
                    cursor.execute("DELETE FROM giveaway WHERE message = %s", (row['message'],))
                    db.commit()
                except Exception as e:
                     print(e)
                     cursor.execute("DELETE FROM giveaway WHERE message = %s", (row['message'],))
                     db.commit()
               
   



@bot.slash_command(name="giveaway", description="Start a giveaway")
async def giveaway(interaction: Interaction,
                       winners: int = SlashOption(description="number of winners"),
                       prize: str = SlashOption(description="name/description of prize"),
                       end: str = SlashOption(description="gives time for example id 20h")):
        times = end.split(" ")
        end_date = datetime.datetime.now(datetime.timezone.utc)
        for i in times:
            if i.endswith("d"):
                end_date += datetime.timedelta(days=int(i[:-1]))
            elif i.endswith("h"):
                end_date += datetime.timedelta(hours=int(i[:-1]))
            elif i.endswith("m"):
                end_date += datetime.timedelta(minutes=int(i[:-1]))
            elif i.endswith("s"):
                end_date += datetime.timedelta(seconds=int(i[:-1]))
            else:
                await interaction.response.send_message(f"invalid format {i}", ephemeral=True)
                return

        embed = nextcord.Embed(title=f"giveaway by {interaction.user.name}",
                               description=f"Ends at {str(end_date).split('.')[0]}",
                               color=nextcord.Color.dark_orange())
        embed.add_field(name="prize", value=prize)
        embed.add_field(name="ends", value=f"<t:{str(end_date.timestamp()).split('.')[0]}:f> UTC")
        embed.add_field(name="winners:", value=winners)
        embed.set_thumbnail(url=interaction.user.display_avatar)
        await interaction.response.send_message("giveaway is created")
        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("🎉")
        sql = "INSERT INTO giveaway (guild, channel, message, host, winners, prize, start, end) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (interaction.guild.id, interaction.channel.id, msg.id, interaction.user.id, winners, prize, datetime.datetime.now(datetime.timezone.utc).timestamp(), end_date.timestamp())
        cursor.execute(sql, val)
        db.commit()
 
 

bot.run(config.TOKEN)