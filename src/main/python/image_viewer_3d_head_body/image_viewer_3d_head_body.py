raise Exception("this has been rewritten in kotlin")
import random
from pathlib import Path

import oexp

this_file = Path(__file__)
import sys

sys.path.append(str(this_file.parent.parent))

from mstuff.argparser import ArgParser
from mstuff.mstuff import error, read, load
from text import main_prompt, review_instructions_prompt
import cbor2

JUST_TRIM = True


parser = ArgParser("Script Options")
parser.flag("open", "open the experiment in Chrome")
parser.flag("print", "print the experiment URL")
parser.flag("hotcss", "css hot reloading", short="c")
parser.flag("analyze", "analyze data")
parser.int("manifest", "manifest number")
parser.flag("demographics", "open with the demographics form")
parser.str("lab_key", "lab key to allow testing without PID")
parser.flag("test", "include a minimum number of trials to demo the experiment")

args = parser.parse_args()

auth_json = load(this_file.parent.parent.joinpath(".auth.json"))

user = oexp.login(auth_json["username"], auth_json["password"])
exp = user.experiment("image_viewer_3d_head_body")

# EXTRACT_NAME = "BRS1_extract_for_oexp"
# EXTRACT_NAME = "bts1_full_extract_for_annotations_1"
EXTRACT_NAME = "brs1_null_quick_check_1"

if not args.analyze:

    hotcss = args.hotcss

    STYLE_FILE = this_file.parent.joinpath("image_viewer_3d_head_body.scss")

    if not JUST_TRIM:
        exp.delete_all_images()
    extract_root = Path(
        f"/Users/matthewgroth/registered/data/BriarExtracts/{EXTRACT_NAME}"
    )

    metadata_minimal_cbor = extract_root.joinpath("metadata_minimal.cbor")
    with open(metadata_minimal_cbor, "rb") as f:

        metadata_minimal_cbor = cbor2.load(f)

    example_prompts = [
        oexp.access.prompt(
            text="In the beginning of a trial you will see an image of a person (left) and a 3D body",
            image=oexp.access.image(
                remote_path="example_images/not_frontal_body.png", one_shot=False
            ),
        ),
        oexp.access.prompt(
            text="You will use your mouse to adjust the orientation of the 3D body (by moving it side to side) until you believe it closely matches the orientation of the body of the person in the image on the left.",
            image=oexp.access.image(
                remote_path="example_images/body_aligned.png", one_shot=False
            ),
        ),
        oexp.access.prompt(
            text="After you confirmed your choice of orientation for the 3D body (by pressing the spacebar), you will see the same image of a person (left), but on the right there will be a 3D head",
            image=oexp.access.image(
                remote_path="example_images/not_frontal.png", one_shot=False
            ),
        ),
        oexp.access.prompt(
            text="You will use your mouse to adjust the orientation of the 3D head (by moving it side to side and up and down) until you believe it closely matches the orientation of the head of the person in the image on the left. Please remember that while the body can only rotate in the side-to-side axis, the head also should be aligned in the up-and-down axis as well.",
            image=oexp.access.image(
                remote_path="example_images/head_aligned.png", one_shot=False
            ),
        ),
        oexp.access.prompt(
            text="After you confirmed your choice of orientation for the 3D head (by pressing the spacebar), a new trial will appear!",
            image=oexp.access.image(
                remote_path="example_images/new_trial.png", one_shot=False
            ),
        ),
    ]

    ims = []

    with exp.image_upload_session() as upload_session:
        for media_list in metadata_minimal_cbor["media"]:
            framesMetaDataFile = media_list["framesMetaDataFile"]
            if framesMetaDataFile is not None:
                frames_json = load(framesMetaDataFile)
                for frame in frames_json["frames"]:
                    frame_index = frame["index"]
                    frame_image_file = (
                        framesMetaDataFile[: framesMetaDataFile.rfind(".")]
                        + "/"
                        + str(frame_index)
                        + ".png"
                    )
                    rel_path = frame_image_file.replace(str(extract_root) + "/", "")
                    ims.append(rel_path)
                    upload_session.upload_image_async_efficient(
                        local_abs_path=frame_image_file,
                        remote_rel_path=rel_path,
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

        for ex in example_prompts:
            upload_session.upload_image_async_efficient(
                local_abs_path=str(this_file.parent.joinpath(ex.image.remote_path)),
                remote_rel_path=ex.image.remote_path,
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

    if args.test:
        ims = ims[:2]

    def create_manifest(yaws, pitches, seed):
        global ims
        if len(pitches) != len(yaws):
            error("pitches and yaws must be same length")

        rand = random.Random(seed)
        for m in range(1):
            trials = [
                oexp.access.prompt(
                    text=main_prompt(),
                    image=None,
                ),
                *example_prompts,
                oexp.access.prompt(
                    text=review_instructions_prompt(),
                    image=None,
                ),
            ]

            rand.shuffle(ims)
            for an_im in ims:

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

    exp.link_prolific("654a92de37939974ff0b579a")

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
