#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Author the language cubes — French, German, Latin, Hebrew, Mandarin — into coach curriculum files.

Matt, 2026-09-21: "wire french, german, latin, and hebrew ... mandarin as well."

The CUBE is the fixed frame (Cubo's method): five embodied anchors + a review, learned in the
learner's own room. The body shows what the words mean before the words are understood. Only the
TARGET LANGUAGE changes — the cube stays. English is the instruction language (the coach's script);
each target phrase is given in its own script, with romanization where the script is not Latin, and
an English gloss, so the learner can say it and know what they said.

Every non-Latin example is written  <native> — <romanization> — <English>  so all three are on the
card. Authored curriculum (generated:false), marked DRAFT pending the author's review, exactly as the
English anchor cube is.

    PYTHONPATH=src python build_cubes.py           # writes data/curriculum/{fr,de,la,he,zh}_en.json
"""
from __future__ import annotations
import io, json, sys
from pathlib import Path

OUT = Path("data") / "curriculum"


def U(track, seq, uid, title, rule, examples, decodable,
      c_instr, c_script, t_instr, t_script, prompt, answer, note, choices):
    return {
        "id": uid, "unit_seq": seq, "track": track, "title": title, "rule": rule,
        "examples": examples, "decodable_sentence": decodable,
        "modes": [
            {"id": "coach_models", "label": "The coach shows", "instruction": c_instr, "script": c_script},
            {"id": "take_turns", "label": "Take turns", "instruction": t_instr, "script": t_script},
        ],
        "check": {"prompt": prompt, "answer": answer, "teaching_note": note, "choices": choices},
        "generated": False,
    }


def cube(subject, track, note, units):
    return {"subject": subject, "track": track, "track_note": note, "units": units}


# ─────────────────────────────────────────────── FRENCH ───────────────────────────────────────────
FR = cube("fr", "cubo_fr",
    "Speech track for learning FRENCH by the cube — five embodied anchors in the learner's own room. "
    "English is the instruction; each French phrase is given with an English gloss. Status: DRAFT, "
    "pending author review.",
    [
     U("cubo_fr", 1, "cubo_fr_iam", "Je suis — where I stand",
       "Je suis (zhuh swee) means \"I am\". Stand in the middle of your room and point to yourself: "
       "Je suis ici — I am here. The words travel with you; wherever you stand, Je suis ici is true "
       "from that spot.",
       ["Je suis ici. — I am here.",
        "Je suis dans la maison. — I am in the house.",
        "Je suis dans la cuisine. — I am in the kitchen."],
       "Je suis ici.",
       "Stand in the center, point to yourself, and say Je suis ici. Walk to the door and say it again — the words move with you.",
       "Je suis ici. Now I walk to the door. Je suis ici. Same words, new spot.",
       "Name a place in the room. The learner walks there and says Je suis dans plus the place.",
       "You say: la cuisine. The learner walks there and says: Je suis dans la cuisine.",
       "You are standing in the kitchen. Which is true?",
       "Je suis dans la cuisine.",
       "Only one answer matches where the body actually is. If unsure, walk to the kitchen and say it from there.",
       ["Je suis dans la cuisine.", "Je suis dans le lit.", "Je vais à la cuisine."]),
     U("cubo_fr", 2, "cubo_fr_thereis", "Il y a — what exists in the space",
       "Il y a (eel-ya) means \"there is\" or \"there are\" — French uses the same words for one or "
       "many. Look around the room and name what is there without pointing at any one thing.",
       ["Il y a une table. — There is a table.",
        "Il y a deux chaises. — There are two chairs.",
        "Il y a de l'eau. — There is water."],
       "Il y a une table et il y a deux chaises.",
       "Sweep your hand across the room and name three things with Il y a — do not point at any single one.",
       "Il y a une table. Il y a deux chaises. Il y a une porte.",
       "The learner finds something and says Il y a plus the thing. Then you find one. Keep going to five.",
       "The learner sees the window and says: Il y a une fenêtre.",
       "There are two chairs in the room. Which is true?",
       "Il y a deux chaises.",
       "Je suis is only for where I stand. Things that simply exist take Il y a — for one thing and for many.",
       ["Il y a deux chaises.", "Je suis deux chaises.", "Je vais deux chaises."]),
     U("cubo_fr", 3, "cubo_fr_thisis", "C'est — pointing at one thing",
       "C'est (say) means \"this is\" — it walks up to one thing, points, and names it. Il y a says a "
       "thing exists somewhere; C'est points right at it.",
       ["C'est une table. — This is a table.",
        "C'est mon chien. — This is my dog.",
        "C'est grand. — It is big."],
       "C'est une chaise.",
       "Point directly at one object and name it with C'est. Then point at another. Finger and words go together.",
       "C'est une table. C'est une chaise. C'est ma tasse.",
       "Point at an object; the learner names it with C'est. Then the learner points and you name it.",
       "You point at the dog. The learner says: C'est un chien.",
       "You point at a dog. Which is true?",
       "C'est un chien.",
       "The test is the pointing finger. If you can point at the one thing you mean, the words are C'est.",
       ["C'est un chien.", "Il y a ici.", "Je suis un chien."]),
     U("cubo_fr", 4, "cubo_fr_igo", "Je vais — the arrow of movement",
       "Je vais (zhuh vay) means \"I go\". It is the arrow from where you stand to where you will be: "
       "Je vais à la porte. When the arrow finishes, it becomes Je suis again: Je suis à la porte.",
       ["Je vais à la cuisine. — I go to the kitchen.",
        "Je vais à la porte. — I go to the door.",
        "Je suis à la porte. — I am at the door."],
       "Je vais à la porte.",
       "Say Je vais à plus a place, then walk there. On arrival, stop and say Je suis à plus the place. Show the flip.",
       "Je vais à la porte. I walk. I arrive. Je suis à la porte.",
       "Call a destination. The learner says Je vais à plus the place, walks there, and on arrival says Je suis à plus the place.",
       "You say: la cuisine. The learner says Je vais à la cuisine, walks, and says Je suis dans la cuisine.",
       "You are walking to the door right now. Which is true?",
       "Je vais à la porte.",
       "While the feet move, the words are Je vais. When the feet stop, they flip to Je suis.",
       ["Je vais à la porte.", "Je suis la porte.", "Il y a la porte."]),
     U("cubo_fr", 5, "cubo_fr_path", "De, par, à — the three parts of the path",
       "Every arrow has three parts. De is where it starts, par is the space it passes through, à is "
       "where it ends. Walk the whole path and say it.",
       ["Je vais de la cuisine à la porte. — I go from the kitchen to the door.",
        "Je vais par le couloir. — I go through the hall.",
        "Je vais de la chaise à la table. — I go from the chair to the table."],
       "Je vais de la cuisine, par le couloir, à la porte.",
       "Announce your start with de, the middle with par, the arrival with à — narrate each as your body reaches it.",
       "Je vais de la cuisine... par le couloir... à la porte. Je suis à la porte.",
       "Give the learner a start and an end. The learner walks it, saying all three parts in order.",
       "From the chair to the window. The learner says: Je vais de la chaise, par le couloir, à la fenêtre.",
       "Put the path words in order from start to finish.",
       "De, par, à.",
       "De starts, par carries, à lands. If they mix, walk the path slowly and say each word in that part.",
       ["De, par, à.", "À, par, de.", "Par, de, à."]),
     U("cubo_fr", 6, "cubo_fr_review", "Revue — the whole cube in one breath",
       "Now run the whole cube in French. Stand: Je suis. Look around: Il y a. Point: C'est. Move: Je "
       "vais, with de, par, à marking the path. Five anchors, one room, one breath.",
       ["Je suis ici. — I am here.",
        "Il y a une table. — There is a table.",
        "C'est ma chaise. — This is my chair.",
        "Je vais de la chaise à la porte. — I go from the chair to the door."],
       "Je suis ici. Il y a une table. C'est ma chaise. Je vais de la chaise, par le couloir, à la porte.",
       "Perform the full sequence with your body: stand and say Je suis, sweep and say Il y a, point and say C'est, then walk saying Je vais de, par, à.",
       "Je suis ici. Il y a une table et deux chaises. C'est ma tasse. Je vais de la table, par le couloir, à la porte. Je suis à la porte.",
       "The learner performs the full run in their own room with their own objects. Then you perform it and make one deliberate mistake to catch.",
       "The learner stands, sweeps, points, and walks, saying all five anchors in order.",
       "You point at one chair and name it. Which anchor do you use?",
       "C'est.",
       "Pointing at one named thing is always C'est. If any anchor slips, return to that unit and run its body movement again.",
       ["Je suis.", "Il y a.", "C'est.", "Je vais."]),
    ])


# ─────────────────────────────────────────────── GERMAN ───────────────────────────────────────────
DE = cube("de", "cubo_de",
    "Speech track for learning GERMAN by the cube — five embodied anchors in the learner's own room. "
    "English is the instruction; each German phrase is given with an English gloss. German changes the "
    "word for \"the\" and \"a\" with the case; the examples show the correct form. Status: DRAFT, pending "
    "author review.",
    [
     U("cubo_de", 1, "cubo_de_iam", "Ich bin — where I stand",
       "Ich bin (ikh bin) means \"I am\". Stand in the middle of your room, point to yourself: Ich bin "
       "hier — I am here. Wherever you stand, Ich bin hier is true from that spot.",
       ["Ich bin hier. — I am here.",
        "Ich bin im Haus. — I am in the house.",
        "Ich bin in der Küche. — I am in the kitchen."],
       "Ich bin hier.",
       "Stand in the center, point to yourself, say Ich bin hier. Walk to the door and say it again.",
       "Ich bin hier. Now I walk to the door. Ich bin hier. Same words, new spot.",
       "Name a place. The learner walks there and says Ich bin plus the place.",
       "You say: die Küche. The learner walks there and says: Ich bin in der Küche.",
       "You are standing in the kitchen. Which is true?",
       "Ich bin in der Küche.",
       "Only one answer matches where the body actually is. If unsure, walk to the kitchen and say it there.",
       ["Ich bin in der Küche.", "Ich bin im Bett.", "Ich gehe in die Küche."]),
     U("cubo_de", 2, "cubo_de_thereis", "Es gibt — what exists in the space",
       "Es gibt (es gipt) means \"there is\" or \"there are\" — the same for one or many. Look around "
       "the room and name what is there.",
       ["Es gibt einen Tisch. — There is a table.",
        "Es gibt zwei Stühle. — There are two chairs.",
        "Es gibt Wasser. — There is water."],
       "Es gibt einen Tisch und es gibt zwei Stühle.",
       "Sweep your hand across the room and name three things with Es gibt — do not point at one.",
       "Es gibt einen Tisch. Es gibt zwei Stühle. Es gibt eine Tür.",
       "The learner finds something and says Es gibt plus the thing. Keep going to five.",
       "The learner sees the window and says: Es gibt ein Fenster.",
       "There are two chairs in the room. Which is true?",
       "Es gibt zwei Stühle.",
       "Ich bin is only for where I stand. Things that simply exist take Es gibt.",
       ["Es gibt zwei Stühle.", "Ich bin zwei Stühle.", "Ich gehe zwei Stühle."]),
     U("cubo_de", 3, "cubo_de_thisis", "Das ist — pointing at one thing",
       "Das ist (das ist) means \"this is\" — walk up to one thing, point, and name it. Es gibt says a "
       "thing exists; Das ist points right at it.",
       ["Das ist ein Tisch. — This is a table.",
        "Das ist mein Hund. — This is my dog.",
        "Das ist groß. — It is big."],
       "Das ist ein Stuhl.",
       "Point directly at one object and name it with Das ist. Then point at another.",
       "Das ist ein Tisch. Das ist ein Stuhl. Das ist meine Tasse.",
       "Point at an object; the learner names it with Das ist. Then the learner points and you name it.",
       "You point at the dog. The learner says: Das ist ein Hund.",
       "You point at a dog. Which is true?",
       "Das ist ein Hund.",
       "The test is the pointing finger. If you can point at the one thing you mean, the words are Das ist.",
       ["Das ist ein Hund.", "Es gibt hier.", "Ich bin ein Hund."]),
     U("cubo_de", 4, "cubo_de_igo", "Ich gehe — the arrow of movement",
       "Ich gehe (ikh gay-uh) means \"I go\". It is the arrow from where you stand to where you will "
       "be: Ich gehe zur Tür. When the arrow finishes, it becomes Ich bin again: Ich bin an der Tür.",
       ["Ich gehe in die Küche. — I go to the kitchen.",
        "Ich gehe zur Tür. — I go to the door.",
        "Ich bin an der Tür. — I am at the door."],
       "Ich gehe zur Tür.",
       "Say Ich gehe zu plus a place, then walk there. On arrival say Ich bin an plus the place. Show the flip.",
       "Ich gehe zur Tür. I walk. I arrive. Ich bin an der Tür.",
       "Call a destination. The learner says Ich gehe, walks there, and on arrival says Ich bin an plus the place.",
       "You say: die Küche. The learner says Ich gehe in die Küche, walks, and says Ich bin in der Küche.",
       "You are walking to the door right now. Which is true?",
       "Ich gehe zur Tür.",
       "While the feet move, the words are Ich gehe. When the feet stop, they flip to Ich bin.",
       ["Ich gehe zur Tür.", "Ich bin die Tür.", "Es gibt die Tür."]),
     U("cubo_de", 5, "cubo_de_path", "Von, durch, zu — the three parts of the path",
       "Every arrow has three parts. Von is where it starts, durch is the space it passes through, zu "
       "is where it ends. Walk the whole path and say it.",
       ["Ich gehe von der Küche zur Tür. — I go from the kitchen to the door.",
        "Ich gehe durch den Flur. — I go through the hall.",
        "Ich gehe vom Stuhl zum Tisch. — I go from the chair to the table."],
       "Ich gehe von der Küche, durch den Flur, zur Tür.",
       "Announce your start with von, the middle with durch, the arrival with zu — narrate each as your body reaches it.",
       "Ich gehe von der Küche... durch den Flur... zur Tür. Ich bin an der Tür.",
       "Give the learner a start and an end. The learner walks it, saying all three parts in order.",
       "From the chair to the window. The learner says: Ich gehe vom Stuhl, durch den Flur, zum Fenster.",
       "Put the path words in order from start to finish.",
       "Von, durch, zu.",
       "Von starts, durch carries, zu lands. If they mix, walk the path slowly and say each word in that part.",
       ["Von, durch, zu.", "Zu, durch, von.", "Durch, von, zu."]),
     U("cubo_de", 6, "cubo_de_review", "Wiederholung — the whole cube in one breath",
       "Now run the whole cube in German. Stand: Ich bin. Look around: Es gibt. Point: Das ist. Move: "
       "Ich gehe, with von, durch, zu marking the path. Five anchors, one room, one breath.",
       ["Ich bin hier. — I am here.",
        "Es gibt einen Tisch. — There is a table.",
        "Das ist mein Stuhl. — This is my chair.",
        "Ich gehe vom Stuhl zur Tür. — I go from the chair to the door."],
       "Ich bin hier. Es gibt einen Tisch. Das ist mein Stuhl. Ich gehe vom Stuhl, durch den Flur, zur Tür.",
       "Perform the full sequence with your body: stand and say Ich bin, sweep and say Es gibt, point and say Das ist, then walk saying Ich gehe von, durch, zu.",
       "Ich bin hier. Es gibt einen Tisch und zwei Stühle. Das ist meine Tasse. Ich gehe vom Tisch, durch den Flur, zur Tür. Ich bin an der Tür.",
       "The learner performs the full run in their own room. Then you perform it and make one deliberate mistake to catch.",
       "The learner stands, sweeps, points, and walks, saying all five anchors in order.",
       "You point at one chair and name it. Which anchor do you use?",
       "Das ist.",
       "Pointing at one named thing is always Das ist. If any anchor slips, return to that unit and run its body movement again.",
       ["Ich bin.", "Es gibt.", "Das ist.", "Ich gehe."]),
    ])


# ─────────────────────────────────────────────── LATIN ────────────────────────────────────────────
LA = cube("la", "cubo_la",
    "Speech track for learning LATIN by the cube — five embodied anchors in the learner's own room. "
    "English is the instruction; each Latin phrase is given with an English gloss. Latin marks a word's "
    "job by its ENDING, so the same noun changes shape as it moves through the path — the examples show "
    "the correct ending. The verb often stands last. Status: DRAFT, pending author review.",
    [
     U("cubo_la", 1, "cubo_la_iam", "Sum — where I stand",
       "Sum (soom) means \"I am\". Stand in the middle of your room and point to yourself: Hic sum — "
       "here I am. The verb sum can stand alone; hic means \"here\". Wherever you stand, Hic sum is true.",
       ["Hic sum. — Here I am.",
        "In casa sum. — I am in the house.",
        "In culina sum. — I am in the kitchen."],
       "Hic sum.",
       "Stand in the center, point to yourself, say Hic sum. Walk to the door and say it again.",
       "Hic sum. Now I walk to the door. Hic sum. Same words, new spot.",
       "Name a place. The learner walks there and says In plus the place plus sum.",
       "You say: culina (kitchen). The learner walks there and says: In culina sum.",
       "You are standing in the kitchen. Which is true?",
       "In culina sum.",
       "Only one answer matches where the body actually is. In Latin the verb sum can sit at the end.",
       ["In culina sum.", "In lecto sum.", "Ad culinam eo."]),
     U("cubo_la", 2, "cubo_la_thereis", "Est / Sunt — what exists in the space",
       "Est (est) means \"there is\" for one thing; Sunt (soont) means \"there are\" for many. Look "
       "around the room and name what is there.",
       ["Est mensa. — There is a table.",
        "Sunt duae sellae. — There are two chairs.",
        "Est aqua. — There is water."],
       "Est mensa et sunt duae sellae.",
       "Sweep your hand across the room. Use Est for one thing, Sunt for many.",
       "Est mensa. Sunt duae sellae. Est ianua.",
       "The learner finds one thing (Est) or several (Sunt) and names them. Keep going to five.",
       "The learner sees the window and says: Est fenestra.",
       "There are two chairs in the room. Which is true?",
       "Sunt duae sellae.",
       "One thing takes Est; many take Sunt. Hic sum is only for where I stand.",
       ["Sunt duae sellae.", "Duae sellae sum.", "Ad sellas eo."]),
     U("cubo_la", 3, "cubo_la_thisis", "Hic / Haec / Hoc est — pointing at one thing",
       "\"This is\" points at one thing and names it. Latin fits the word for \"this\" to the thing: "
       "hic for a masculine thing, haec for a feminine one, hoc for a neuter one. Point, then name.",
       ["Haec est mensa. — This is a table. (mensa is feminine)",
        "Hic est canis meus. — This is my dog. (canis is masculine)",
        "Hoc est magnum. — This is big. (neuter)"],
       "Haec est sella.",
       "Point at one object and name it, fitting hic / haec / hoc to the thing. Then point at another.",
       "Haec est mensa. Haec est sella. Hoc est poculum meum.",
       "Point at an object; the learner names it with hic, haec, or hoc plus est. Then switch.",
       "You point at the dog. The learner says: Hic est canis.",
       "You point at a dog (canis, masculine). Which is true?",
       "Hic est canis.",
       "The word for \"this\" fits the thing: hic (masc.), haec (fem.), hoc (neut.). The pointing finger tells you it is a \"this is\".",
       ["Hic est canis.", "Est hic.", "Canis sum."]),
     U("cubo_la", 4, "cubo_la_igo", "Eo — the arrow of movement",
       "Eo (eh-oh) means \"I go\". It is the arrow from where you stand to where you will be: Ad ianuam "
       "eo — I go to the door. When the arrow finishes, you are there again: Nunc adsum — now I am here. "
       "Notice ianua becomes ianuam after ad.",
       ["Ad culinam eo. — I go to the kitchen.",
        "Ad ianuam eo. — I go to the door.",
        "Nunc adsum. — Now I am here."],
       "Ad ianuam eo.",
       "Say Ad plus a place plus eo, then walk there. On arrival, stop and say Nunc adsum. Show the flip.",
       "Ad ianuam eo. I walk. I arrive. Nunc adsum.",
       "Call a destination. The learner says Ad plus the place plus eo, walks there, and on arrival says Nunc adsum.",
       "You say: culina. The learner says Ad culinam eo, walks, and says Nunc adsum.",
       "You are walking to the door right now. Which is true?",
       "Ad ianuam eo.",
       "While the feet move, the words are eo. When the feet stop, you are there: adsum. After ad, ianua changes to ianuam.",
       ["Ad ianuam eo.", "Ianua sum.", "Est ianua."]),
     U("cubo_la", 5, "cubo_la_path", "Ab, per, ad — the three parts of the path",
       "Every arrow has three parts. Ab is where it starts, per is the space it passes through, ad is "
       "where it ends. Each one changes the noun's ending: ab culina, per atrium, ad ianuam.",
       ["Ab culina ad ianuam eo. — I go from the kitchen to the door.",
        "Per atrium eo. — I go through the hall.",
        "A sella ad mensam eo. — I go from the chair to the table."],
       "Ab culina, per atrium, ad ianuam eo.",
       "Announce your start with ab, the middle with per, the arrival with ad — narrate each as your body reaches it.",
       "Ab culina... per atrium... ad ianuam eo. Nunc adsum.",
       "Give the learner a start and an end. The learner walks it, saying all three parts in order.",
       "From the chair to the window. The learner says: A sella, per atrium, ad fenestram eo.",
       "Put the path words in order from start to finish.",
       "Ab, per, ad.",
       "Ab starts, per carries, ad lands. Each changes the noun after it — walk the path slowly and say each word in its part.",
       ["Ab, per, ad.", "Ad, per, ab.", "Per, ab, ad."]),
     U("cubo_la", 6, "cubo_la_review", "Recapitulatio — the whole cube in one breath",
       "Now run the whole cube in Latin. Stand: sum. Look around: est / sunt. Point: hic, haec, hoc "
       "est. Move: eo, with ab, per, ad marking the path. Five anchors, one room, one breath.",
       ["Hic sum. — Here I am.",
        "Est mensa. — There is a table.",
        "Haec est sella mea. — This is my chair.",
        "A sella ad ianuam eo. — I go from the chair to the door."],
       "Hic sum. Est mensa. Haec est sella mea. A sella, per atrium, ad ianuam eo.",
       "Perform the full sequence with your body: stand and say sum, sweep and say est / sunt, point and say hic/haec/hoc est, then walk saying eo with ab, per, ad.",
       "Hic sum. Est mensa et sunt duae sellae. Hoc est poculum meum. A mensa, per atrium, ad ianuam eo. Nunc adsum.",
       "The learner performs the full run in their own room. Then you perform it and make one deliberate mistake to catch.",
       "The learner stands, sweeps, points, and walks, saying all five anchors in order.",
       "You point at one chair (sella, feminine) and name it. Which anchor do you use?",
       "Haec est.",
       "Pointing at one named thing is always hic / haec / hoc est, fitted to the thing. A feminine sella takes haec.",
       ["Sum.", "Est.", "Haec est.", "Eo."]),
    ])


# ─────────────────────────────────────────────── HEBREW ───────────────────────────────────────────
HE = cube("he", "cubo_he",
    "Speech track for learning HEBREW (modern, spoken) by the cube — five embodied anchors in the "
    "learner's own room. English is the instruction; each Hebrew phrase is given as  Hebrew — "
    "romanization — English. Hebrew reads right to left and, in the present, uses no separate word for "
    "\"am/is/are\". Some verbs change with the speaker's gender; both forms are shown. Status: DRAFT, "
    "pending author review.",
    [
     U("cubo_he", 1, "cubo_he_iam", "אֲנִי — where I stand",
       "Ani (אֲנִי) means \"I\". In the present, Hebrew needs no word for \"am\" — you place yourself "
       "with just I plus where. Stand in the middle of your room and say: Ani kan — I (am) here.",
       ["אֲנִי כָּאן — ani kan — I am here.",
        "אֲנִי בַּבַּיִת — ani ba-bayit — I am in the house.",
        "אֲנִי בַּמִּטְבָּח — ani ba-mitbach — I am in the kitchen."],
       "אֲנִי כָּאן — ani kan",
       "Stand in the center, point to yourself, say Ani kan. Walk to the door and say it again — no word for \"am\" is needed.",
       "Ani kan. Now I walk to the door. Ani kan. Same words, new spot.",
       "Name a place. The learner walks there and says Ani ba- plus the place.",
       "You say: mitbach (kitchen). The learner walks there and says: Ani ba-mitbach.",
       "You are standing in the kitchen. Which is true?",
       "אֲנִי בַּמִּטְבָּח — ani ba-mitbach",
       "Only one answer matches where the body actually is. There is no separate word for \"am\": ani plus the place is enough.",
       ["אֲנִי בַּמִּטְבָּח — ani ba-mitbach", "אֲנִי בַּמִּטָּה — ani ba-mita (in the bed)",
        "אֲנִי הוֹלֵךְ לַמִּטְבָּח — ani holech la-mitbach (I go to the kitchen)"]),
     U("cubo_he", 2, "cubo_he_thereis", "יֵשׁ — what exists in the space",
       "Yesh (יֵשׁ) means \"there is\" or \"there are\" — the same word for one or many. Look around "
       "the room and name what is there.",
       ["יֵשׁ שֻׁלְחָן — yesh shulchan — There is a table.",
        "יֵשׁ שְׁנֵי כִּסְאוֹת — yesh shney kis'ot — There are two chairs.",
        "יֵשׁ מַיִם — yesh mayim — There is water."],
       "יֵשׁ שֻׁלְחָן וְיֵשׁ שְׁנֵי כִּסְאוֹת — yesh shulchan ve-yesh shney kis'ot",
       "Sweep your hand across the room and name three things with Yesh — do not point at one.",
       "Yesh shulchan. Yesh shney kis'ot. Yesh delet.",
       "The learner finds something and says Yesh plus the thing. Keep going to five.",
       "The learner sees the window and says: Yesh chalon.",
       "There are two chairs in the room. Which is true?",
       "יֵשׁ שְׁנֵי כִּסְאוֹת — yesh shney kis'ot",
       "Ani is only for where I stand. Things that simply exist take Yesh — one word for one and for many.",
       ["יֵשׁ שְׁנֵי כִּסְאוֹת — yesh shney kis'ot", "אֲנִי שְׁנֵי כִּסְאוֹת — ani shney kis'ot",
        "אֲנִי הוֹלֵךְ כִּסְאוֹת — ani holech kis'ot"]),
     U("cubo_he", 3, "cubo_he_thisis", "זֶה — pointing at one thing",
       "Zeh (זֶה) means \"this is\" for a masculine thing; zot (זֹאת) for a feminine one. It walks up "
       "to one thing, points, and names it. Yesh says a thing exists; zeh points right at it.",
       ["זֶה שֻׁלְחָן — zeh shulchan — This is a table.",
        "זֶה הַכֶּלֶב שֶׁלִּי — zeh ha-kelev sheli — This is my dog.",
        "זֶה גָּדוֹל — zeh gadol — It is big."],
       "זֶה כִּסֵּא — zeh kise",
       "Point directly at one object and name it with Zeh. Then point at another. Finger and words go together.",
       "Zeh shulchan. Zeh kise. Zeh ha-sefel sheli (this is my cup).",
       "Point at an object; the learner names it with Zeh. Then the learner points and you name it.",
       "You point at the dog. The learner says: Zeh kelev.",
       "You point at a dog. Which is true?",
       "זֶה כֶּלֶב — zeh kelev",
       "The test is the pointing finger. Zeh names one masculine thing; a feminine thing takes zot.",
       ["זֶה כֶּלֶב — zeh kelev", "יֵשׁ כָּאן — yesh kan (there is here)",
        "אֲנִי כֶּלֶב — ani kelev (I am a dog)"]),
     U("cubo_he", 4, "cubo_he_igo", "אֲנִי הוֹלֵךְ — the arrow of movement",
       "Ani holech (אֲנִי הוֹלֵךְ) means \"I go / I am going\" when a man speaks; a woman says ani "
       "holechet (הוֹלֶכֶת). It is the arrow from where you stand to where you will be: to the door. "
       "When the arrow finishes, you are there: ani kan.",
       ["אֲנִי הוֹלֵךְ לַמִּטְבָּח — ani holech la-mitbach — I go to the kitchen.",
        "אֲנִי הוֹלֵךְ לַדֶּלֶת — ani holech la-delet — I go to the door.",
        "אֲנִי לְיַד הַדֶּלֶת — ani le-yad ha-delet — I am at the door."],
       "אֲנִי הוֹלֵךְ לַדֶּלֶת — ani holech la-delet",
       "Say Ani holech la- plus a place, then walk there. On arrival, stop and say Ani le-yad plus the place. Show the flip.",
       "Ani holech la-delet. I walk. I arrive. Ani le-yad ha-delet.",
       "Call a destination. The learner says Ani holech la- plus the place, walks there, and on arrival says where they are.",
       "You say: mitbach. The learner says Ani holech la-mitbach, walks, and says Ani ba-mitbach.",
       "You are walking to the door right now. Which is true?",
       "אֲנִי הוֹלֵךְ לַדֶּלֶת — ani holech la-delet",
       "While the feet move, the words are holech (or holechet, if a woman speaks). When the feet stop, you place yourself with ani again.",
       ["אֲנִי הוֹלֵךְ לַדֶּלֶת — ani holech la-delet", "אֲנִי דֶּלֶת — ani delet (I am a door)",
        "יֵשׁ דֶּלֶת — yesh delet (there is a door)"]),
     U("cubo_he", 5, "cubo_he_path", "מִן, דֶּרֶךְ, אֶל — the three parts of the path",
       "Every arrow has three parts. Min (מִן), often shortened to me- on the front of a word, is "
       "where it starts; derech (דֶּרֶךְ) is the space it passes through; el (אֶל) is where it ends. "
       "Walk the whole path and say it.",
       ["אֲנִי הוֹלֵךְ מֵהַמִּטְבָּח אֶל הַדֶּלֶת — ani holech me-ha-mitbach el ha-delet — from the kitchen to the door.",
        "אֲנִי הוֹלֵךְ דֶּרֶךְ הַמִּסְדְּרוֹן — ani holech derech ha-misdron — I go through the hall.",
        "מֵהַכִּסֵּא אֶל הַשֻּׁלְחָן — me-ha-kise el ha-shulchan — from the chair to the table."],
       "אֲנִי הוֹלֵךְ מֵהַמִּטְבָּח, דֶּרֶךְ הַמִּסְדְּרוֹן, אֶל הַדֶּלֶת — ani holech me-ha-mitbach, derech ha-misdron, el ha-delet",
       "Announce your start with me-, the middle with derech, the arrival with el — narrate each as your body reaches it.",
       "Ani holech me-ha-mitbach... derech ha-misdron... el ha-delet. Ani le-yad ha-delet.",
       "Give the learner a start and an end. The learner walks it, saying all three parts in order.",
       "From the chair to the window. The learner says: me-ha-kise, derech ha-misdron, el ha-chalon.",
       "Put the path words in order from start to finish.",
       "מִן, דֶּרֶךְ, אֶל — min, derech, el",
       "Min (me-) starts, derech carries, el lands. If they mix, walk the path slowly and say each word in its part.",
       ["מִן, דֶּרֶךְ, אֶל — min, derech, el", "אֶל, דֶּרֶךְ, מִן — el, derech, min",
        "דֶּרֶךְ, מִן, אֶל — derech, min, el"]),
     U("cubo_he", 6, "cubo_he_review", "חֲזָרָה — the whole cube in one breath",
       "Now run the whole cube in Hebrew. Stand: ani. Look around: yesh. Point: zeh / zot. Move: ani "
       "holech, with min (me-), derech, el marking the path. Five anchors, one room, one breath.",
       ["אֲנִי כָּאן — ani kan — I am here.",
        "יֵשׁ שֻׁלְחָן — yesh shulchan — There is a table.",
        "זֶה הַכִּסֵּא שֶׁלִּי — zeh ha-kise sheli — This is my chair.",
        "אֲנִי הוֹלֵךְ מֵהַכִּסֵּא אֶל הַדֶּלֶת — ani holech me-ha-kise el ha-delet — from the chair to the door."],
       "אֲנִי כָּאן. יֵשׁ שֻׁלְחָן. זֶה הַכִּסֵּא שֶׁלִּי. אֲנִי הוֹלֵךְ מֵהַכִּסֵּא, דֶּרֶךְ הַמִּסְדְּרוֹן, אֶל הַדֶּלֶת.",
       "Perform the full sequence with your body: stand and say ani, sweep and say yesh, point and say zeh, then walk saying ani holech me-, derech, el.",
       "Ani kan. Yesh shulchan ve-shney kis'ot. Zeh ha-sefel sheli. Ani holech me-ha-shulchan, derech ha-misdron, el ha-delet. Ani le-yad ha-delet.",
       "The learner performs the full run in their own room. Then you perform it and make one deliberate mistake to catch.",
       "The learner stands, sweeps, points, and walks, saying all five anchors in order.",
       "You point at one chair and name it. Which anchor do you use?",
       "זֶה — zeh",
       "Pointing at one named thing is zeh (or zot for a feminine thing). If any anchor slips, return to that unit and run its body movement again.",
       ["אֲנִי — ani", "יֵשׁ — yesh", "זֶה — zeh", "הוֹלֵךְ — holech"]),
    ])


# ────────────────────────────────────────────── MANDARIN ──────────────────────────────────────────
ZH = cube("zh", "cubo_zh",
    "Speech track for learning MANDARIN CHINESE by the cube — five embodied anchors in the learner's "
    "own room. English is the instruction; each phrase is given as  characters — pinyin — English. The "
    "marks over the pinyin vowels are the four tones: say them as written. Counting a thing needs a "
    "small \"measure word\" between the number and the noun; the examples show it. Status: DRAFT, "
    "pending author review.",
    [
     U("cubo_zh", 1, "cubo_zh_iam", "我在 — where I stand",
       "Wǒ (我) means \"I\"; zài (在) means \"am at / in\". Stand in the middle of your room and say: "
       "Wǒ zài zhèlǐ — I am here. Zài holds a person in a place.",
       ["我在这里 — wǒ zài zhèlǐ — I am here.",
        "我在家 — wǒ zài jiā — I am at home.",
        "我在厨房 — wǒ zài chúfáng — I am in the kitchen."],
       "我在这里 — wǒ zài zhèlǐ",
       "Stand in the center, point to yourself, say Wǒ zài zhèlǐ. Walk to the door and say it again.",
       "Wǒ zài zhèlǐ. Now I walk to the door. Wǒ zài zhèlǐ. Same words, new spot.",
       "Name a place. The learner walks there and says Wǒ zài plus the place.",
       "You say: chúfáng (kitchen). The learner walks there and says: Wǒ zài chúfáng.",
       "You are standing in the kitchen. Which is true?",
       "我在厨房 — wǒ zài chúfáng",
       "Only one answer matches where the body actually is. Zài is the word that holds you in a place.",
       ["我在厨房 — wǒ zài chúfáng", "我在床上 — wǒ zài chuáng shàng (on the bed)",
        "我去厨房 — wǒ qù chúfáng (I go to the kitchen)"]),
     U("cubo_zh", 2, "cubo_zh_thereis", "有 — what exists in the space",
       "Yǒu (有) means \"there is / there are\" — the same word for one or many. Counting a thing needs "
       "a measure word: 一张 yì zhāng for a flat thing like a table, 两把 liǎng bǎ for two handled "
       "things like chairs. Look around and name what is there.",
       ["有一张桌子 — yǒu yì zhāng zhuōzi — There is a table.",
        "有两把椅子 — yǒu liǎng bǎ yǐzi — There are two chairs.",
        "有水 — yǒu shuǐ — There is water."],
       "有一张桌子，有两把椅子 — yǒu yì zhāng zhuōzi, yǒu liǎng bǎ yǐzi",
       "Sweep your hand across the room and name three things with Yǒu — do not point at one.",
       "Yǒu yì zhāng zhuōzi. Yǒu liǎng bǎ yǐzi. Yǒu yí ge mén (there is a door).",
       "The learner finds something and says Yǒu plus the thing. Keep going to five.",
       "The learner sees the window and says: Yǒu yí shàn chuānghu.",
       "There are two chairs in the room. Which is true?",
       "有两把椅子 — yǒu liǎng bǎ yǐzi",
       "Wǒ zài is only for where I stand. Things that simply exist take Yǒu. For two, use 两 liǎng, not 二 èr.",
       ["有两把椅子 — yǒu liǎng bǎ yǐzi", "我是两把椅子 — wǒ shì liǎng bǎ yǐzi (I am two chairs)",
        "我去两把椅子 — wǒ qù liǎng bǎ yǐzi (I go two chairs)"]),
     U("cubo_zh", 3, "cubo_zh_thisis", "这是 — pointing at one thing",
       "Zhè shì (这是) means \"this is\" — it walks up to one thing, points, and names it. Yǒu says a "
       "thing exists somewhere; zhè shì points right at it.",
       ["这是一张桌子 — zhè shì yì zhāng zhuōzi — This is a table.",
        "这是我的狗 — zhè shì wǒ de gǒu — This is my dog.",
        "这很大 — zhè hěn dà — This is big."],
       "这是一把椅子 — zhè shì yì bǎ yǐzi",
       "Point directly at one object and name it with Zhè shì. Then point at another.",
       "Zhè shì yì zhāng zhuōzi. Zhè shì yì bǎ yǐzi. Zhè shì wǒ de bēizi (this is my cup).",
       "Point at an object; the learner names it with Zhè shì. Then the learner points and you name it.",
       "You point at the dog. The learner says: Zhè shì gǒu.",
       "You point at a dog. Which is true?",
       "这是狗 — zhè shì gǒu",
       "The test is the pointing finger. If you can point at the one thing you mean, the words are Zhè shì.",
       ["这是狗 — zhè shì gǒu", "有这里 — yǒu zhèlǐ (there is here)",
        "我是狗 — wǒ shì gǒu (I am a dog)"]),
     U("cubo_zh", 4, "cubo_zh_igo", "我去 — the arrow of movement",
       "Wǒ qù (我去) means \"I go\". It is the arrow from where you stand to where you will be: Wǒ qù "
       "ménkǒu — I go to the door. When the arrow finishes, it becomes Wǒ zài again: Wǒ zài ménkǒu.",
       ["我去厨房 — wǒ qù chúfáng — I go to the kitchen.",
        "我去门口 — wǒ qù ménkǒu — I go to the door.",
        "我在门口 — wǒ zài ménkǒu — I am at the door."],
       "我去门口 — wǒ qù ménkǒu",
       "Say Wǒ qù plus a place, then walk there. On arrival, stop and say Wǒ zài plus the place. Show the flip.",
       "Wǒ qù ménkǒu. I walk. I arrive. Wǒ zài ménkǒu.",
       "Call a destination. The learner says Wǒ qù plus the place, walks there, and on arrival says Wǒ zài plus the place.",
       "You say: chúfáng. The learner says Wǒ qù chúfáng, walks, and says Wǒ zài chúfáng.",
       "You are walking to the door right now. Which is true?",
       "我去门口 — wǒ qù ménkǒu",
       "While the feet move, the words are qù (go). When the feet stop, they flip to zài (am at).",
       ["我去门口 — wǒ qù ménkǒu", "我是门 — wǒ shì mén (I am a door)",
        "有门 — yǒu mén (there is a door)"]),
     U("cubo_zh", 5, "cubo_zh_path", "从、经过、到 — the three parts of the path",
       "Every arrow has three parts. Cóng (从) is where it starts, jīngguò (经过) is the space it "
       "passes through, dào (到) is where it ends. In Chinese the whole path is said before the verb. "
       "Walk it and say it.",
       ["我从厨房到门口 — wǒ cóng chúfáng dào ménkǒu — I go from the kitchen to the door.",
        "我经过走廊 — wǒ jīngguò zǒuláng — I go through the hall.",
        "我从椅子到桌子 — wǒ cóng yǐzi dào zhuōzi — from the chair to the table."],
       "我从厨房，经过走廊，到门口 — wǒ cóng chúfáng, jīngguò zǒuláng, dào ménkǒu",
       "Announce your start with cóng, the middle with jīngguò, the arrival with dào — narrate each as your body reaches it.",
       "Wǒ cóng chúfáng... jīngguò zǒuláng... dào ménkǒu. Wǒ zài ménkǒu.",
       "Give the learner a start and an end. The learner walks it, saying all three parts in order.",
       "From the chair to the window. The learner says: Wǒ cóng yǐzi, jīngguò zǒuláng, dào chuānghu.",
       "Put the path words in order from start to finish.",
       "从、经过、到 — cóng, jīngguò, dào",
       "Cóng starts, jīngguò carries, dào lands. If they mix, walk the path slowly and say each word in its part.",
       ["从、经过、到 — cóng, jīngguò, dào", "到、经过、从 — dào, jīngguò, cóng",
        "经过、从、到 — jīngguò, cóng, dào"]),
     U("cubo_zh", 6, "cubo_zh_review", "复习 — the whole cube in one breath",
       "Now run the whole cube in Mandarin. Stand: wǒ zài. Look around: yǒu. Point: zhè shì. Move: wǒ "
       "qù, with cóng, jīngguò, dào marking the path. Five anchors, one room, one breath.",
       ["我在这里 — wǒ zài zhèlǐ — I am here.",
        "有一张桌子 — yǒu yì zhāng zhuōzi — There is a table.",
        "这是我的椅子 — zhè shì wǒ de yǐzi — This is my chair.",
        "我从椅子到门口 — wǒ cóng yǐzi dào ménkǒu — from the chair to the door."],
       "我在这里。有一张桌子。这是我的椅子。我从椅子，经过走廊，到门口。",
       "Perform the full sequence with your body: stand and say wǒ zài, sweep and say yǒu, point and say zhè shì, then walk saying wǒ cóng, jīngguò, dào.",
       "Wǒ zài zhèlǐ. Yǒu yì zhāng zhuōzi hé liǎng bǎ yǐzi. Zhè shì wǒ de bēizi. Wǒ cóng zhuōzi, jīngguò zǒuláng, dào ménkǒu. Wǒ zài ménkǒu.",
       "The learner performs the full run in their own room. Then you perform it and make one deliberate mistake to catch.",
       "The learner stands, sweeps, points, and walks, saying all five anchors in order.",
       "You point at one chair and name it. Which anchor do you use?",
       "这是 — zhè shì",
       "Pointing at one named thing is always Zhè shì. If any anchor slips, return to that unit and run its body movement again.",
       ["我在 — wǒ zài", "有 — yǒu", "这是 — zhè shì", "我去 — wǒ qù"]),
    ])


# ─────────────────────────────────────────── BIBLICAL GREEK ───────────────────────────────────────
GR = cube("grc", "cubo_grc",
    "Speech track for learning BIBLICAL (Koine) GREEK by the cube — five embodied anchors in the "
    "learner's own room, in the tongue of the New Testament. English is the instruction; each Greek "
    "phrase is given as  Greek — romanization — English. Greek marks a word's job by its ENDING, so "
    "the same noun changes shape as it moves through the path; the article (the word for \"the\") "
    "changes with it. The verb often carries \"I\" already, so the pronoun can be dropped. The words "
    "are the everyday nouns of the room, chosen where the New Testament itself uses them. Status: "
    "DRAFT, pending author review.",
    [
     U("cubo_grc", 1, "cubo_grc_iam", "εἰμί — where I stand",
       "Eimi (εἰμί) means \"I am\" — the verb already says \"I\", so no separate word for \"I\" is "
       "needed. Stand in the middle of your room and say: ὧδέ εἰμι (hōde eimi) — I am here. Hōde means "
       "\"here\".",
       ["ὧδέ εἰμι — hōde eimi — I am here.",
        "ἐν τῷ οἴκῳ εἰμί — en tō oikō eimi — I am in the house.",
        "ἐν τῷ ταμείῳ εἰμί — en tō tameiō eimi — I am in the room."],
       "ὧδέ εἰμι — hōde eimi",
       "Stand in the center, point to yourself, say hōde eimi. Walk to the door and say it again — the verb carries the \"I\".",
       "Hōde eimi. Now I walk to the door. Hōde eimi. Same words, new spot.",
       "Name a place. The learner walks there and says en tō plus the place plus eimi.",
       "You say: oikos (house). The learner walks there and says: en tō oikō eimi.",
       "You are standing in the room. Which is true?",
       "ἐν τῷ ταμείῳ εἰμί — en tō tameiō eimi",
       "Only one answer matches where the body actually is. Eimi already means \"I am\" — no separate \"I\" is needed.",
       ["ἐν τῷ ταμείῳ εἰμί — en tō tameiō eimi", "ἐν τῇ ὁδῷ εἰμί — en tē hodō eimi (on the road)",
        "ὑπάγω εἰς τὸ ταμεῖον — hypagō eis to tameion (I go into the room)"]),
     U("cubo_grc", 2, "cubo_grc_thereis", "ἔστιν / εἰσίν — what exists in the space",
       "Estin (ἔστιν) means \"there is\" for one thing; eisin (εἰσίν) means \"there are\" for many. Look "
       "around the room and name what is there.",
       ["ἔστι τράπεζα — esti trapeza — There is a table.",
        "εἰσὶ δύο καθέδραι — eisi dyo kathedrai — There are two seats.",
        "ἔστιν ὕδωρ — estin hydōr — There is water."],
       "ἔστι τράπεζα καὶ εἰσὶ δύο καθέδραι — esti trapeza kai eisi dyo kathedrai",
       "Sweep your hand across the room. Use estin for one thing, eisin for many.",
       "Esti trapeza. Eisi dyo kathedrai. Esti thyra (there is a door).",
       "The learner finds one thing (estin) or several (eisin) and names them. Keep going to five.",
       "The learner sees the water and says: estin hydōr.",
       "There are two seats in the room. Which is true?",
       "εἰσὶ δύο καθέδραι — eisi dyo kathedrai",
       "One thing takes estin; many take eisin. Eimi is only for where I stand.",
       ["εἰσὶ δύο καθέδραι — eisi dyo kathedrai", "δύο καθέδραι εἰμί — dyo kathedrai eimi (I am two seats)",
        "ὑπάγω δύο καθέδραι — hypagō dyo kathedrai (I go two seats)"]),
     U("cubo_grc", 3, "cubo_grc_thisis", "οὗτος / αὕτη / τοῦτο — pointing at one thing",
       "\"This is\" points at one thing and names it. Greek fits the word for \"this\" to the thing: "
       "houtos (οὗτος) for a masculine thing, hautē (αὕτη) for a feminine one, touto (τοῦτο) for a "
       "neuter one. Point, then name.",
       ["αὕτη ἐστὶ τράπεζα — hautē esti trapeza — This is a table. (table is feminine)",
        "τοῦτό ἐστι τὸ βιβλίον μου — touto esti to biblion mou — This is my book. (book is neuter)",
        "οὗτός ἐστιν ὁ ἄρτος — houtos estin ho artos — This is the bread. (bread is masculine)"],
       "αὕτη ἐστὶ καθέδρα — hautē esti kathedra",
       "Point at one object and name it, fitting houtos / hautē / touto to the thing. Then point at another.",
       "Hautē esti trapeza. Hautē esti kathedra. Touto esti to biblion mou.",
       "Point at an object; the learner names it with houtos, hautē, or touto plus esti. Then switch.",
       "You point at the bread (artos, masculine). The learner says: houtos estin ho artos.",
       "You point at the bread (ὁ ἄρτος, masculine). Which is true?",
       "οὗτός ἐστιν ὁ ἄρτος — houtos estin ho artos",
       "The word for \"this\" fits the thing: houtos (masc.), hautē (fem.), touto (neut.). The pointing finger tells you it is a \"this is\".",
       ["οὗτός ἐστιν ὁ ἄρτος — houtos estin ho artos", "ἔστιν ὧδε — estin hōde (there is here)",
        "ἄρτος εἰμί — artos eimi (I am bread)"]),
     U("cubo_grc", 4, "cubo_grc_igo", "ὑπάγω — the arrow of movement",
       "Hypagō (ὑπάγω) means \"I go\". It is the arrow from where you stand to where you will be: "
       "ὑπάγω πρὸς τὴν θύραν — I go to the door. When the arrow finishes, it becomes eimi again: νῦν "
       "ὧδέ εἰμι — now I am here. Notice that after pros, ἡ θύρα becomes τὴν θύραν.",
       ["ὑπάγω εἰς τὸν οἶκον — hypagō eis ton oikon — I go into the house.",
        "ὑπάγω πρὸς τὴν θύραν — hypagō pros tēn thyran — I go to the door.",
        "νῦν ὧδέ εἰμι — nyn hōde eimi — Now I am here."],
       "ὑπάγω πρὸς τὴν θύραν — hypagō pros tēn thyran",
       "Say hypagō pros plus a place, then walk there. On arrival, stop and say nyn hōde eimi. Show the flip.",
       "Hypagō pros tēn thyran. I walk. I arrive. Nyn hōde eimi.",
       "Call a destination. The learner says hypagō pros plus the place, walks there, and on arrival says nyn hōde eimi.",
       "You say: thyra (door). The learner says hypagō pros tēn thyran, walks, and says nyn hōde eimi.",
       "You are walking to the door right now. Which is true?",
       "ὑπάγω πρὸς τὴν θύραν — hypagō pros tēn thyran",
       "While the feet move, the word is hypagō. When the feet stop, you are there: eimi. After pros, thyra changes to thyran.",
       ["ὑπάγω πρὸς τὴν θύραν — hypagō pros tēn thyran", "θύρα εἰμί — thyra eimi (I am a door)",
        "ἔστι θύρα — esti thyra (there is a door)"]),
     U("cubo_grc", 5, "cubo_grc_path", "ἀπό, διά, πρός — the three parts of the path",
       "Every arrow has three parts. Apo (ἀπό) is where it starts, dia (διά) is the space it passes "
       "through, pros (πρός) is where it ends. Each one changes the noun's ending: ἀπὸ τοῦ οἴκου, διὰ "
       "τῆς θύρας, πρὸς τὴν τράπεζαν.",
       ["ἀπὸ τοῦ οἴκου πρὸς τὴν θύραν — apo tou oikou pros tēn thyran — from the house to the door.",
        "διὰ τῆς θύρας — dia tēs thyras — through the door.",
        "ἀπὸ τῆς καθέδρας πρὸς τὴν τράπεζαν — apo tēs kathedras pros tēn trapezan — from the seat to the table."],
       "ἀπὸ τοῦ οἴκου, διὰ τῆς θύρας, πρὸς τὴν τράπεζαν — apo tou oikou, dia tēs thyras, pros tēn trapezan",
       "Announce your start with apo, the middle with dia, the arrival with pros — narrate each as your body reaches it.",
       "Apo tou oikou... dia tēs thyras... pros tēn trapezan. Nyn hōde eimi.",
       "Give the learner a start and an end. The learner walks it, saying all three parts in order.",
       "From the seat to the door. The learner says: apo tēs kathedras, dia tēs thyras, pros tēn thyran.",
       "Put the path words in order from start to finish.",
       "ἀπό, διά, πρός — apo, dia, pros",
       "Apo starts, dia carries, pros lands. Each changes the noun after it — walk the path slowly and say each word in its part.",
       ["ἀπό, διά, πρός — apo, dia, pros", "πρός, διά, ἀπό — pros, dia, apo",
        "διά, ἀπό, πρός — dia, apo, pros"]),
     U("cubo_grc", 6, "cubo_grc_review", "ἀνακεφαλαίωσις — the whole cube in one breath",
       "Now run the whole cube in Greek. Stand: eimi. Look around: estin / eisin. Point: houtos, "
       "hautē, touto esti. Move: hypagō, with apo, dia, pros marking the path. Five anchors, one room, "
       "one breath.",
       ["ὧδέ εἰμι — hōde eimi — I am here.",
        "ἔστι τράπεζα — esti trapeza — There is a table.",
        "αὕτη ἐστὶ ἡ καθέδρα μου — hautē esti hē kathedra mou — This is my seat.",
        "ὑπάγω ἀπὸ τῆς καθέδρας πρὸς τὴν θύραν — hypagō apo tēs kathedras pros tēn thyran — from the seat to the door."],
       "ὧδέ εἰμι. ἔστι τράπεζα. αὕτη ἐστὶ ἡ καθέδρα μου. ὑπάγω ἀπὸ τῆς καθέδρας, διὰ τῆς θύρας, πρὸς τὴν τράπεζαν.",
       "Perform the full sequence with your body: stand and say eimi, sweep and say estin / eisin, point and say houtos/hautē/touto esti, then walk saying hypagō with apo, dia, pros.",
       "Hōde eimi. Esti trapeza kai eisi dyo kathedrai. Touto esti to biblion mou. Hypagō apo tēs trapezēs, dia tēs thyras, pros ton oikon. Nyn hōde eimi.",
       "The learner performs the full run in their own room. Then you perform it and make one deliberate mistake to catch.",
       "The learner stands, sweeps, points, and walks, saying all five anchors in order.",
       "You point at one seat (καθέδρα, feminine) and name it. Which anchor do you use?",
       "αὕτη ἐστί — hautē esti",
       "Pointing at one named thing is always houtos / hautē / touto esti, fitted to the thing. A feminine kathedra takes hautē.",
       ["εἰμί — eimi", "ἔστιν — estin", "αὕτη ἐστί — hautē esti", "ὑπάγω — hypagō"]),
    ])


def main():
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — already utf-8, or no buffer (imported): harmless
        pass
    OUT.mkdir(parents=True, exist_ok=True)
    for c in (FR, DE, LA, HE, ZH, GR):
        path = OUT / (c["subject"] + "_en.json")
        path.write_text(json.dumps(c["units"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  {c['subject']}: wrote {len(c['units'])} units → {path}")
    print("done.")


if __name__ == "__main__":
    main()
