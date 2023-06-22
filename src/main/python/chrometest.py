import sys
from pathlib import Path

this_file = Path(__file__)
sys.path.append(str(this_file.parent.parent.parent.parent.parent.joinpath("src").joinpath("main").joinpath("python")))

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

exp.upload_image(
    local_abs_path="/Users/matthewgroth/registered/ide/all/k/iarpa/src/jvmTest/resources/Example_Online_BRIAR_1.jpg",
    remote_rel_path="Example_Online_BRIAR_1.jpg"
)
exp.upload_image(
    local_abs_path="/Users/matthewgroth/registered/ide/all/k/iarpa/src/jvmTest/resources/Example_Online_BRIAR_2.jpg",
    remote_rel_path="Example_Online_BRIAR_2.jpg"
)


import random

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
            image=None
        ),
        oexp.access.prompt(
            text="""
By clicking on the images in the bottom row, you will indicate which are the top three most similar identities to the identity at the top.

Press SPACEBAR to continue example.
	  """.strip(),
            image="Example_Online_BRIAR_1.jpg"
        ),
        oexp.access.prompt(
            text="""
Once you have ranked your top three images, you can continue to the next trial (click blue button).
If you want to change your choices - click the red reset button.

Press SPACEBAR to start the experiment.
	  """.strip(),
            image="Example_Online_BRIAR_2.jpg"
        ),
    ]
    for t in range(15):
        trial = oexp.access.gallery_trial(
            query=random.choice(uploaded_images),
            distractors=[random.choice(uploaded_images) for i in range(5)]
        )
        trials.append(trial)
    manifests.append(oexp.access.trial_manifest(trials))
exp.manifests = manifests
with open(STYLE_FILE, "r") as f:
    exp.css = f.read()
