[app]
title = LioApp
package.name = lioapplimpieza
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# 1. Agregamos las dependencias base esenciales para el entorno
requirements = python3,kivy,sqlite3,fpdf2,setuptools

# 2. Le avisamos a Android que fpdf2 es una libreria pura de Python
android.pip_dependencies = fpdf2

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.skip_update = False
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
