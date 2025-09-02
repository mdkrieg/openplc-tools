import requests
import time
from lxml import etree
from loguru import logger

parser = etree.HTMLParser()
session = requests.Session()

stfile_name = "logic.st" # for now, this file needs to be in the same directory as this script
url = "http://192.168.8.228:8080"
login_user = "openplc"
login_pass = "openplc"

login_url = f"{url}/login"
upload_program_url = f"{url}/upload-program"
upload_program_action_url = f"{url}/upload-program-action"
compile_program_url = f"{url}/compile-program"
compilation_logs_url = f"{url}/compilation-logs"

logger.info("STEP 1 - start off the session")
response = session.get(login_url)

logger.info("STEP 2 - log in")
login_payload = f"username={login_user}&password={login_pass}"
req = requests.Request(
    'POST',
    login_url,
    data=login_payload,
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    }
)
prepped = session.prepare_request(req)
response = session.send(prepped)

logger.info("STEP 3 - upload the file")
req = requests.Request(
    'POST',
    upload_program_url,
    files={
        "file": (stfile_name, open(stfile_name, "rb"), "application/octet-stream"),
        "submit": (None, "Upload Program")
    }
)

prepped = session.prepare_request(req)
response = session.send(prepped)
# debugging stuff I'm too traumatized to delete
# print(prepped.body.decode())
# with open("response.html","wb") as f:
#     f.write(response.content)

logger.info("STEP 4 - activate the uploaded program")
# have to read the response file to determine what the renamed .st file is
tree = etree.fromstring(response.content.decode("utf-8"),parser=parser)
el = tree.find(".//input[@id='prog_file']")
prog_file = el.attrib["value"]

req = requests.Request(
    'POST',
    upload_program_action_url,
    data={
        "prog_name": stfile_name.split(".")[0],
        "prog_descr": "",
        "prog_file": prog_file,
        "epoch_time": int(time.time())
    }
)
prepped = session.prepare_request(req)
response = session.send(prepped)

logger.info(f"STEP 5 - compile the uploaded program: {prog_file}")
response = session.get(
    compile_program_url,
    params={
        "file":prog_file
    }
)
logger.info(f"STEP 6 - poll the logs route to see status")
loglen = 0
while True:
    response = session.get(compilation_logs_url)
    log = response.content.decode("utf-8").splitlines()
    newlogs = log[loglen:]
    loglen = len(log)
    for ln in newlogs:
        logger.info("> " + ln)
    if log[-1].lower().startswith("compilation finished"): break
    time.sleep(1)

pass
