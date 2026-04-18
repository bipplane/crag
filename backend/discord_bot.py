import os
import discord
import asyncio
from dotenv import load_dotenv
from services.rag_service import query_module_content
from services.adk_service import generate_course_summary

# Load environment variables for Discord and Pinecone/GenAI
load_dotenv('.env')

# Adjust the intents so our bot can read message contents
intents = discord.Intents.default()
intents.message_content = True

class CRAGBot(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def on_message(self, message):
        # Ignore messages sent by the bot itself
        if message.author.id == self.user.id:
            return

        # Check if the bot was mentioned in the message
        if self.user in message.mentions:
            # Remove the bot's mention from the input text to extract just the question
            question = message.content.replace(f'<@{self.user.id}>', '').strip()
            
            if not question:
                await message.reply("Please ask a question after mentioning me!")
                return

            # Note: Since the RAG functions are synchronous, we run them in a thread pool 
            # to prevent blocking the Discord event loop.
            # For demonstration, we're hardcoding the tenant/module to the ones used 
            # previously ("ryanc", "cs2030s"). You can also link these to the server (message.guild.id).
            tenant_id = "ryanc"     # e.g., str(message.guild.id)
            module_id = "cs2030s" 
            
            # Simple keyword-based intent classification
            # If the user asks for a summary or comprehensive guide, use ADK Orchestration
            summary_keywords = ["summarize", "summarise", "summary", "study guide", "comprehensive review"]
            intent = "summary" if any(kw in question.lower() for kw in summary_keywords) else "qa"
            
            try:
                # Provide a typing indicator while processing the query
                async with message.channel.typing():
                    if intent == "summary":
                        # Send acknowledgment first
                        await message.reply(f"⏳ Thanks for the request! I'm synthesizing a comprehensive guide asynchronously. I will ping you when it's done.")
                        
                        # Process the heavy workload asynchronously using asyncio instead of Celery/Redis
                        response = await asyncio.to_thread(
                            generate_course_summary, 
                            tenant_id, 
                            module_id, 
                            question
                        )
                        # Reply with the completed summary
                        await message.reply(f"✅ <@{message.author.id}>, your asynchronous task is complete!\n\n> {response['summary']}")
                    else:
                        # Synchronous Low-Latency LlamaIndex RAG Pipeline  
                        response = await asyncio.to_thread(
                            query_module_content, 
                            tenant_id, 
                            module_id, 
                            question
                        )
                        await message.reply(str(response))
            except Exception as e:
                print(f"Error handling Discord message: {e}")
                await message.reply("Oops, something went wrong while searching the database.")

if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set in .env")
        exit(1)
        
    client = CRAGBot(intents=intents)
    client.run(token)
