#################### 디스코드 그림봇 By makejoy ####################
# ver. 2024.07.25
# pip install discord requests aiohttp BeautifulSoup4 pillow
# .env예시 파일 참조하여 .env 파일 생성 및 수정 필요
###################################################################

import io
import re
import os
import sys
import json
import base64
import discord
import aiohttp
import requests
import urllib.request
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from discord.ext import commands
from PIL import Image, PngImagePlugin
load_dotenv()

# 디스코드 봇 토큰
TOKEN = os.environ['DISCORD_BOT_TOKEN']

# 디스코드 봇 접두사 (미설정 시 '/', 여러개 설정 가능)
PREFIXS = os.environ.get("PREFIXS", "/").split(',')

# 도움말 명령어 (미설정 시 '그림봇', 여러개 설정 가능)
HELP_CMDS = os.environ.get("HELP_CMDS", "그림봇").split(',')

# 그리기 명령어 (미설정 시 '그림', 여러개 설정 가능)
DRAW_CMDS = os.environ.get("DRAW_CMDS", "그림").split(',')

# 디스코드 봇 답장용 헤더
BOT_HEADER = "[" + os.environ.get("BOT_NAME", "MJ Draw Bot") + "] "

# 디스코드 봇 Intents 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = PREFIXS, intents = intents)

# 봇 상태 메시지
@bot.event
async def on_ready():   
    await bot.change_presence(status = discord.Status.online, activity = discord.Game(f"{PREFIXS[0]}{HELP_CMDS[0]}"))

# 봇 에러 예외처리
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass

# 원본 메시지 삭제시 답장 삭제
@bot.event
async def on_message_delete(message):  

    # 메시지 찾기
    target_messages = []
    async for msg in message.channel.history(limit = 30):
        if msg.reference and msg.reference.message_id == message.id and msg.author.id == bot.user.id:
            target_messages.append(msg)
            
    # 찾은 메시지 삭제
    for target_message in target_messages:
        await target_message.delete()

# 번역 (deepLX API)
def translate(text):
    TRANSLATE_API_URL = os.environ['TRANSLATE_API_URL']
    payload = {
        "target_lang": "en",
        "text": text
    }
    response = requests.post(TRANSLATE_API_URL, data = payload)
    res = response.json()
    return res["translations"][0]["text"]

# 배열에서 검색
def get_key_or_value(msg, array):
    if msg in array:
        return msg
    else:
        for key, value in array.items():
            if value == msg or msg in value:
                return key
    return None 

# stable diffusion api url (미설정시 기본)
STABLE_API_URL = os.environ.get("STABLE_API_URL", "http://127.0.0.1:7860")

# 설치된 모든 모델 불러오기
model_data  = requests.get(f"{STABLE_API_URL}/sdapi/v1/sd-models").json()
models = {}
for item in model_data:
    title = item["title"]
    base_name = item["model_name"].split()[0]
    name = base_name.split('_')[0].split('-')[0]
    models[title] = name

# 모든 샘플러 불러오기
sampler_data  = requests.get(f"{STABLE_API_URL}/sdapi/v1/samplers").json()
samplers = {}
for item in sampler_data:
    name = item["name"]
    aliases = item["aliases"]
    samplers[name] = aliases

# 현재 모델 불러오기
now_model = requests.get(f"{STABLE_API_URL}/sdapi/v1/options").json().get("sd_model_checkpoint", None)

# 이미 생성중인 서버에서 새로운 생성 방지를 위한 선언
working_guilds = []

# 영어가 아닌 경우 자동 번역을 위한 선언
excluded_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}\\|;:'\",.<>/?`~’“”\n ")

# 이미지 스포일러 처리를 위한 선정적 단어 선언 (영어)
spoiler_words = [
    'ahegao', 'anal', 'ass', 
    'bdsm', 'bestiality', 'bitch', 'blowjop', 'body', 'bondage', 'boob', 'breast', 'bukkake', 
    'chest', 'clit', 'condom', 'crotch', 'cum', 
    'dick', 'dildo', 
    'ejaculation', 'erotic', 
    'fellatio', 'female', 'fuck', 'furry', 
    'girl', 'guro', 
    'handjob', 'hentai', 'hole', 'horny', 'kiss', 
    'lewd', 'lingerie', 'loli', 'lovejuice', 
    'masturbation', 'milf', 
    'naked', 'netorare', 'nipple', 'nsfw', 'ntr', 'nude', 
    'oppai', 'oral', 'orgasm', 
    'paizuri', 'penis', 'pregnant', 'pussy', 
    'racy', 'rape', 
    'semen', 'sex', 'shirtlift', 'slave', 'spankthroat', 'squirting', 
    'tit', 
    'underwear', 
    'vagin', 'vulva', 
    'without', 'woman'
]

# 이미지 생성시 기본값 설정
defaults = [None, "easynegative", now_model, 480, 640, sampler_data[0]["name"], 7, 30]

