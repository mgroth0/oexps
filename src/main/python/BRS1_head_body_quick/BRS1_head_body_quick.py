from __future__ import annotations
import dataclasses
import itertools
from typing import List, Optional


import PIL
from PIL import Image


FINAL_CONDITION = "_ar"
conditions = ["_ar_bo", "_ar_ho", FINAL_CONDITION]
distances = [5, 100, 200, 500]


IDS_PER_SUBJECT = 27  # that is the number of IDs in the CSV Michal sent, even though originally we expected 30
# ID_DISTS_PER_SUBJECT = IDS_PER_SUBJECT * len(distances)
TRIALS_PER_SUBJECT = IDS_PER_SUBJECT * len(conditions)

NUM_PARTICIPANTS = 80

import json
import os
import random
from pathlib import Path

import oexp
from mstuff.argparser import ArgParser

parser = ArgParser("Open or print experiment URL")
parser.flag("open", "open the experiment in Chrome")
parser.flag("print", "print the experiment URL")
parser.str("lab_key", "lab key to allow testing without PID")
parser.flag("hotcss", "css hot reloading", short="c")

args = parser.parse_args()

hotcss = args.hotcss

this_file = Path(__file__)

STYLE_FILE = this_file.parent.joinpath("BRS1_head_body_quick.scss")

with open(this_file.parent.parent.joinpath(".auth.json")) as f:
    auth_json = json.loads(f.read())

user = oexp.login(auth_json["username"], auth_json["password"])

exp = user.experiment("BRS1_head_body_quick")
# exp.delete_all_images()


extract_root = Path(
    "/Users/matthewgroth/registered/data/iarpa/ManuallyAlteredExtracts/Final_images_WB_BRS1_pilot_Oct2023/ExtractRoot"
)
data_root = extract_root.joinpath("data")

subject_matchings = extract_root.joinpath(
    "fixed_Final_QuerryGalleryIDs_WB_BRS1_pilot.csv"
)
with open(subject_matchings) as f:
    subject_matchings = f.read()


subject_matchings = subject_matchings.split("\n")[2:]
subject_matchings = [l.split(",") for l in subject_matchings]
subject_matchings = [
    {"q": l[0].lower(), "d": [s.lower() for s in l[1:]]} for l in subject_matchings
]

query_image_folder = extract_root.joinpath("query_images")


existing_qs = [s.lower() for s in os.listdir(query_image_folder)]
# print(f"existing_qs={existing_qs}")
subject_matchings = [m for m in subject_matchings if m["q"] in existing_qs]
# print(f"subject_matchings={subject_matchings}")




def find_query_image(subject_id, distance, suffix) -> str:
    subject_folder = query_image_folder.joinpath(subject_id.lower())
    if distance == 5:
        search_folder = subject_folder.joinpath("controlled")
    else:
        search_folder = subject_folder.joinpath("field").joinpath(str(distance) + "m")
    candidates: List[str] = [
        str(os.path.join(dp, f))
        for dp, dn, filenames in os.walk(search_folder)
        for f in filenames
    ]
    for c in candidates:
        if c.endswith(suffix):
            return c
    raise Exception(f"could not find id={subject_id},d=${distance},suffix={suffix}")



original_distractors_folder = extract_root.joinpath("Gallery_brs1_jpegs")

distractors_folder = extract_root.joinpath("Gallery_brs1_jpegs_downsampled")

DESIRED_WIDTH = 150
if not os.path.exists(distractors_folder):
    originals = os.listdir(original_distractors_folder)
    originals.remove(".DS_Store")
    os.mkdir(distractors_folder)
    for o in originals:
        original = os.path.join(original_distractors_folder, o)
        downsampled = os.path.join(distractors_folder, o)
        img = Image.open(original)
        w_percent = DESIRED_WIDTH / float(img.size[0])
        h_size = int(float(img.size[1]) * float(w_percent))
        img_resized = img.resize((DESIRED_WIDTH, h_size), PIL.Image.Resampling.LANCZOS)
        img_resized.save(downsampled, "JPEG")


available_distractor_images = os.listdir(distractors_folder)


def find_distractor_image(subject_id):
    id_lower = subject_id.lower()
    for d in available_distractor_images:
        if d.startswith(id_lower):
            return str(distractors_folder.joinpath(d))
    raise Exception(f"could not find subject_id={subject_id}")


@dataclasses.dataclass
class HeadBodyTrial:
    query_id: str
    query_image: str
    dist: int
    condition: str
    query_distractor: str
    distractor_images: List[str]
    trial_set: TrialSet


