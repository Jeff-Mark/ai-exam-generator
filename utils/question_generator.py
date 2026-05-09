import random

verbs = ["Define", "Explain", "Discuss", "Evaluate"]


def generate_question(topic):
    verb = random.choice(verbs)
    return f"{verb} {topic}"