# 봇 도움말 명령어
@bot.command(name = 'how', aliases = HELP_CMDS)
async def how(ctx):
    await ctx.reply(f"```ini\n{BOT_HEADER} - 도움말\n\n\n[명령어 구성]\n{PREFIXS[0]}{DRAW_CMDS[0]} 요청태그 | 제외태그 | 모델 | 너비 | 높이 | 샘플러 | 스케일 | 스텝\n\n[구성 설명]\n<요청태그> : 그림에 반영할 내용\n<제외태그> : 그림에 반영하지 않을 내용\n<모델> : 그림의 종류, 스타일\n<너비> : 그림의 가로 크기 (최대값 : 800)\n<높이> : 그림의 세로 크기 (최대값 : 800)\n<샘플러> : 그림의 색채, 특성\n<스케일> : 요청태그가 그림에 미치는 영향 (최대값 : 10)\n<스텝> : 그림 생성 단계 수 (최대값 : 30)\n\n* 태그는 영어로 번역되므로 오번역이 있을 수 있습니다.\n* 정확한 결과를 위해서는 태그를 영어로 작성하세요.\n* 요청태그를 제외한 모든 값은 생략할 수 있습니다.\n\n[생략시 기본 설정 값]\n<제외태그> : {defaults[1]}\n<모델> : {defaults[2].split('_')[0].split('-')[0]}\n<너비> : {defaults[3]}\n<높이> : {defaults[4]}\n<샘플러> : {defaults[5]}\n<스케일> : {defaults[6]}\n<스텝> : {defaults[7]}\n\n* 설정을 변경하려면 명령어 구조에 따라 | 로 구분하여 입력하세요.\n* 변경하지 않을 값은 구조에 따라 | 로 구분하되, 빈칸으로 두세요.\n\n[명령어 예시]\n{PREFIXS[0]}{DRAW_CMDS[0]} 높은 디테일, 리그오브레전드, 아리\n{PREFIXS[0]}{DRAW_CMDS[0]} high detailed, league of legends, ahri | easynegative\n{PREFIXS[0]}draw 높은 디테일, 리그오브레전드, 아리 | easynegative | {defaults[2].split('_')[0].split('-')[0]} | 800 | 400\n{PREFIXS[0]}draw high detailed, league of legends, ahri | easynegative | {defaults[2].split('_')[0].split('-')[0]} | | | {defaults[5]}\n\n[사용할 수 있는 모델 목록]\n{', '.join(models.values())}\n\n[사용할 수 있는 샘플러 목록]\n{', '.join(samplers.keys())}\n\n[주의 및 참고 사항]\n* 선정적 / 19금 컨텐츠의 생성 제한이 따로 없고 스포일러 처리됩니다.\n하지만, 가끔 스포일러 처리되지 않을 수 있으니 사용에 유의하세요.\n\n* 그림을 요청한 메시지를 삭제하면, 봇의 응답(메시지/그림)도 삭제됩니다.\n\n* 태그(prompt), 모델, 샘플러 관련 정보는 아래 사이트에서 참고하세요.\n```https://civitai.com")

