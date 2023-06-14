import json
import random
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

extract_root = Path("/Users/matthewgroth/registered/data/BriarExtracts/BRS1_extract_for_oexp")
data_root = extract_root.joinpath("data")

trials_json = extract_root.joinpath("trials.json")
with open(trials_json) as f:
    trials_json = json.load(f)

for trial in trials_json:

    ims = []
    ims.append(trial["query"])
    ims.append(trial["queryGallery"])
    for d in trial["distractors"]:
        ims.append(d)
    for im in ims:
        exp.upload_image(
            local_abs_path=str(data_root.joinpath(im)),
            remote_rel_path=im
        )


uploaded_images = exp.list_images()
exists = []
does_not_exist = []
for u in uploaded_images:
    local_im_file = data_root.joinpath(u)
    if local_im_file.exists():
        exists.append(local_im_file)
    else:
        does_not_exist.append(local_im_file)



rand = random.Random(23084)
manifests = []
for m in range(20):
    trials = []
    trials_json_copy = trials_json.copy()
    rand.shuffle(trials_json_copy)
    for t in trials_json_copy:
        distractors = [t["queryGallery"], *t["distractors"]]
        rand.shuffle(distractors)
        trial = oexp.access.trial(
            query=t["query"],
            distractors=distractors
        )
        trials.append(trial)
    manifests.append(oexp.access.trial_manifest(trials))
exp.manifests = manifests
with open(STYLE_FILE, "r") as f:
    exp.css = f.read()


exp.link_prolific("64887b7cd8e3bc6a8ac0ebaa")

if args.print:
    print("Sharable Experiment URL:", exp.session_url())

if args.open:
    exp.open(disable_auto_fullscreen=True, allow_fullscreen_exit=True)

args = parser.parse_args()

