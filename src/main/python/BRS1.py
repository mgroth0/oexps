import json
from pathlib import Path
import oexp
import argparse

parser = argparse.ArgumentParser(description='Open or print experiment URL')
# parser.add_argument('url', type=str, help='the experiment URL')
parser.add_argument('-o', '--open', action='store_true', help='open the experiment in Chrome')
parser.add_argument('-p', '--print', action='store_true', help='print the experiment URL')

args = parser.parse_args()

this_file = Path(__file__)

STYLE_FILE = this_file.parent.joinpath("BRS1.css")

with open(this_file.parent.joinpath(".auth.json")) as f:
    auth_json = json.loads(f.read())

user = oexp.login(auth_json["username"], auth_json["password"])

exp = user.experiment("BRS1")
exp.delete_all_images()
ims = exp.upload_images("/Users/matthewgroth/registered/bolt/oexp_demo/images")
uploaded_images = exp.list_images()
import random

manifests = []
for m in range(20):
    trials = []
    for t in range(15):
        trial = oexp.access.trial(
            query=random.choice(uploaded_images),
            distractors=[random.choice(uploaded_images) for i in range(5)]
        )
        trials.append(trial)
    manifests.append(oexp.access.trial_manifest(trials))
exp.manifests = manifests
with open(STYLE_FILE, "r") as f:
    exp.css = f.read()


if args.print:
    print("Experiment URL:", exp.session_url())

if args.open:
    exp.open()


args = parser.parse_args()






