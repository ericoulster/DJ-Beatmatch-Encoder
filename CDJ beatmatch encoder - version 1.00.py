import re
import os

# main regex pattern
re_pat = re.compile('\s-\s\d{2,3}\.')

# current BPM
base_bpm = 130


# current directory
dj_directory = r'C:\Users\Ewic\Desktop\5 Track Stall'
os.chdir(dj_directory)

#initializing lists
namelist_process = []
bpm_list = []
beatmatch = []
preprocess_namelist = []
result_list = []


# bpm function for converting a raw BPM into a percentage difference from the DJ set's BPM
def interval_calculation(track_bpm, base_bpm):
    if base_bpm == track_bpm:
        calculation = 0
    elif base_bpm > track_bpm:
        calculation = ("+" + str(round((
            ((base_bpm - track_bpm)/track_bpm) * 100), 2))
                       )
    else:
        calculation = ("-" + str(round(
            (((track_bpm - base_bpm)/track_bpm) * 100), 2))
                       )
    return calculation
    
# Takes the list of names and the list of BPM % differences and combines them
def naming_function(name_list, beatmatch_list):
    final_name = (name_list[:3] + "(" + beatmatch_list + ")" + name_list[3:])
    return final_name


# this opens the directory, scans it, extracts BPM info, then converts them into percentages.
with os.scandir(dj_directory) as it:
    for entry in it:
        if re_pat.search(entry.name) is not None and entry.is_file():
            preprocess_namelist.append(entry.name)
            namelist_process.append(re_pat.search(entry.name).group())
    for i in namelist_process:
        bpm_list.append(float(re.search('\d{2,3}', i).group()))
    for j in bpm_list:
        beatmatch.append(interval_calculation(track_bpm=j, base_bpm=base_bpm))
    for preprocess_namelist, beatmatch in zip(preprocess_namelist, beatmatch):
        result = naming_function(preprocess_namelist, beatmatch)
        result_list.append(result)




# renames files in directory, and disqualifies ones without the adequate BPM info for renaming

with os.scandir(dj_directory) as it:
    for entry, result in zip(it, result_list):
        if re_pat.search(entry.name) is not None and entry.is_file():
            os.rename(os.path.join(dj_directory, entry.name), os.path.join(dj_directory, result))

print(result_list)

"""
for entry in os.scandir(dj_directory):
    if re_pat.search(entry.name) is not None and entry.is_file():
        for result in result_list:
            os.rename(os.path.join(dj_directory, entry.name), os.path.join(dj_directory, result))
# other attempt

def name_encoder(i, newname):
        os.rename(
            os.path.join(dj_directory, i.name),
            os.path.join(dj_directory, newname)
            )
"""

# notes: current version doesn't support 'irregular' characters
