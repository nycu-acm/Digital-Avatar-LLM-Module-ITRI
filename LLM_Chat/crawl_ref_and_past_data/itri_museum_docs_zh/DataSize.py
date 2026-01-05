import os
folder = '/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs'
total_data = 0
total_json = 0
total_txt  = 0
for root, dirs, files in os.walk(folder):
    for f in files:
        if f.endswith('.txt'):
            total_txt += os.path.getsize(os.path.join(root, f))
        elif f.endswith('.json'):
            total_json += os.path.getsize(os.path.join(root, f))
total_data = total_json + total_txt

print(f'[*] Total .json size: {total_json/1024/1024:.2f} MB')
print(f'[*] Total .txt size: {total_txt/1024/1024:.2f} MB')
print(f' - Total size: {total_data/1024/1024:.2f} MB')
