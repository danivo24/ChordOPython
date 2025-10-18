from PyInstaller.utils.hooks import collect_all

# coleta todos os arquivos, binários e imports do pacote just_playback
datas, binaries, hiddenimports = collect_all('just_playback')