class TrialSet:
    def __init__(self):

        self.base: [HeadBodyTrial] = None
        self.body_occluded: Optional[HeadBodyTrial] = None
        self.head_occluded: Optional[HeadBodyTrial] = None


all_trials = []
print(f"{len(subject_matchings)=}")
for matching in subject_matchings:

    subject_id = matching["q"]

    for dist in distances:
        trial_set = TrialSet()
        for condition in conditions:
            query_image = find_query_image(
                subject_id=subject_id, distance=dist, suffix=f"{condition}.jpg"
            )
            t = HeadBodyTrial(
                query_id=subject_id,
                query_image=query_image,
                query_distractor=find_distractor_image(subject_id),
                distractor_images=[find_distractor_image(it) for it in matching["d"]],
                trial_set=trial_set,
                dist=dist,
                condition=condition,
            )
            if condition == "_ar_bo":
                trial_set.body_occluded = t
            elif condition == "_ar_ho":
                trial_set.head_occluded = t
            elif condition == FINAL_CONDITION:
                trial_set.base = t
            else:
                raise Exception("???")
            all_trials.append(t)
print(f"{len(all_trials)=}")

# print(f"size of all_trials: {len(all_trials)}")

EXAMPLE_IM_1 = "WB_examples_1.jpg"
EXAMPLE_IM_2 = "WB_examples_2.jpg"

with exp.image_upload_session() as upload_session:
    # print("inside image upload session")
    upload_session.upload_image_async_efficient(
        local_abs_path=f"/Users/matthewgroth/registered/ide/all/k/iarpa/src/jvmTest/resources/{EXAMPLE_IM_1}",
        remote_rel_path=EXAMPLE_IM_1,
    )

    upload_session.upload_image_async_efficient(
        local_abs_path=f"/Users/matthewgroth/registered/ide/all/k/iarpa/src/jvmTest/resources/{EXAMPLE_IM_2}",
        remote_rel_path=EXAMPLE_IM_2,
    )

    for d in available_distractor_images:
        abs_d = str(os.path.join(distractors_folder, d))
        remote_rel_path = os.path.relpath(abs_d, extract_root)
        upload_session.upload_image_async_efficient(
            local_abs_path=abs_d, remote_rel_path=remote_rel_path
        )
        # print(f"{remote_rel_path=}")

    for trial in all_trials:
        q_im = trial.query_image

        remote_rel_path = os.path.relpath(q_im, query_image_folder)
        # print(f"{remote_rel_path=}")
        upload_session.upload_image_async_efficient(
            local_abs_path=q_im,
            remote_rel_path=remote_rel_path,
        )


rand = random.Random(
    345934985
)  #  changed from 39457 after the `and`/`or`+`==`/`!=` bug
manifests = []

rand.shuffle(all_trials)

# all_trial_sets = set([t.trial_set for t in all_trials])

TRIAL_BATCHES_TO_GEN = 40  # make this number as high as needed.

remaining_trials = []
for i in range(TRIAL_BATCHES_TO_GEN):
    trial_batch = all_trials.copy()
    rand.shuffle(trial_batch)
    remaining_trials.extend(trial_batch)


# remaining_trials_last_size = -1
t_candidate_index = -1


def swapPositions(li, pos1, pos2):
    li[pos1], li[pos2] = li[pos2], li[pos1]


total_trials_needed = TRIALS_PER_SUBJECT * NUM_PARTICIPANTS
if len(remaining_trials) < total_trials_needed:
    raise Exception(
        f"need {total_trials_needed} trials, but only have {len(remaining_trials)}. Try increasing TRIAL_BATCHES_TO_GEN"
    )

