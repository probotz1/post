import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import ffmpeg

from config import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID

app = Client("auto_post_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store file paths and states for processing
user_data = {}

@app.on_message(filters.command(["start"]))
def start(client, message):
    message.reply_text("Welcome! Send a photo with a caption to start.")

@app.on_message(filters.photo & filters.caption)
def handle_photo(client, message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['caption'] = message.caption
    photo_path = f"{user_id}_photo.jpg"
    message.photo.download(photo_path)
    user_data[user_id]['photo'] = photo_path
    message.reply_text("Photo received! Now send the video file.")

@app.on_message(filters.video)
def handle_video(client, message):
    user_id = message.from_user.id
    video_path = f"{user_id}_video.mp4"
    message.video.download(video_path)
    user_data[user_id]['video'] = video_path
    message.reply_text("Video received! Now send the audio file.")

@app.on_message(filters.audio)
def handle_audio(client, message):
    user_id = message.from_user.id
    audio_path = f"{user_id}_audio.mp3"
    message.audio.download(audio_path)
    user_data[user_id]['audio'] = audio_path
    message.reply_text("Audio received! Merging files...")

    merge_files(user_id)
    send_custom_options(client, message)

def merge_files(user_id):
    video_path = user_data[user_id]['video']
    audio_path = user_data[user_id]['audio']
    output_path = f"{user_id}_merged.mp4"

    # Use ffmpeg to merge video and audio
    ffmpeg.input(video_path).output(audio_path, v=1, a=1).output(output_path).run()

    user_data[user_id]['merged_video'] = output_path

def send_custom_options(client, message):
    user_id = message.from_user.id
    buttons = [
        [InlineKeyboardButton("Option 1", callback_data=f"{user_id}_option1")],
        [InlineKeyboardButton("Option 2", callback_data=f"{user_id}_option2")],
        [InlineKeyboardButton("Option 3", callback_data=f"{user_id}_option3")],
        [InlineKeyboardButton("Option 4", callback_data=f"{user_id}_option4")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    message.reply_text("Select an option:", reply_markup=reply_markup)

@app.on_callback_query()
def handle_callback_query(client, callback_query):
    user_id, option = callback_query.data.split("_")
    option_caption = {
        "option1": "Here is your video with Option 1!",
        "option2": "Here is your video with Option 2!",
        "option3": "Here is your video with Option 3!",
        "option4": "Here is your video with Option 4!"
    }
    output_path = user_data[int(user_id)]['merged_video']

    client.send_video(
        chat_id=callback_query.message.chat.id,
        video=output_path,
        caption=option_caption[option]
    )

    send_custom_options(client, callback_query.message)

@app.on_message(filters.command(["post"]))
def post_video(client, message):
    user_id = message.from_user.id
    output_path = user_data.get(user_id, {}).get('merged_video')
    if not output_path:
        message.reply_text("No video to post. Please start the process again.")
        return
    
    message.reply_text("Posting video to channel...")
    client.send_video(
        chat_id=CHANNEL_ID,
        video=output_path,
        caption=user_data[user_id]['caption']
    )

    # Clean up files
    os.remove(user_data[user_id]['photo'])
    os.remove(user_data[user_id]['video'])
    os.remove(user_data[user_id]['audio'])
    os.remove(output_path)
    del user_data[user_id]

    message.reply_text("Video posted to channel!")

app.run()
