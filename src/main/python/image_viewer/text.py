def main_prompt(none_choice):
    return f"""
Welcome to the Orientation Annotater.

We will ask you to look at images of people. For each image, please select the head orientation that is the most similar to the image.

If none are similar, select "{none_choice}". 

Press SPACEBAR to start
      """.strip()
