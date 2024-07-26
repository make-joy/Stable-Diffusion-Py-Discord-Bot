# Stable-Diffusion-Py-Discord-Bot

stable diffusion 디스코드 그림봇

# 주요기능

1. 한글 명령어 지원 및 영한타 오타를 지원 (그림, rmfla 등)
2. 요청태그(prompt), 거부태그(ng_prompt) 입력 시, 영어가 아니라면 영어로 자동 번역
3. 요청태그, 거부태그, 모델, 너비, 높이, 샘플러, 스케일, 스텝을 구분자 | 로 세부적인 그림 생성 가능
4. nsfw 관련 키워드 포함시 자동으로 스포일러 처리
5. 요청 메시지(명령어) 삭제 시, 봇 메시지도 삭제 처리

## **봇 설치 및 사용법**

**1.** Stable Diffusion WebUi 설치 [바로가기](https://github.com/AUTOMATIC1111/stable-diffusion-webui)

**2.** 이 저장소의 모든 파일을 Stable Diffusion WebUi 설치 폴더 내부로 이동

**3.** 같은 폴더에 **`.env예시`** 파일을 참조하여 **`.env`** 파일 생성 후 정보 입력 

### _.env 파일 예시

```env
TOKEN: 디스코드봇 토큰
PREFIXS: /,+,.,?,!
HELP_CMDS: 그림봇,drawbot,도움말,rmflaqht,ehdnaakf
DRAW_CMDS: 그림,그리기,rmfla,rmflrl
BOT_NAME: MJ Draw Bot
TRANSLATE_API_URL: deepLX 번역 API URL
STABLE_API_URL: http://127.0.0.1:7860
```

**4.** Stable Diffusion WebUi 실행 시 봇 파일도 바로 실행을 위해 Webui.bat 파일 수정<br/>
```shell

```

## 라이센스

[CC BY-NC](https://creativecommons.org/licenses/by-nc/2.0)
