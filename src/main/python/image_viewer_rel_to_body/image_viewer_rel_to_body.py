import glob
import random
from pathlib import Path

import oexp

this_file = Path(__file__)
import sys

sys.path.append(str(this_file.parent.parent))
import util
from mstuff.argparser import ArgParser
from mstuff.mstuff import error, read, load
from text import main_prompt

JUST_TRIM = True

this_file = Path(__file__)

parser = ArgParser("Script Options")
parser.flag("open", "open the experiment in Chrome")
parser.flag("print", "print the experiment URL")
parser.flag("hotcss", "css hot reloading", short="c")
parser.flag("analyze", "analyze data")
parser.int("manifest", "manifest number")

args = parser.parse_args()

auth_json = load(this_file.parent.parent.joinpath(".auth.json"))

user = oexp.login(auth_json["username"], auth_json["password"])
exp = user.experiment("image_viewer_rel_to_body")

if not args.analyze:

    hotcss = args.hotcss

    STYLE_FILE = this_file.parent.joinpath("image_viewer_rel_to_body.scss")

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
        choice_image_files = [
            choice_folder.joinpath(f) for f in glob.glob(str(choice_folder) + "/*.png")
        ]

        for c in choice_image_files:
            upload_session.upload_image_async_efficient(
                local_abs_path=str(c), remote_rel_path=c.name
            )

    manifests = []

    def create_manifest(yaws, pitches, seed):
        choices = [
            oexp.access.choice(
                value=c.name.replace(".png", ""),
                image=oexp.access.image(remote_path=c.name, one_shot=False),
                text=""
            )
            for c in choice_image_files
            if abs(util.yaw(c)) in yaws and abs(util.pitch(c)) in pitches
        ]
        choices = sorted(choices, key=util.custom_comparator)
        base_choices = choices.copy()
        choices = []
        i = 0
        first = True
        for b in base_choices:
            if first:
                first = False
            else:
                choices.append(
                    oexp.access.choice(value=f"...{i}", image=None, text="...")
                )
                i += 1
            choices.append(b)
        # choices.append(oexp.access.choice(value=f"...{i}", image=None, text="..."))
        rand = random.Random(seed)
        for m in range(1):
            trials = [
                oexp.access.prompt(
                    text=main_prompt(),
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
                    trials, css_vars={"box-length": str(len(yaws) * 4 - 2)}
                )
            )

    create_manifest(yaws=[0, 30, 60, 90], pitches=[0], seed=54235)

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
