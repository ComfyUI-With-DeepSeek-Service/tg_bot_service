# Telegram bot service

Телеграм бот для общения с локально поднятым DeepSeek и StableDiffusion (ComfyUI)

### CMD
`pyenv install 3.12.4` \
`pyenv local 3.12.4` \
`poetry env use python` \
`poetry shell` \
`python main.py`

### Docker

``` commandline
docker build --progress=plain  -t tg_bot_service . && \
docker run -it  -p 8000:8000 tg_bot_service
```
