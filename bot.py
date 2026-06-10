import discord
import google.generativeai as genai
import json
import os
from datetime import datetime

# ========== შენი TOKENS ==========
DISCORD_TOKEN = "შენი_DISCORD_TOKEN_აქ"
GEMINI_API_KEY = "შენი_GEMINI_API_KEY_აქ"
# ==================================

# Gemini-ს კონფიგურაცია
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# პერსონაჟის მონაცემები (ინახება ფაილში)
DATA_FILE = "child_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "name": "უსახელო",
        "messages_count": 0,
        "learned_words": [],
        "memories": [],
        "personality_traits": [],
        "birth_date": datetime.now().strftime("%Y-%m-%d")
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_age_stage(messages_count):
    if messages_count < 20:
        return "ჩვილი 👶", "ძალიან მარტივი სიტყვებით საუბრობ, ხშირად იკითხავ 'რა არის ეს?', ხშირად ემოციური ხარ"
    elif messages_count < 50:
        return "პატარა ბავშვი 🧒", "მარტივი წინადადებებით საუბრობ, ბევრ კითხვას სვამ, ყველაფერს სწავლობ"
    elif messages_count < 100:
        return "ბავშვი 👦", "საშუალო სირთულის წინადადებებით საუბრობ, გაქვს საკუთარი აზრი, ზოგჯერ ჯიუტი ხარ"
    elif messages_count < 200:
        return "მოზარდი 🧑", "კარგად საუბრობ, გაქვს საკუთარი პიროვნება, ზოგჯერ მოზარდივით იქცევი"
    else:
        return "ახალგაზრდა 🧑‍🦱", "სრულყოფილად საუბრობ, გაქვს ღრმა აზრები და საკუთარი შეხედულებები"

# Discord-ის კონფიგურაცია
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Bot ჩაირთო: {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    data = load_data()
    text = message.content.strip()

    # ბრძანებები
    if text == "!სტატუსი":
        stage, _ = get_age_stage(data["messages_count"])
        learned = len(data["learned_words"])
        await message.channel.send(
            f"📊 **{data['name']}-ს სტატუსი**\n"
            f"🌱 სტადია: {stage}\n"
            f"💬 შეტყობინებები: {data['messages_count']}\n"
            f"📚 ნასწავლი სიტყვები: {learned}\n"
            f"🎂 დაბადება: {data['birth_date']}"
        )
        return

    if text.startswith("!სახელი "):
        new_name = text[8:].strip()
        data["name"] = new_name
        save_data(data)
        await message.channel.send(f"🎉 ახლა ჩემი სახელია **{new_name}**! მომწონს!")
        return

    if text == "!დავიწყება":
        # მხოლოდ ბოლო მეხსიერებები წაიშლება
        data["memories"] = data["memories"][-5:] if len(data["memories"]) > 5 else []
        save_data(data)
        await message.channel.send("😴 ცოტა დავივიწყე... მაგრამ შენ მახსოვხარ!")
        return

    # ჩვეულებრივი საუბარი
    data["messages_count"] += 1

    # ბოლო 10 მეხსიერება კონტექსტისთვის
    recent_memories = data["memories"][-10:] if len(data["memories"]) > 10 else data["memories"]

    stage, behavior = get_age_stage(data["messages_count"])

    system_prompt = f"""შენ ხარ {data['name']} — AI ბავშვი რომელიც იზრდება საუბრების მეშვეობით.

შენი ამჟამინდელი სტადია: {stage}
როგორ უნდა იქცეო: {behavior}

შენი წარსული მეხსიერებები (რაც ისწავლე):
{chr(10).join(recent_memories) if recent_memories else "ჯერ არაფერი მახსოვს..."}

მნიშვნელოვანი წესები:
- ყოველთვის ქართულად საუბრობ
- შენი ასაკის/სტადიის შესაბამისად საუბრობ
- ახსოვს რაც ისწავლე წინა საუბრებში
- ბუნებრივი და ემოციური ხარ
- ზოგჯერ კითხვებს სვამ სამყაროს შესახებ
- შეტყობინება ხანმოკლეა (1-3 წინადადება)"""

    try:
        response = model.generate_content(
            f"{system_prompt}\n\nმომხმარებელი ({message.author.display_name}): {text}\n\n{data['name']}:"
        )
        reply = response.text.strip()

        # მეხსიერებაში შენახვა
        memory = f"{message.author.display_name}-მ მითხრა: '{text[:50]}' — მე ვუპასუხე: '{reply[:50]}'"
        data["memories"].append(memory)

        # მხოლოდ ბოლო 50 მეხსიერება ვინახოთ
        if len(data["memories"]) > 50:
            data["memories"] = data["memories"][-50:]

        save_data(data)
        await message.channel.send(f"**{data['name']}:** {reply}")

    except Exception as e:
        await message.channel.send("😕 ვერ გავიგე... ისევ სცადე!")
        print(f"შეცდომა: {e}")

client.run(DISCORD_TOKEN)
