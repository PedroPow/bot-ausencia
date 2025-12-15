import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import os

TOKEN = os.getenv("TOKEN")

CANAL_AUSENCIA_ID = 1449997864255357091
LOG_AUSENCIA_ID = 1449997591713677362
CATEGORIA_TICKETS_ID = 1449997306765250610  # mesma do boletim interno

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== BOTÃO DE EMITIR AUSÊNCIA =====
class AusenciaView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label=" Emitir Ausência", style=discord.ButtonStyle.secondary, custom_id="abrir_ausencia"))

# ===== EVENTO ON_READY PARA ENVIAR O BOTÃO =====
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    canal = bot.get_channel(CANAL_AUSENCIA_ID)
    if canal:
        await canal.purge(limit=5)
        embed = discord.Embed(
            title="Segurança Pública | Sistema de Ausência",
            description="Para registrar sua ausência interno basta apertar o botão que corresponde a categoria desejada!",
            color=discord.Color.dark_gray()
        )
        await canal.send(embed=embed, view=AusenciaView())
    else:
        print(f"❌ Canal de ausência não encontrado.")

# ===== MANUSEIO DO BOTÃO PARA CRIAR O TICKET E FAZER PERGUNTAS =====
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data.get("custom_id") == "abrir_ausencia":
            guild = interaction.guild
            ticket_name = f"ausencia-{interaction.user.name}".replace(" ", "-").lower()

            # Verifica se o usuário já tem um ticket aberto
            for channel in guild.text_channels:
                if channel.name == ticket_name:
                    await interaction.response.send_message("⚠️ Você já possui um ticket de ausência aberto.", ephemeral=True)
                    return

            # Criação do ticket
            category = discord.utils.get(guild.categories, id=CATEGORIA_TICKETS_ID)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            }

            canal = await guild.create_text_channel(ticket_name, overwrites=overwrites, category=category)
            await interaction.response.send_message("✅ Ticket de ausência criado com sucesso!", ephemeral=True)

            await asyncio.sleep(2)
            try:
                await interaction.delete_original_response()
            except:
                pass

            await asyncio.sleep(1)

            perguntas = [
                (" Informe seu **Nome e Patente**:", "nome_patente"),
                (" Informe sua **Guarnição**:", "guarnicao"),
                (" Qual o **motivo da ausência**?", "motivo"),
                (" Qual o **tempo de ausência** (ex: 3 dias)?", "tempo")
            ]
            respostas = {}

            def check(m):
                return m.channel == canal and m.author == interaction.user

            for pergunta, chave in perguntas:
                await canal.send(pergunta)
                try:
                    msg = await bot.wait_for("message", check=check, timeout=300)
                    respostas[chave] = msg.content
                except asyncio.TimeoutError:
                    await canal.send(" Tempo esgotado. O ticket será fechado.")
                    await asyncio.sleep(5)
                    return await canal.delete()

            log_embed = discord.Embed(title=" Registro de Ausência", color=discord.Color.dark_gray())
            log_embed.add_field(name=" Nome e Patente", value=respostas["nome_patente"], inline=False)
            log_embed.add_field(name=" Guarnição", value=respostas["guarnicao"], inline=False)
            log_embed.add_field(name=" Motivo", value=respostas["motivo"], inline=False)
            log_embed.add_field(name=" Tempo", value=respostas["tempo"], inline=False)
            log_embed.set_footer(text=f"Solicitado por {interaction.user}", icon_url=interaction.user.display_avatar.url)
            log_embed.timestamp = discord.utils.utcnow()

            canal_log = guild.get_channel(LOG_AUSENCIA_ID)
            if canal_log:
                await canal_log.send(embed=log_embed)

            await canal.send("✅ Ausência registrada com sucesso. Este ticket será fechado.")
            await asyncio.sleep(5)
            await canal.delete()


# ===== COMANDO OPCIONAL PARA REPOSTAR O BOTÃO =====
@bot.command(name="painel_ausencia")
async def painel_ausencia(ctx):
    canal = bot.get_channel(CANAL_AUSENCIA_ID)
    if canal:
        await canal.purge(limit=5)
        embed = discord.Embed(
            title="Segurança Pública | Sistema de Ausência",
            description="Para registrar sua ausência interno basta apertar o botão que corresponde a categoria desejada!",
            color=discord.Color.dark_gray()
        )
        await canal.send(embed=embed, view=AusenciaView())
        await ctx.send("✅ Painel de ausência repostado!", delete_after=5)
    else:
        await ctx.send("❌ Canal de ausência não encontrado.", delete_after=5)

bot.run(TOKEN)
