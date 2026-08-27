[app]
title = NOVAX Agent
package.name = novaxagent
package.domain = org.novax

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3

version = 1.0

requirements = python3,kivy,pyjnius,requests,google-genai,speechrecognition,edge-tts

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,RECORD_AUDIO,CAMERA,FOREGROUND_SERVICE,WAKE_LOCK

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
