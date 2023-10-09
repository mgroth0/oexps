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


parser = ArgParser("Script Options")
parser.flag("open", "open the experiment in Chrome")
parser.flag("print", "print the experiment URL")
parser.flag("hotcss", "css hot reloading", short="c")
parser.flag("analyze", "analyze data")
parser.int("manifest", "manifest number")
parser.flag("demographics", "open with the demographics form")
parser.str("lab_key", "lab key to allow testing without PID")

args = parser.parse_args()

auth_json = load(this_file.parent.parent.joinpath(".auth.json"))

user = oexp.login(auth_json["username"], auth_json["password"])
exp = user.experiment("image_viewer_3d_head_body")

if not args.analyze:

    hotcss = args.hotcss

    STYLE_FILE = this_file.parent.joinpath("image_viewer_3d_head_body.scss")

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

        upload_session.upload_image_async_efficient(
            local_abs_path="/Users/matthewgroth/registered/data/iarpa/facial_orientations/input/BustBaseMesh_Obj/BustBaseMesh_Decimated.obj",
            remote_rel_path="BustBaseMesh_Decimated.obj",
        )

        upload_session.upload_image_async_efficient(
            local_abs_path="/Users/matthewgroth/registered/data/iarpa/body_orientations/input/lowPolyMan1.obj",
            remote_rel_path="lowPolyMan1.obj",
        )

    manifests = []

    the_face_orient = oexp.access.orient(
        image=oexp.access.image(
            remote_path="BustBaseMesh_Decimated.obj", one_shot=False
        )
    )
    the_body_orient = oexp.access.orient(
        image=oexp.access.image(remote_path="lowPolyMan1.obj", one_shot=False),
        offsets=oexp.access.xyz(x=0.0, y=-0.6, z=-1.0),
        # offsets=oexp.access.xyz(x=0.0, y=-0.6, z=-0.0),
        rotate_pitch=False,
    )

    def create_manifest(yaws, pitches, seed):
        if len(pitches) != len(yaws):
            error("pitches and yaws must be same length")

        rand = random.Random(seed)
        for m in range(1):
            trials = [
                oexp.access.prompt(
                    text="insert 3d head(+body) prompt here",
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

                body_trial = oexp.access.orient_trial(
                    image=oexp.access.image(remote_path=an_im, one_shot=True),
                    orient=the_body_orient,
                )
                trials.append(body_trial)

                face_trial = oexp.access.orient_trial(
                    image=oexp.access.image(remote_path=an_im, one_shot=True),
                    orient=the_face_orient,
                )
                trials.append(face_trial)

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
            exp.session_url(
                disable_auto_fullscreen=True,
                allow_fullscreen_exit=True,
                hot_css=hotcss,
                man_num=args.manifest,
                demographics=args.demographics,
                lab_key=args.lab_key,
            ),
        )

    if args.open:
        exp.open(
            disable_auto_fullscreen=True,
            allow_fullscreen_exit=True,
            hot_css=hotcss,
            man_num=args.manifest,
            demographics=args.demographics,
            lab_key=args.lab_key,
        )

    if hotcss:
        exp.hot_css(str(STYLE_FILE))
else:
    if args.open or args.print or args.hotcss:
        error("cannot use these options with analyze")

    data = exp.subject_data()
    print(data.to_json())
