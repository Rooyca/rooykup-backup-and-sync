import zipfile
import os, stat, argparse
import datetime, time

from colors import *
from config import *

today = datetime.date.today()

# Parsing arguments
parser = argparse.ArgumentParser(description='rooykup lets you backup and sync your data')
parser.add_argument('-s', '--shutdown', dest='shutdown', action='store_true', help='Shutdown after script is done')
parser.add_argument('-c', '--allways-create-zip', dest='allways_create_zip', action='store_true', help='Create zip even if it already exists')
parser.set_defaults(shutdown=SHUTDOWN_AFTER, allways_create_zip=ALLWAYS_CREATE_ZIP)
args = parser.parse_args()

if args.allways_create_zip:
	ALLWAYS_CREATE_ZIP = not ALLWAYS_CREATE_ZIP

if args.shutdown:
	SHUTDOWN_AFTER = not SHUTDOWN_AFTER

"""
Functions

"""

def get_size(start_path):
	total_size = 0
	for dirpath, dirnames, filenames in os.walk(start_path):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			total_size += os.path.getsize(fp)
	return total_size

def check_if_file_was_created_today(file_path):
  stat_info = os.stat(file_path)
  creation_time = stat_info.st_ctime
  return datetime.datetime.fromtimestamp(creation_time).date() == today

# Start timer
started = time.time()

# Load exclude directories
exclude = toml_data['exclude']['directories']

for p in toml_data['pathAndDirName']:
	size_initial = get_size(p['path'])

	# Check if directory is enty or not found
	if size_initial == 0:
		string_to_log = f"- [ ] {p['zipName']} (0MB) - Directory empty or not found"
		print(string_to_log[:string_to_log.find("-")]+RED+string_to_log[string_to_log.find("-"):]+RESET_ALL)
		with open(f"logs/log-{str(today)}.md", 'a') as f:
			f.write(string_to_log+"\n")
		continue

	# Size of directory
	size_inital_mb = size_initial/(1024*1024)
	source_dir = p['path']
	zipName = p['zipName']+".zip"

	if not ALLWAYS_CREATE_ZIP:
		is_file = "compressed/" + zipName
		if os.path.isfile(is_file):
			if check_if_file_was_created_today(is_file):
				print(f"- [x] {zipName} "+GREEN+"(Already created today)"+RESET_ALL)
				#with open(f"logs/log-{str(today)}.md", 'a') as f:
				#	f.write(f"- [x] {zipName} (Already created today)\n")
				continue

	archive = zipfile.ZipFile("compressed/"+zipName, "w")

	for root, dirs, files in os.walk(source_dir):
		dirs[:] = [d for d in dirs if d not in exclude]
		for file in files:
			try:
				archive.write(os.path.join(root, file))
			except:
				print(RED+"[-] Error: "+RESET_ALL+" Something went wrong with: "+file+"at "+root+" (Skipping)")
				continue
	archive.close()

	# Size of ZIP
	size_final = os.path.getsize("compressed/"+zipName)/(1024*1024)
	out_str = f"- [x] {zipName} ({size_inital_mb:.1f}MB => {size_final:.1f}MB)"

	print(out_str[:out_str.find("(")]+GREEN+out_str[out_str.find("("):]+RESET_ALL)

	with open(f"logs/log-{str(today)}.md", 'a') as f:
		f.write(out_str+"\n")

print("-"*30)

path_compressed = os.getcwd() + "/compressed"

try:
	remote = toml_data['config']['remote']
	local = toml_data['config']['local']
except:
	print(RED+"[-] Error"+RESET_ALL+" - add 'remote' and 'local' to config file")
	exit()

try:
	config_pass = os.environ['RCLONE_CONFIG_PASS']
	for r in remote:
		os.system(f"echo {config_pass} | rclone copy {local+path_compressed} {r} -P")
		print(GREEN+"[+] "+RESET_ALL+"Uploaded to "+r)

except:
	print(RED+"Uploading error..."+RESET_ALL)

# End timer
ended = time.time()

time_elapsed = ended-started
time_var = "seconds"

if time_elapsed > 60:
	time_elapsed = time_elapsed/60
	time_var = "minutes"

print("-"*30)
print(BLUE+" ==> "+f"Total time elapsed: {time_elapsed:.2f} {time_var}"+RESET_ALL)

with open(f"logs/log-{str(today)}.md", 'a') as f:
	f.write("\n")
	f.write("----\n")
	f.write(f"## Time elapsed: {time_elapsed:.2f} {time_var}\n")

print("-"*30)

if SHUTDOWN_AFTER:
	os.system("shutdown now")
