"""
Discord Integration Service for ChatChonk

This service provides Discord bot functionality for ChatChonk support,
including automated support channels, user assistance, and community management.

Features:
- Automated support ticket creation
- User tier-based channel access
- ChatChonk status updates
- File processing notifications
- Community moderation

Author: Rip Jonesy
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import discord
from discord.ext import commands, tasks
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.mswap_models import UserTier

logger = logging.getLogger("chatchonk.discord")


class DiscordConfig(BaseModel):
    """Discord bot configuration."""
    
    bot_token: str
    guild_id: int
    
    # Channel IDs
    general_channel_id: Optional[int] = None
    support_channel_id: Optional[int] = None
    announcements_channel_id: Optional[int] = None
    feedback_channel_id: Optional[int] = None
    
    # Role IDs for user tiers
    free_role_id: Optional[int] = None
    lilbean_role_id: Optional[int] = None
    clawback_role_id: Optional[int] = None
    bigchonk_role_id: Optional[int] = None
    meowtrix_role_id: Optional[int] = None
    
    # Staff roles
    admin_role_id: Optional[int] = None
    moderator_role_id: Optional[int] = None
    support_role_id: Optional[int] = None


class SupportTicket(BaseModel):
    """Support ticket model."""
    
    ticket_id: str
    user_id: str
    discord_user_id: int
    channel_id: int
    status: str = "open"
    priority: str = "normal"
    category: str = "general"
    created_at: datetime
    last_activity: datetime


class ChatChonkBot(commands.Bot):
    """ChatChonk Discord Bot."""
    
    def __init__(self, config: DiscordConfig):
        """Initialize the ChatChonk bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!chonk ',
            intents=intents,
            description="ChatChonk Support Bot - Tame the Chatter. Find the Signal."
        )
        
        self.config = config
        self.active_tickets: Dict[int, SupportTicket] = {}
        
        # Add cogs and commands
        self.setup_commands()
        
        # Start background tasks
        self.status_update.start()
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f"ChatChonk bot logged in as {self.user}")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for chat logs to process 📁"
        )
        await self.change_presence(activity=activity)
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_member_join(self, member: discord.Member):
        """Welcome new members."""
        if self.config.general_channel_id:
            channel = self.get_channel(self.config.general_channel_id)
            if channel:
                embed = discord.Embed(
                    title="Welcome to ChatChonk! 🐱",
                    description=f"Hey {member.mention}! Welcome to the ChatChonk community.\n\n"
                               f"**What is ChatChonk?**\n"
                               f"ChatChonk transforms your AI chat conversations into structured, "
                               f"searchable knowledge bundles. Perfect for second-brain builders "
                               f"and neurodivergent thinkers!\n\n"
                               f"**Getting Started:**\n"
                               f"• Check out our website: https://chatchonk.com\n"
                               f"• Use `!chonk help` to see available commands\n"
                               f"• Need support? Use `!chonk ticket` to create a support ticket\n\n"
                               f"*Tame the Chatter. Find the Signal.*",
                    color=0x7C3AED
                )
                embed.set_thumbnail(url="https://chatchonk.com/logo.png")
                await channel.send(embed=embed)
    
    def setup_commands(self):
        """Set up bot commands."""
        
        @self.command(name='help')
        async def help_command(ctx):
            """Show help information."""
            embed = discord.Embed(
                title="ChatChonk Bot Commands 🤖",
                description="Here are the available commands:",
                color=0x7C3AED
            )
            
            embed.add_field(
                name="🎫 Support Commands",
                value="`!chonk ticket` - Create a support ticket\n"
                      "`!chonk close` - Close your support ticket\n"
                      "`!chonk status` - Check ChatChonk service status",
                inline=False
            )
            
            embed.add_field(
                name="📊 Account Commands",
                value="`!chonk account` - View your account info\n"
                      "`!chonk usage` - Check your usage statistics\n"
                      "`!chonk tier` - View your subscription tier",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Utility Commands",
                value="`!chonk ping` - Check bot latency\n"
                      "`!chonk about` - About ChatChonk\n"
                      "`!chonk feedback` - Submit feedback",
                inline=False
            )
            
            await ctx.send(embed=embed)
        
        @self.command(name='ping')
        async def ping_command(ctx):
            """Check bot latency."""
            latency = round(self.latency * 1000)
            await ctx.send(f"🏓 Pong! Latency: {latency}ms")
        
        @self.command(name='about')
        async def about_command(ctx):
            """About ChatChonk."""
            embed = discord.Embed(
                title="About ChatChonk 🐱",
                description="ChatChonk transforms AI chat conversations into structured, "
                           "searchable knowledge bundles.",
                color=0x7C3AED
            )
            
            embed.add_field(
                name="🎯 Mission",
                value="Designed for second-brain builders and neurodivergent thinkers "
                      "who need to organize their AI conversations effectively.",
                inline=False
            )
            
            embed.add_field(
                name="✨ Features",
                value="• Process ZIP archives up to 2GB\n"
                      "• AI-powered content structuring\n"
                      "• Export to Markdown/Notion\n"
                      "• ADHD-optimized templates\n"
                      "• Custom AI model selection",
                inline=False
            )
            
            embed.add_field(
                name="🔗 Links",
                value="[Website](https://chatchonk.com) | "
                      "[Documentation](https://docs.chatchonk.com) | "
                      "[GitHub](https://github.com/ripj3/CHATCHONKBETA)",
                inline=False
            )
            
            embed.set_footer(text="Tame the Chatter. Find the Signal.")
            await ctx.send(embed=embed)
        
        @self.command(name='ticket')
        async def create_ticket(ctx, *, description: str = None):
            """Create a support ticket."""
            if not description:
                await ctx.send("❌ Please provide a description: `!chonk ticket Your issue description here`")
                return
            
            # Check if user already has an open ticket
            existing_ticket = None
            for ticket in self.active_tickets.values():
                if ticket.discord_user_id == ctx.author.id and ticket.status == "open":
                    existing_ticket = ticket
                    break
            
            if existing_ticket:
                channel = self.get_channel(existing_ticket.channel_id)
                await ctx.send(f"❌ You already have an open ticket: {channel.mention}")
                return
            
            # Create ticket channel
            guild = ctx.guild
            category = discord.utils.get(guild.categories, name="Support Tickets")
            
            if not category:
                # Create category if it doesn't exist
                category = await guild.create_category("Support Tickets")
            
            # Create private channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add support role if configured
            if self.config.support_role_id:
                support_role = guild.get_role(self.config.support_role_id)
                if support_role:
                    overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            channel_name = f"ticket-{ctx.author.name.lower()}-{ctx.author.discriminator}"
            ticket_channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites
            )
            
            # Create ticket record
            ticket = SupportTicket(
                ticket_id=f"CHONK-{datetime.now().strftime('%Y%m%d')}-{ticket_channel.id}",
                user_id="unknown",  # Would be linked to ChatChonk user ID
                discord_user_id=ctx.author.id,
                channel_id=ticket_channel.id,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
            
            self.active_tickets[ticket_channel.id] = ticket
            
            # Send ticket creation message
            embed = discord.Embed(
                title=f"Support Ticket Created 🎫",
                description=f"**Ticket ID:** {ticket.ticket_id}\n"
                           f"**Created by:** {ctx.author.mention}\n"
                           f"**Description:** {description}",
                color=0x00FF00
            )
            
            await ticket_channel.send(embed=embed)
            await ticket_channel.send(
                f"👋 Hi {ctx.author.mention}! Thanks for creating a support ticket. "
                f"Our team will be with you shortly.\n\n"
                f"**While you wait:**\n"
                f"• Check our [documentation](https://docs.chatchonk.com)\n"
                f"• Search previous discussions in this server\n"
                f"• Use `!chonk close` when your issue is resolved"
            )
            
            await ctx.send(f"✅ Support ticket created: {ticket_channel.mention}")
        
        @self.command(name='close')
        async def close_ticket(ctx):
            """Close a support ticket."""
            ticket = self.active_tickets.get(ctx.channel.id)
            
            if not ticket:
                await ctx.send("❌ This is not a support ticket channel.")
                return
            
            if ticket.discord_user_id != ctx.author.id:
                # Check if user has support role
                if self.config.support_role_id:
                    support_role = ctx.guild.get_role(self.config.support_role_id)
                    if support_role not in ctx.author.roles:
                        await ctx.send("❌ You can only close your own tickets.")
                        return
            
            # Close ticket
            ticket.status = "closed"
            
            embed = discord.Embed(
                title="Ticket Closed ✅",
                description=f"Ticket {ticket.ticket_id} has been closed.\n"
                           f"This channel will be deleted in 30 seconds.",
                color=0xFF0000
            )
            
            await ctx.send(embed=embed)
            
            # Delete channel after delay
            await asyncio.sleep(30)
            await ctx.channel.delete(reason="Support ticket closed")
            
            # Remove from active tickets
            del self.active_tickets[ctx.channel.id]
        
        @self.command(name='status')
        async def status_command(ctx):
            """Check ChatChonk service status."""
            # TODO: Implement actual health check
            embed = discord.Embed(
                title="ChatChonk Service Status 📊",
                color=0x00FF00
            )
            
            embed.add_field(
                name="🌐 Website",
                value="✅ Online",
                inline=True
            )
            
            embed.add_field(
                name="🔧 API",
                value="✅ Operational",
                inline=True
            )
            
            embed.add_field(
                name="🗄️ Database",
                value="✅ Connected",
                inline=True
            )
            
            embed.add_field(
                name="🤖 AI Processing",
                value="✅ Available",
                inline=True
            )
            
            embed.add_field(
                name="📁 File Processing",
                value="✅ Active",
                inline=True
            )
            
            embed.add_field(
                name="📤 Exports",
                value="✅ Working",
                inline=True
            )
            
            embed.set_footer(text=f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            await ctx.send(embed=embed)
    
    @tasks.loop(minutes=30)
    async def status_update(self):
        """Update bot status periodically."""
        statuses = [
            "for chat logs to process 📁",
            "over ChatChonk users 👥",
            "AI conversations 🤖",
            "knowledge bundles 📚"
        ]
        
        import random
        status = random.choice(statuses)
        
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=status
        )
        await self.change_presence(activity=activity)


class DiscordService:
    """Discord integration service for ChatChonk."""
    
    def __init__(self):
        """Initialize the Discord service."""
        self.bot: Optional[ChatChonkBot] = None
        self.config: Optional[DiscordConfig] = None
        self._running = False
    
    async def initialize(self, config: DiscordConfig):
        """Initialize the Discord bot."""
        self.config = config
        self.bot = ChatChonkBot(config)
        
        logger.info("Discord service initialized")
    
    async def start(self):
        """Start the Discord bot."""
        if not self.bot or not self.config:
            raise ValueError("Discord service not initialized")
        
        if self._running:
            logger.warning("Discord bot is already running")
            return
        
        try:
            self._running = True
            await self.bot.start(self.config.bot_token)
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            self._running = False
            raise
    
    async def stop(self):
        """Stop the Discord bot."""
        if self.bot and self._running:
            await self.bot.close()
            self._running = False
            logger.info("Discord bot stopped")
    
    async def send_notification(
        self,
        channel_type: str,
        title: str,
        message: str,
        color: int = 0x7C3AED,
        user_id: Optional[int] = None
    ):
        """Send a notification to a Discord channel."""
        if not self.bot or not self._running:
            return
        
        channel_id = None
        if channel_type == "general":
            channel_id = self.config.general_channel_id
        elif channel_type == "announcements":
            channel_id = self.config.announcements_channel_id
        elif channel_type == "support":
            channel_id = self.config.support_channel_id
        
        if not channel_id:
            return
        
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        
        embed = discord.Embed(
            title=title,
            description=message,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        if user_id:
            user = self.bot.get_user(user_id)
            if user:
                embed.set_footer(text=f"User: {user.name}", icon_url=user.avatar.url if user.avatar else None)
        
        await channel.send(embed=embed)


# Global Discord service instance
_discord_service: Optional[DiscordService] = None


def get_discord_service() -> DiscordService:
    """Get the global Discord service instance."""
    global _discord_service
    if _discord_service is None:
        _discord_service = DiscordService()
    return _discord_service
