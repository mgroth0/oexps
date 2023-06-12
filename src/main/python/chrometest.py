import sys
from pathlib import Path

this_file = Path(__file__)
pw = str(this_file.parent.parent.parent.parent.parent.joinpath("src").joinpath("main").joinpath("python"))
print(f"{pw=}")
sys.path.append(pw)

import oexp
from oexp import access
import os

STYLE_FILE = this_file.parent.joinpath("chrometest.css")

matt_user = os.environ['MATT_USER']
matt_pw = os.environ['MATT_PW']
if (ktor_port := os.getenv("MATT_KTOR_PORT")) is not None:
    # noinspection PyProtectedMember
    # noinspection PyArgumentList
    access.API.enable_local_mode(int(ktor_port))

user = oexp.login(matt_user, matt_pw)

exp = user.experiment("chrometest")
exp.delete_all_images()
ims = exp.upload_images("/Users/matthewgroth/registered/bolt/oexp_demo/images")
uploaded_images = exp.list_images()
import random

manifests = []
for m in range(20):
    trials = []
    for t in range(15):
        trial = oexp.access.trial(
            query=random.choice(uploaded_images),
            distractors=[random.choice(uploaded_images) for i in range(5)]
        )
        trials.append(trial)
    manifests.append(oexp.access.trial_manifest(trials))
exp.manifests = manifests
with open(STYLE_FILE, "r") as f:
    exp.css = f.read()
