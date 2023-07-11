import argparse
import glob
import json
import random
import subprocess
import sys
from pathlib import Path

JUST_TRIM = True

parser = argparse.ArgumentParser(description='Open or print experiment URL')
# parser.add_argument('url', type=str, help='the experiment URL')
parser.add_argument('-o', '--open', action='store_true', help='open the experiment in Chrome')
parser.add_argument('-p', '--print', action='store_true', help='print the experiment URL')
parser.add_argument('-l', '--local', action='store_true', help='use development version of oexp client')
parser.add_argument('-c', '--hotcss', action='store_true', help='css hot reloading')

args = parser.parse_args()

hotcss = args.hotcss

this_file = Path(__file__)
if args.local:
    subprocess.run(
        args=["/Users/matthewgroth/registered/ide/all/gradlew", ":k:oexp:oexpGenSources"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        cwd="/Users/matthewgroth/registered/ide/all/",
        check=True
    )
    sys.path.insert(0,
                    str(this_file.parent.parent.parent.parent.parent.parent.joinpath("src").joinpath("main").joinpath(
                        "python")))
    import oexp
    import oexp.jbridge

    oexp.jbridge.LOCAL_JAR = "/Users/matthewgroth/registered/ide/all/k/oexp/front/build/libs/oexp-front-0-all.jar"
else:
    import oexp

STYLE_FILE = this_file.parent.joinpath("image_viewer.css")

with open(this_file.parent.parent.joinpath(".auth.json")) as f:
    auth_json = json.loads(f.read())

user = oexp.login(auth_json["username"], auth_json["password"])

exp = user.experiment("image_viewer")
if not JUST_TRIM:
    exp.delete_all_images()
extract_root = Path("/Users/matthewgroth/registered/data/BriarExtracts/BRS1_extract_for_oexp")
data_root = extract_root.joinpath("data")

trials_json = extract_root.joinpath("trials.json")
with open(trials_json) as f:
    trials_json = json.load(f)

with exp.image_upload_session() as upload_session:
    for trial in trials_json:
        ims = []
        ims.append(trial["query"])
        ims.append(trial["queryGallery"])
        for d in trial["distractors"]:
            ims.append(d)
        for im in ims:
            upload_session.upload_image_async_efficient(
                local_abs_path=str(data_root.joinpath(im)),
                remote_rel_path=im
            )

    uploaded_images = exp.list_images()

    choice_folder = Path("/Users/matthewgroth/registered/data/iarpa/facial_orientations/output")
    choice_image_files = glob.glob(str(choice_folder) + "/*.png")
    choice_image_files = [choice_folder.joinpath(f) for f in choice_image_files]

    for c in choice_image_files:
        upload_session.upload_image_async_efficient(
            local_abs_path=str(c),
            remote_rel_path=c.name
        )

choices = [
    oexp.access.choice(show_text=False, value=c.name.replace(".png", ""),
                       image=oexp.access.image(remote_path=c.name, one_shot=False))
    for
    c in choice_image_files]


def custom_comparator(item: oexp.access.Choice):
    value = item.value
    r = 0

    up = "U" in value
    left = "R" in value
    yaw = int(value[1:3])
    pitch = int(value[4:])

    p_value = pitch * 1000
    if up: p_value *= -1
    y_value = yaw
    if left: y_value *= -1
    return p_value + y_value



choices = sorted(choices, key=custom_comparator)

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

if JUST_TRIM:
    exp.delete_unused_images()

if args.print:
    print("Sharable Experiment URL:", exp.session_url(hot_css=hotcss))

if args.open:
    exp.open(disable_auto_fullscreen=True, allow_fullscreen_exit=True, hot_css=hotcss)

if (hotcss):
    exp.hot_css(str(STYLE_FILE))
