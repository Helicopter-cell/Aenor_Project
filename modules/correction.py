from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def check_answer(user, correct):
    user = user.lower()
    correct = correct.lower()

    if user == correct:
        return "✅ Correct !"
    elif similarity(user, correct) > 0.75:
        return "🟡 Presque !"
    else:
        return "❌ Faux !"