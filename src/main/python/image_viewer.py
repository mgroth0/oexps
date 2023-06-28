import argparse
import glob
import json
import random
from pathlib import Path

import oexp

print("NEED TO TRIM IMAGES")

parser = argparse.ArgumentParser(description='Open or print experiment URL')
# parser.add_argument('url', type=str, help='the experiment URL')
parser.add_argument('-o', '--open', action='store_true', help='open the experiment in Chrome')
parser.add_argument('-p', '--print', action='store_true', help='print the experiment URL')

args = parser.parse_args()

this_file = Path(__file__)

STYLE_FILE = this_file.parent.joinpath("image_viewer.css")

with open(this_file.parent.joinpath(".auth.json")) as f:
    auth_json = json.loads(f.read())

user = oexp.login(auth_json["username"], auth_json["password"])

exp = user.experiment("image_viewer")
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

choice_folder = Path("/Users/matthewgroth/registered/data/iarpa/facial_orientations/output")
choice_image_files = glob.glob(str(choice_folder) + "/*.png")
choice_image_files = [choice_folder.joinpath(f) for f in choice_image_files]

for c in choice_image_files:
    exp.upload_image(
        local_abs_path=str(c),
        remote_rel_path=c.name
    )

choices = [
    oexp.access.choice(value=c.name.replace(".png", ""), image=oexp.access.image(remote_path=c.name, one_shot=False))
    for
    c in choice_image_files]
choices.append(oexp.access.choice(value="None", image=None))

rand = random.Random(99753)
manifests = []
for m in range(20):
    trials = [
        oexp.access.prompt(
            text=f"""
Welcome to the Image Viewer.

We want annotate the direction that the people in these images are facing.

You will be presented with an image of a person and asked to tell which direction they are facing.

Please select the option that has the most similar to the image. If none are similar, select "{choices[-1].value}".

Press SPACEBAR to start
  """.strip(),
            image=None
        )
    ]
    trials_json_copy = trials_json.copy()
    all_ims = []

    for t in trials_json_copy:
        all_ims.append(t["query"])
        all_ims.append(t["queryGallery"])
        for d in t["distractors"]:
            all_ims.append(d)
    rand.shuffle(all_ims)
    for an_im in all_ims:
        trial = oexp.access.choice_trial(
            image=oexp.access.image(remote_path=an_im, one_shot=True),
            choices=choices
        )
        trials.append(trial)
    manifests.append(oexp.access.trial_manifest(trials))
exp.manifests = manifests
with open(STYLE_FILE) as f:
    exp.css = f.read()

# exp.link_prolific("64887b7cd8e3bc6a8ac0ebaa")

if args.print:
    print("Sharable Experiment URL:", exp.session_url())

if args.open:
    exp.open(disable_auto_fullscreen=True, allow_fullscreen_exit=True)

args = parser.parse_args()