for i in range(NUM_PARTICIPANTS):
    # print(f"generating trials for participant {i}")

    # if len(remaining_trials) == remaining_trials_last_size:
    #     raise Exception("remaining trials not decreasing")
    # remaining_trials_last_size = len(remaining_trials)
    trials = [
        oexp.access.prompt(
            text="""
Welcome to the Person Identification experiment.

The study aims to examine how identification performance changes across conditions where the head, body, or neither are occluded and at varying viewing distances. 

You will be presented with a query image of a person at the left of the screen. The face or body may be sometimes occluded, meaning you will not see part of the image. You will be asked to compare it with five other images of people on the right side of the screen.

Press SPACEBAR to see an example.
  """.strip(),
            image=None,
        ),
        oexp.access.prompt(
            text="""
By clicking on the images on the right side of the screen, you will indicate which are the top three most similar identities to the query identity on the left.

Press SPACEBAR to continue example.
	  """.strip(),
            image=oexp.access.image(remote_path=EXAMPLE_IM_1, one_shot=False),
        ),
        oexp.access.prompt(
            text="""
Once you have ranked your top three images, you can continue to the next trial (click blue button).
If you want to change your choices - click the red reset button.

Press SPACEBAR to start the experiment.
	  """.strip(),
            image=oexp.access.image(remote_path=EXAMPLE_IM_2, one_shot=False),
        ),
    ]

    intro_trials_len = len(trials)

    ids_got = []
    my_trials = []
    distances_shuffled = distances.copy()
    rand.shuffle(distances)
    dist_iter = itertools.cycle(distances)
    next_distance = next(dist_iter)

    last_trials_check_size = -1
    while len(ids_got) < IDS_PER_SUBJECT:
        t_candidate_index += 1
        if t_candidate_index == len(remaining_trials):
            t_candidate_index = 0
        next_trial_candidate = remaining_trials[t_candidate_index]
        if t_candidate_index == 0:
            if last_trials_check_size == len(my_trials):
                raise Exception(
                    f"not getting new trials ({i=}, {next_distance=},{ids_got=}). Try increasing TRIAL_BATCHES_TO_GEN"
                )
            last_trials_check_size = len(my_trials)
        candidate_id = next_trial_candidate.query_id
        candidate_dist = next_trial_candidate.dist
        if candidate_id in ids_got or candidate_dist != next_distance:
            continue
        else:
            next_distance = next(dist_iter)
            ids_got.append(candidate_id)
            trial_set = next_trial_candidate.trial_set
            my_trials.append(trial_set.base)
            my_trials.append(trial_set.head_occluded)
            my_trials.append(trial_set.body_occluded)
            i = remaining_trials.index(trial_set.base)
            if i <= t_candidate_index:
                t_candidate_index -= 1
            remaining_trials.remove(trial_set.base)
            i = remaining_trials.index(trial_set.head_occluded)
            if i <= t_candidate_index:
                t_candidate_index -= 1
            remaining_trials.remove(trial_set.head_occluded)
            i = remaining_trials.index(trial_set.body_occluded)
            if i <= t_candidate_index:
                t_candidate_index -= 1
            remaining_trials.remove(trial_set.body_occluded)

    rand.shuffle(my_trials)
    finished_trial_sets = set()
    for i in range(len(my_trials)):
        t = my_trials[i]
        t_set = t.trial_set
        if t_set in finished_trial_sets:
            continue
        finished_trial_sets.add(t_set)
        base = t_set.base
        bo = t_set.body_occluded
        ho = t_set.head_occluded
        i_base = my_trials.index(base)
        i_bo = my_trials.index(bo)
        i_ho = my_trials.index(ho)
        all_i = sorted([i_base, i_bo, i_ho])
        my_trials[all_i[2]] = base
        if bool(rand.getrandbits(1)):
            my_trials[all_i[0]] = bo
            my_trials[all_i[1]] = ho
        else:
            my_trials[all_i[0]] = ho
            my_trials[all_i[1]] = bo

    ONE_SHOT = True

    for t in my_trials:
        distractors = [
            oexp.access.image(
                remote_path=os.path.relpath(t.query_distractor, extract_root),
                one_shot=ONE_SHOT,
            ),
            *[
                oexp.access.image(
                    remote_path=os.path.relpath(im, extract_root), one_shot=ONE_SHOT
                )
                for im in t.distractor_images
            ],
        ]
        rand.shuffle(distractors)
        query_image = oexp.access.image(
            remote_path=os.path.relpath(t.query_image, query_image_folder),
            one_shot=ONE_SHOT,
        )
        trial = oexp.access.gallery_trial(query=query_image, distractors=distractors)
        trials.append(trial)

    real_trials_len = len(trials) - intro_trials_len
    if real_trials_len != TRIALS_PER_SUBJECT:
        raise Exception(
            f"expected {TRIALS_PER_SUBJECT} trials, but got {real_trials_len}"
        )
    manifests.append(oexp.access.trial_manifest(trials))

exp.manifests = manifests

with open(STYLE_FILE, "r") as f:
    exp.scss = f.read()

# IT IS ALREADY LINKED
# exp.link_prolific("653eed5fd37d6c92ea04798b")

if args.print:
    print(
        "Sharable Experiment URL:",
        exp.session_url(
            disable_auto_fullscreen=True,
            allow_fullscreen_exit=True,
            lab_key=args.lab_key,
            hot_css=hotcss,
        ),
    )

if args.open:
    exp.open(
        disable_auto_fullscreen=True,
        allow_fullscreen_exit=True,
        lab_key=args.lab_key,
        hot_css=hotcss,
    )

if hotcss:
    exp.hot_css(str(STYLE_FILE))

args = parser.parse_args()
