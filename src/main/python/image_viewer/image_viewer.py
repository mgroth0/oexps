import argparse
import glob
import random
from pathlib import Path

from text import main_prompt

import oexp
import util
from mstuff.mstuff import error, read, load

JUST_TRIM = True

this_file = Path(__file__)

parser = argparse.ArgumentParser(description="Open or print experiment URL")
parser.add_argument(
    "-o", "--open", action="store_true", help="open the experiment in Chrome"
)
parser.add_argument(
    "-p", "--print", action="store_true", help="print the experiment URL"
)
parser.add_argument("-c", "--hotcss", action="store_true", help="css hot reloading")
parser.add_argument("-a", "--analyze", action="store_true", help="analyze data")
parser.add_argument("-m", "--manifest", help="manifest number", type=int)

args = parser.parse_args()

auth_json = load(this_file.parent.parent.joinpath(".auth.json"))

user = oexp.login(auth_json["username"], auth_json["password"])
exp = user.experiment("image_viewer")

if not args.analyze:

    hotcss = args.hotcss

    STYLE_FILE = this_file.parent.joinpath("image_viewer.scss")

    if not JUST_TRIM:
        exp.delete_all_images()
    extract_root = Path(
        "/Users/matthewgroth/registered/data/BriarExtracts/BRS1_extract_for_oexp"
    )
    data_root = extract_root.joinpath("data")

    trials_json = extract_root.joinpath("trials.json")
    trials_json = load(trials_json)

    with exp.image_upload_session() as upload_session:
        for trial in trials_json:
            ims = [trial["query"], trial["queryGallery"]]
            for d in trial["distractors"]:
                ims.append(d)
            for im in ims:
                upload_session.upload_image_async_efficient(
                    local_abs_path=str(data_root.joinpath(im)), remote_rel_path=im
                )

        uploaded_images = exp.list_images()

        choice_folder = Path(
            "/Users/matthewgroth/registered/data/iarpa/facial_orientations/output"
        )
        choice_image_files = glob.glob(str(choice_folder) + "/*.png")

        choice_image_files = [choice_folder.joinpath(f) for f in choice_image_files]

        for c in choice_image_files:
            upload_session.upload_image_async_efficient(
                local_abs_path=str(c), remote_rel_path=c.name
            )

    manifests = []

    def create_manifest(yaws, pitches, seed):
        if len(pitches) != len(yaws):
            error("pitches and yaws must be same length")
        choices = [
            oexp.access.choice(
                show_text=False,
                value=c.name.replace(".png", ""),
                image=oexp.access.image(remote_path=c.name, one_shot=False),
            )
            for c in choice_image_files
            if abs(util.yaw(c)) in yaws and abs(util.pitch(c)) in pitches
        ]
        choices = sorted(choices, key=util.custom_comparator)
        choices.append(oexp.access.choice(value="None", image=None))
        rand = random.Random(seed)
        for m in range(1):
            trials = [
                oexp.access.prompt(
                    text=main_prompt(none_choice=choices[-1].value),
                    image=None,
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
                    choices=choices,
                )
                trials.append(trial)
            manifests.append(
                oexp.access.trial_manifest(
                    trials, css_vars={"box-length": str(len(yaws) * 2 - 1)}
                )
            )

    create_manifest(yaws=[0, 45, 90], pitches=[0, 15, 30], seed=99753)
    create_manifest(yaws=[0, 10, 45, 90], pitches=[0, 5, 15, 30], seed=756234)
    create_manifest(yaws=[0, 5, 10, 45, 90], pitches=[0, 5, 10, 25, 30], seed=8435)

    exp.manifests = manifests
    exp.scss = read(STYLE_FILE)

    # exp.link_prolific("64887b7cd8e3bc6a8ac0ebaa")

    if JUST_TRIM:
        exp.delete_unused_images()

    if args.print:
        print(
            "Sharable Experiment URL:",
            exp.session_url(hot_css=hotcss, man_num=args.manifest),
        )

    if args.open:
        exp.open(
            disable_auto_fullscreen=True,
            allow_fullscreen_exit=True,
            hot_css=hotcss,
            man_num=args.manifest,
        )

    if hotcss:
        exp.hot_css(str(STYLE_FILE))
else:
    if args.open or args.print or args.hotcss:
        error("cannot use these options with analyze")

    data = exp.subject_data()
    print(data.to_json())
