def main_prompt():
    return f"""
Welcome to the head and body orientation experiment.

In this study you will be asked to match the orientations of a 3D head and a 3D body with the head and body of a person in an image. You will need a mouse or a touch pad to control the orientation, and a keyboard to confirm your choices.
 
To minimize complexity, the 3D head can only move in two ways: 
    - Vertical - up and down, like saying “yes”, named Pitch movement.
    - Horizontal - side to side, like saying “no”, named Yaw movement.

The 3D body can only move in one way - from side to side.

For each trial (image) you have unlimited time. You will first be asked to determine the body orientation, and once you have made your choice you will be asked to determine the head’s orientation. There is no option to go back to change your choice, so, please make sure you are happy with the orientation before confirming the final position of the head/body.

Press the spacebar to continue

      """.strip()


def review_instructions_prompt():
    return f"""

Ready to start the experiment?

Please remember:

    - Do not exit the full screen mode because the experiment will stop and close
    - The progress bar (on the top/bottom) will indicate how far you’ve gone through the trials
    - Please pay careful attention to the images. This is an academic study and we need to ensure the quality of the data. We will not be able to use data that is no better than chance level. Thank you for your understanding and for your thoughtful participation. 


Press the spacebar to begin experiment !


      """.strip()