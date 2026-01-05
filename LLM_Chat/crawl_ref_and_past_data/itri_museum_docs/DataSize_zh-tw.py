導入操作系統
文件夾='/mnt/hdd2/he110/linly-talker/llm_chat/itri_museum_docs'
total_data = 0
total_json = 0
total_txt = 0
對於root，dirs，在OS.Walk（文件夾）中的文件：
對於文件中的f：
如果F.Endswith（'。txt'）：
total_txt += os.path.getSize（os.path.join（root，f））
Elif F.Endswith（'。json'）：
total_json += os.path.getSize（os.path.join（root，f））
total_data = total_json + total_txt

打印（f'[*]總數.json大小：{total_json/1024/1024：.2f} MB'）
打印（f'[*]總數.txt大小：{total_txt/1024/1024：.2f} mb'）
打印（f' - 總尺寸：{total_data/1024/1024：.2f} mb'）