import json
import random
from pathlib import Path

import oexp
from mstuff.argparser import ArgParser

parser = ArgParser("Open or print experiment URL")
parser.flag("open", "open the experiment in Chrome")
parser.flag("print", "print the experiment URL")

args = parser.parse_args()

this_file = Path(__file__)

STYLE_FILE = this_file.parent.joinpath("BRS1.css")

with open(this_file.parent.parent.joinpath(".auth.json")) as f:
    auth_json = json.loads(f.read())

user = oexp.login(auth_json["username"], auth_json["password"])

exp = user.experiment("BRS1")
exp.delete_all_images()

extract_root = Path(
    "/Users/matthewgroth/registered/data/BriarExtracts/BRS1_extract_for_oexp"
)
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
        exp.upload_image(local_abs_path=str(data_root.joinpath(im)), remote_rel_path=im)

exp.upload_image(
    local_abs_path="/Users/matthewgroth/registered/ide/all/k/iarpa/src/jvmTest/resources/Example_Online_BRIAR_1.jpg",
    remote_rel_path="Example_Online_BRIAR_1.jpg",
)
exp.upload_image(
    local_abs_path="/Users/matthewgroth/registered/ide/all/k/iarpa/src/jvmTest/resources/Example_Online_BRIAR_2.jpg",
    remote_rel_path="Example_Online_BRIAR_2.jpg",
)

rand = random.Random(23084)
manifests = []
for m in range(20):
    trials = [
        oexp.access.prompt(
            text="""
Welcome to the Face Identification experiment.

We want to learn about face identification across different distances and different face orientations.

You will be presented with an image of a face at the top of the screen and asked to compare it with five other face images at the bottom of the screen.

Press SPACEBAR to see an example.
  """.strip(),
            image=None,
        ),
        oexp.access.prompt(
            text="""
By clicking on the images in the bottom row, you will indicate which are the top three most similar identities to the identity at the top.

Press SPACEBAR to continue example.
	  """.strip(),
            image="Example_Online_BRIAR_1.jpg",
        ),
        oexp.access.prompt(
            text="""
Once you have ranked your top three images, you can continue to the next trial (click blue button).
If you want to change your choices - click the red reset button.

Press SPACEBAR to start the experiment.
	  """.strip(),
            image="Example_Online_BRIAR_2.jpg",
        ),
    ]
    trials_json_copy = trials_json.copy()
    rand.shuffle(trials_json_copy)
    for t in trials_json_copy:
        distractors = [t["queryGallery"], *t["distractors"]]
        rand.shuffle(distractors)
        trial = oexp.access.trial(query=t["query"], distractors=distractors)
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