# 봇 그리기 명령어
@bot.command(name = 'draw', aliases = DRAW_CMDS)
async def draw(ctx, *, message):
  
    # dm 사용 불가
    if ctx.guild is None:
        await ctx.reply(f"```ini\n{BOT_HEADER}개인 메시지(DM)에서는 사용할 수 없습니다.```")
        return

    # 이미 사용중인 경우 사용 불가
    if ctx.guild.id in working_guilds:
        await ctx.reply(f"```ini\n{BOT_HEADER}해당 서버에서 이미 생성중인 그림이 있습니다. 나중에 다시 시도하세요.\n```")
        return

    # 이미지 생성 메인코드
    try:

        # 생성중인 서버에 추가
        working_guilds.append(ctx.guild.id)

        # 메시지 분리
        sub_cmds = message.split("|") if "|" in message else [message]

        # 메시지 파싱 및 기본값 적용
        parsed_values = [
            (sub_cmds[i].strip() if i < len(sub_cmds) and sub_cmds[i].strip() else defaults[i])
            for i in range(8)
        ]

        # 각 변수 할당
        prompt, ngprompt, model, width, height, sampler, scale, step = parsed_values

        # 모델 및 샘플러 검색 결과 없을 시 기본 값 선언
        ms_settings = []

        # 모델 검색
        if get_key_or_value(model, models):
            model = get_key_or_value(model, models)
        else:
            ms_settings.append("모델")

        # 샘플러 검색
        if get_key_or_value(sampler, samplers):
            sampler = get_key_or_value(sampler, samplers)
        else:
            ms_settings.append("샘플러")

        # 모델, 샘플러 검색 결과 없을 시 출력 문구
        if ms_settings:
            await ctx.reply(f"```ini\n{BOT_HEADER}해당 {', '.join(ms_settings)}의 검색결과가 없습니다.\n{', '.join(ms_settings)} 값은 기본 설정 값으로 그림을 그립니다.\n\n\n[사용할 수 있는 모델 목록]\n\n{', '.join(models.values())}\n\n\n[사용할 수 있는 샘플러 목록]\n\n{', '.join(samplers.keys())}\n```")

        # 영어가 아닐 경우 자동 번역 (요청태그)
        if any(char not in excluded_chars for char in prompt):          
            prompt = translate(prompt)

        # 영어가 아닐 경우 자동 번역 (거부태그)
        if any(char not in excluded_chars for char in ngprompt):         
            ngprompt = translate(ngprompt)   

        # 성능에 따른 과부하 방지를 위한 제한 항목 및 값 선언
        limit_settings = []

        # 너비 값 제한
        if int(width) > 800:
            width = 480
            limit_settings.append("너비")

        # 높이 값 제한
        if int(height) > 800:
            height = 640
            limit_settings.append("높이")

        # 스케일 값 제한
        if int(scale) > 10:
            scale = 7
            limit_settings.append("스케일")

        # 스텝 값 제한
        if int(step) > 30:
            step = 30
            limit_settings.append("스텝")

        # 제한 조건 감지 시 출력 문구
        if limit_settings:
            await ctx.reply(f"```ini\n{BOT_HEADER}AI 과부하 방지를 위해 {', '.join(limit_settings)} 최대값이 제한되었습니다.\n{', '.join(limit_settings)} 값은 기본 설정 값으로 그림을 그립니다.\n\n각각의 허용 범위는 아래를 참고하세요.\n\n너비 범위 : 0 ~ 800\n높이 범위 : 0 ~ 800\n스케일 범위 : 0 ~ 10\n스텝 범위 : 0 ~ 30\n```")

        # 요청 payload
        payload = {
            "prompt": prompt,
            "negative_prompt": f'(low resolution:1.3), (worst quality:1.3), (low quality:1.3), {ngprompt}',
            "width": width,
            "height": height,
            "sampler_index": sampler,
            "cfg_scale": scale,
            "steps": step
        }

        # 요청 option_payload
        option_payload = {
            "sd_model_checkpoint": model
        } 

        # 요청 상태 표출용 요청태그
        title = f"{prompt[:60]}..." if len(prompt) >= 40 else prompt

        # 요청 상태 표출용 거부태그
        ngtitle = f"{ngprompt[:60]}..." if len(ngprompt) >= 40 else ngprompt

        await ctx.reply(f"```ini\n{BOT_HEADER}아래 설정으로 그림을 그립니다.\n네트워크 상황에 따라 15초 이상 소요될 수 있습니다.\n\n<요청 태그> : {title}\n<제외 태그> : {ngtitle}\n<모델> : {model.split('_')[0].split('-')[0]}\n<이미지 사이즈> : {width}x{height}\n<샘플러> : {sampler}\n<스케일> : {scale}\n<스텝> : {step}\n\n[주의 및 참고 사항]\n* 선정적 / 19금 컨텐츠의 생성 제한이 따로 없고 스포일러 처리됩니다.\n하지만, 가끔 스포일러 처리되지 않을 수 있으니 사용에 유의하세요.\n\n* 그림을 요청한 메시지를 삭제하면, 봇의 응답(메시지/그림)도 삭제됩니다.\n\n* 기타 도움말은 명령어 {PREFIXS[0]}{HELP_CMDS[0]} 입력 시 표출됩니다.\n```")

        # 그림 생성
        async with aiohttp.ClientSession() as session:

            # 모델 변경
            option_response = await session.post(f"{STABLE_API_URL}/sdapi/v1/options", json = option_payload)

            # txt2img api 호출 및 생성
            async with session.post(f"{STABLE_API_URL}/sdapi/v1/txt2img", json = payload) as payload_response:
                r = await payload_response.json()

            # 이미지 PNG로 불러오기
            for i in r['images']:
                image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))
                png_payload = {"image": f"data:image/png;base64,{i}"}
                async with session.post(f"{STABLE_API_URL}/sdapi/v1/png-info", json = png_payload) as png_response:
                    pnginfo = PngImagePlugin.PngInfo()
                    pnginfo.add_text("parameters", (await png_response.json()).get("info"))
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format = 'PNG', pnginfo = pnginfo)
                img_byte_arr.seek(0)
                filename = f"{title}_output.png"

                # nsfw 컨텐츠는 스포일러 처리하여 사진 전송
                spoiler = any(keyword in prompt.lower() for keyword in spoiler_words)
                await ctx.reply(file = discord.File(img_byte_arr, filename = filename, spoiler = spoiler))

    # 오류 예외처리
    except Exception as e:

        # print(e)

        if "translations" in str(e):
            await ctx.reply(f"```ini\n{BOT_HEADER}번역 중 오류가 발생하였습니다.\n\n영어를 사용하거나, 나중에 다시 시도해주세요.\n```") 
        elif "invalid literal for int() with base 10" in str(e):
            await ctx.reply(f"```ini\n{BOT_HEADER}너비, 높이, 스케일, 스텝 값은 숫자만 입력할 수 있습니다.\n```") 
        else:
            await ctx.reply(f"```ini\n{BOT_HEADER}올바른 명령어 사용법을 확인해주세요.\n\n도움말 보기 : {PREFIXS[0]}{HELP_CMDS[0]}\n```")

    # 사용 종료
    finally:

        # 생성중인 서버에서 삭제
        working_guilds.remove(ctx.guild.id) 

# 디스코드 봇 실행
bot.run(TOKEN)
