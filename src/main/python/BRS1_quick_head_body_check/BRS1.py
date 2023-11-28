
# purpose of this is a quick demo. It is similar to BRS1. The main difference is that I copied the dataset and manually edited the first 3 query iamges to show full, head, and body. This experiment does not shuffle trial order so the first 3 trials can work as a demo

import json
import random
from pathlib import Path

import oexp
from mstuff.argparser import ArgParser

parser = ArgParser("Open or print experiment URL")
parser.flag("open", "open the experiment in Chrome")
parser.flag("print", "print the experiment URL")
parser.str("lab_key", "lab key to allow testing without PID")

args = parser.parse_args()

this_file = Path(__file__)

STYLE_FILE = this_file.parent.joinpath("BRS1.scss")

with open(this_file.parent.parent.joinpath(".auth.json")) as f:
    auth_json = json.loads(f.read())

user = oexp.login(auth_json["username"], auth_json["password"])

exp = user.experiment("BRS1_quick_head_body_check")
exp.delete_all_images()

extract_root = Path(
    "/Users/matthewgroth/registered/data/BriarExtracts/BRS1_extract_for_oexp_quick_manual_copy_edit"
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
            image=oexp.access.image(
                remote_path="Example_Online_BRIAR_1.jpg", one_shot=False
            ),
        ),
        oexp.access.prompt(
            text="""
Once you have ranked your top three images, you can continue to the next trial (click blue button).
If you want to change your choices - click the red reset button.

Press SPACEBAR to start the experiment.
	  """.strip(),
            image=oexp.access.image(
                remote_path="Example_Online_BRIAR_2.jpg", one_shot=False
            ),
        ),
    ]
    trials_json_copy = trials_json.copy()
    # rand.shuffle(trials_json_copy) # dont shuffle, since I manually edited the top 3 trials
    for t in trials_json_copy:
        distractors = [

            oexp.access.image(

                remote_path=t["queryGallery"],

                one_shot=True
            )

            , *[oexp.access.image(

                remote_path=im,

                one_shot=True
            )  for im in  t["distractors"]]]
        rand.shuffle(distractors)
        query_image = oexp.access.image(

            remote_path=t["query"],

            one_shot=True
        )
        trial = oexp.access.gallery_trial(query= query_image, distractors=distractors)
        trials.append(trial)
    manifests.append(oexp.access.trial_manifest(trials))
exp.manifests = manifests
with open(STYLE_FILE, "r") as f:
    exp.scss = f.read()

# exp.link_prolific("64887b7cd8e3bc6a8ac0ebaa")

if args.print:
    print("Sharable Experiment URL:", exp.session_url(disable_auto_fullscreen=True, allow_fullscreen_exit=True,lab_key=args.lab_key,))

if args.open:
    exp.open(disable_auto_fullscreen=True, allow_fullscreen_exit=True,lab_key=args.lab_key,)

args = parser.parse_args()
