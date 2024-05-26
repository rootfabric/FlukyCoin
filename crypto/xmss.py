# from WOTS import *
import datetime
from typing import List
import json
import base58
import base64
import struct
import pickle
import zlib
from random import choice, seed, randint
from string import ascii_letters, digits
from hashlib import sha256
import hashlib
from math import floor, log2, log, ceil
# from WOTS import *
import datetime
from typing import List
import json
import base58
import base64
import struct
import pickle
import zlib
from random import choice, seed, randint
from string import ascii_letters, digits
from hashlib import sha256
from math import floor, log2, log, ceil

#
word_list =[
        "aback", "abbey", "abbot", "abide", "ablaze", "able", "aboard", "abode", "abort", "abound", "about", "above",
        "abra", "abroad", "abrupt", "absent", "absorb", "absurd", "accent", "accept", "access", "accord", "accuse",
        "ace",
        "ache", "aching", "acid", "acidic", "acorn", "acre", "across", "act", "action", "active", "actor", "actual",
        "acute", "adam", "adapt", "add", "added", "adept", "adhere", "adjust", "admire", "admit", "adobe", "adopt",
        "adrift", "adverb", "advert", "aedes", "aerial", "afar", "affair", "affect", "afford", "afghan", "afield",
        "afloat",
        "afraid", "afresh", "after", "again", "age", "agency", "agenda", "agent", "aghast", "agile", "ago", "agony",
        "agree", "agreed", "aha", "ahead", "aid", "aide", "aim", "air", "airman", "airy", "akin", "alarm",
        "alaska", "albeit", "album", "alert", "alibi", "alice", "alien", "alight", "align", "alike", "alive", "alkali",
        "all", "allars", "allay", "alley", "allied", "allot", "allow", "alloy", "ally", "almond", "almost", "aloft",
        "alone", "along", "aloof", "aloud", "alpha", "alpine", "also", "altar", "alter", "always", "amaze", "amazon",
        "amber", "ambush", "amen", "amend", "amid", "amidst", "amiss", "among", "amount", "ample", "amuse", "anchor",
        "and", "andrew", "anew", "angel", "anger", "angle", "anglo", "angola", "animal", "ankle", "annoy", "annual",
        "answer", "anthem", "anti", "antony", "anubis", "any", "anyhow", "anyway", "apart", "apathy", "apex", "apiece",
        "appeal", "appear", "apple", "apply", "april", "apron", "arcade", "arcane", "arch", "arctic", "ardent", "are",
        "area", "argue", "arid", "arise", "arm", "armful", "armpit", "army", "aroma", "around", "arouse", "array",
        "arrest", "arrive", "arrow", "arson", "art", "artery", "artful", "artist", "ascent", "ashen", "ashore", "aside",
        "ask", "asleep", "aspect", "assay", "assent", "assert", "assess", "asset", "assign", "assist", "assume",
        "assure",
        "asthma", "astute", "asylum", "ate", "athens", "atlas", "atom", "atomic", "atop", "attach", "attain", "attend",
        "attic", "auburn", "audio", "audit", "augite", "august", "aunt", "auntie", "aura", "austin", "auteur", "author",
        "auto", "autumn", "avail", "avenge", "avenue", "avert", "avid", "avoid", "await", "awake", "awaken", "award",
        "aware", "awash", "away", "awful", "awhile", "axes", "axiom", "axis", "axle", "aye", "baby", "bach",
        "back", "backup", "bacon", "bad", "badge", "badly", "bag", "baggy", "bail", "bait", "bake", "baker",
        "bakery", "bald", "ball", "ballad", "ballet", "ballot", "baltic", "bamboo", "ban", "banal", "banana", "band",
        "banjo", "bank", "bar", "barber", "bare", "barely", "barge", "baric", "bark", "barley", "barn", "baron",
        "barrel", "barren", "basalt", "base", "basic", "basil", "basin", "basis", "basket", "basque", "bass", "bat",
        "batch", "bath", "bathe", "baton", "battle", "bay", "beach", "beacon", "beak", "beam", "bean", "bear",
        "beard", "beat", "beauty", "become", "bed", "beech", "beef", "beefy", "beep", "beer", "beet", "beetle",
        "before", "beggar", "begin", "behalf", "behave", "behind", "beige", "being", "belfry", "belief", "bell",
        "belly",
        "belong", "below", "belt", "bench", "bend", "bended", "benign", "bent", "berlin", "berry", "berth", "beset",
        "beside", "best", "bestow", "bet", "beta", "betray", "better", "betty", "beware", "beyond", "bias", "biceps",
        "bicker", "bid", "big", "bike", "bile", "bill", "binary", "bind", "biopsy", "birch", "bird", "birdie",
        "birth", "bishop", "bit", "bite", "bitter", "blade", "blame", "bland", "blaser", "blast", "blaze", "bleak",
        "blend", "bless", "blew", "blink", "blip", "bliss", "blitz", "block", "blond", "blood", "bloom", "blot",
        "blouse", "blue", "bluff", "blunt", "blur", "blush", "boar", "board", "boast", "boat", "bocage", "bodily",
        "body", "bogus", "boil", "bold", "bolt", "bombay", "bond", "bone", "bonn", "bonnet", "bonus", "bony",
        "book", "boost", "boot", "booth", "booze", "bop", "border", "bore", "borrow", "bosom", "boss", "boston",
        "both", "bother", "bottle", "bottom", "bought", "bounce", "bound", "bounty", "bout", "bovine", "bow", "bowel",
        "bowl", "box", "boy", "boyish", "brace", "brain", "brainy", "brake", "bran", "branch", "brand", "brandy",
        "brass", "brave", "bravo", "brazil", "breach", "bread", "break", "breath", "bred", "breed", "breeze", "brew",
        "brick", "bride", "bridge", "brief", "bright", "brim", "brine", "bring", "brink", "brisk", "briton", "broad",
        "broke", "broken", "bronze", "brook", "broom", "brown", "bruise", "brush", "brutal", "brute", "bubble", "buck",
        "bucket", "buckle", "buddha", "budget", "buen", "buffet", "buggy", "build", "bulb", "bulge", "bulk", "bulky",
        "bull", "bullet", "bully", "bump", "bumpy", "bunch", "bundle", "bunk", "bunny", "burden", "bureau", "burial",
        "burly", "burma", "burned", "burnt", "burrow", "burst", "bury", "bus", "bush", "bust", "bustle", "busy",
        "but", "butler", "butter", "button", "buy", "buyer", "buzz", "bye", "byte", "byways", "cab", "cabin",
        "cable", "cache", "cactus", "caesar", "cage", "cagey", "cahot", "cain", "cairo", "cake", "cakile", "calf",
        "call", "caller", "calm", "calmly", "came", "camel", "camera", "camp", "campus", "can", "canada", "canary",
        "cancel", "candid", "candle", "candy", "cane", "canine", "canna", "canoe", "canopy", "canvas", "canyon", "cap",
        "cape", "car", "carbon", "card", "care", "career", "caress", "cargo", "carl", "carnal", "carol", "carp",
        "carpet", "carrot", "carry", "cart", "cartel", "case", "cash", "cask", "cast", "castle", "casual", "cat",
        "catch", "cater", "cattle", "caught", "causal", "cause", "cave", "cease", "celery", "cell", "cellar", "celtic",
        "cement", "censor", "census", "cereal", "cervix", "chain", "chair", "chalet", "chalk", "chalky", "champ",
        "chance",
        "change", "chant", "chaos", "chap", "chapel", "charge", "charm", "chart", "chase", "chat", "cheap", "cheat",
        "check", "cheek", "cheeky", "cheer", "cheery", "cheese", "chef", "cherry", "chess", "chest", "chew", "chic",
        "chick", "chief", "child", "chile", "chill", "chilly", "china", "chip", "choice", "choir", "choose", "chop",
        "choppy", "chord", "chorus", "chose", "chosen", "choux", "chrome", "chunk", "chunky", "cider", "cigar",
        "cinema",
        "circa", "circle", "circus", "cite", "city", "civic", "civil", "clad", "claim", "clammy", "clan", "clap",
        "clash", "clasp", "class", "clause", "claw", "clay", "clean", "clear", "clergy", "clerk", "clever", "click",
        "client", "cliff", "climax", "climb", "clinch", "cling", "clinic", "clip", "cloak", "clock", "clone", "close",
        "closer", "closet", "cloth", "cloud", "cloudy", "clout", "clown", "club", "clue", "clumsy", "clung", "clutch",
        "coach", "coal", "coast", "coat", "coax", "cobalt", "cobble", "cobra", "coca", "cocoa", "code", "coffee",
        "coffin", "cohort", "coil", "coin", "coke", "cold", "collar", "colon", "colony", "colt", "column", "comb",
        "combat", "come", "comedy", "comes", "comic", "commit", "common", "compel", "comply", "concur", "cone",
        "confer",
        "congo", "consul", "convex", "convey", "convoy", "cook", "cool", "cope", "copper", "copy", "coral", "cord",
        "core", "cork", "corn", "corner", "corps", "corpse", "corpus", "cortex", "cosmic", "cosmos", "cost", "costia",
        "costly", "cosy", "cotton", "couch", "cough", "could", "count", "county", "coup", "couple", "coupon", "course",
        "court", "cousin", "cove", "cover", "covert", "cow", "coward", "cowboy", "crab", "cradle", "craft", "crafty",
        "crag", "crane", "crate", "crater", "crawl", "crazy", "creak", "cream", "create", "credit", "creed", "creek",
        "creep", "creepy", "creole", "crept", "crest", "crew", "cried", "crisis", "crisp", "critic", "croft", "crook",
        "crop", "cross", "crow", "crowd", "crown", "crude", "cruel", "cruise", "crunch", "crush", "crust", "crux",
        "cry", "crypt", "cuba", "cube", "cubic", "cuckoo", "cuff", "cult", "cup", "curb", "cure", "curfew",
        "curl", "curlew", "curry", "curse", "cursor", "curve", "custom", "cut", "cute", "cycle", "cyclic", "cynic",
        "cyprus", "czech", "dad", "daddy", "dagger", "daily", "dairy", "daisy", "dale", "dallas", "damage", "damp",
        "dampen", "dance", "danger", "daniel", "danish", "dare", "dark", "darken", "darwin", "dash", "data", "date",
        "david", "dawn", "day", "deadly", "deaf", "deal", "dealer", "dean", "dear", "debar", "debate", "debit",
        "debris", "debt", "debtor", "decade", "decay", "decent", "decide", "deck", "decor", "decree", "deduce", "deed",
        "deep", "deeply", "deer", "defeat", "defect", "defend", "defer", "define", "defy", "degree", "deity", "delay",
        "delete", "delhi", "delphi", "delta", "demand", "demise", "demo", "demure", "denial", "denote", "dense",
        "dental",
        "deny", "depart", "depend", "depict", "deploy", "depot", "depth", "deputy", "derby", "derive", "desert",
        "design",
        "desist", "desk", "detail", "detect", "deter", "detest", "detour", "device", "devise", "devoid", "devote",
        "devour",
        "dial", "diana", "diary", "dice", "dictum", "did", "diesel", "diet", "differ", "digest", "digit", "dine",
        "dinghy", "dingus", "dinner", "diode", "dire", "direct", "dirt", "disc", "disco", "dish", "disk", "dismal",
        "dispel", "ditch", "divert", "divide", "divine", "dizzy", "docile", "dock", "doctor", "dog", "dogger", "dogma",
        "dole", "doll", "dollar", "dolly", "domain", "dome", "domino", "donate", "done", "donkey", "donor", "door",
        "dorsal", "dose", "dote", "double", "doubt", "dough", "dour", "dove", "dower", "down", "dozen", "draft",
        "drag", "dragon", "drain", "drama", "drank", "draper", "draw", "drawer", "dread", "dream", "dreamy", "dreary",
        "dress", "drew", "dried", "drift", "drill", "drink", "drip", "drive", "driver", "drool", "drop", "drove",
        "drown", "drum", "dry", "dual", "dublin", "duck", "duct", "due", "duel", "duet", "duke", "dull",
        "duly", "dummy", "dump", "dune", "dung", "duress", "during", "dusk", "dust", "dusty", "dutch", "duty",
        "dwarf", "dwell", "dyer", "dying", "dynamo", "each", "eager", "eagle", "ear", "earl", "early", "earn",
        "earth", "ease", "easel", "easily", "east", "easter", "easy", "eat", "eaten", "eater", "echo", "eddy",
        "eden", "edge", "edible", "edict", "edit", "editor", "edward", "eerie", "eerily", "effect", "effort", "egg",
        "ego", "egypt", "eight", "eighth", "eighty", "either", "elbow", "elder", "eldest", "elect", "eleven", "elicit",
        "elite", "eloge", "else", "elude", "elves", "embark", "emblem", "embryo", "emerge", "emit", "empire", "employ",
        "empty", "enable", "enamel", "end", "endure", "energy", "engage", "engine", "enjoy", "enlist", "enough",
        "ensure",
        "entail", "enter", "entire", "entre", "entry", "envoy", "envy", "enzyme", "epic", "epoch", "equal", "equate",
        "equip", "equity", "era", "erase", "eric", "erode", "erotic", "errant", "error", "escape", "essay", "essex",
        "estate", "esteem", "ethic", "etoile", "eundo", "europe", "evade", "eve", "even", "event", "ever", "every",
        "evict", "evil", "evoke", "evolve", "exact", "exam", "exceed", "excel", "except", "excess", "excise", "excite",
        "excuse", "exempt", "exert", "exile", "exist", "exit", "exodus", "exotic", "expand", "expect", "expert",
        "expire",
        "export", "expose", "extend", "extra", "exulat", "eye", "eyed", "fabric", "face", "facer", "facial", "fact",
        "factor", "fade", "fail", "faint", "fair", "fairly", "fake", "falcon", "fall", "false", "falter", "fame",
        "family", "famine", "famous", "fan", "fancy", "far", "farce", "fare", "farm", "farmer", "fast", "fasten",
        "faster", "fatal", "fate", "father", "fatty", "fault", "faulty", "fauna", "feast", "feat", "fed", "fee",
        "feeble", "feed", "feel", "feels", "feet", "fell", "fellow", "felt", "female", "femur", "fence", "fend",
        "ferry", "fetal", "fetch", "feudal", "fever", "few", "fewer", "fiance", "fiasco", "fiddle", "field", "fiend",
        "fierce", "fiery", "fifth", "fifty", "fig", "figure", "file", "fill", "filled", "filler", "film", "filter",
        "filth", "filthy", "final", "finale", "find", "fine", "finish", "finite", "firm", "firmly", "first", "fiscal",
        "fish", "fisher", "fit", "fitful", "five", "fix", "flag", "flair", "flak", "flame", "flank", "flare",
        "flash", "flask", "flat", "flaw", "fled", "flee", "fleece", "fleet", "flesh", "fleshy", "flew", "flick",
        "flight", "flimsy", "flint", "flirt", "float", "flock", "floe", "flood", "floor", "floppy", "flora", "floral",
        "flour", "flow", "flower", "fluent", "fluffy", "fluid", "flung", "flurry", "flush", "flute", "flux", "fly",
        "flyer", "foal", "foam", "foamy", "focal", "focus", "fog", "foil", "foin", "fold", "folk", "follow",
        "folly", "fond", "fondly", "font", "food", "fool", "foot", "for", "forbid", "force", "ford", "forest",
        "forge", "forget", "fork", "form", "formal", "format", "former", "fort", "forth", "forty", "forum", "fossil",
        "foster", "foul", "found", "four", "fourth", "fox", "foyer", "frail", "frame", "franc", "france", "frank",
        "free", "freed", "freely", "freer", "freeze", "french", "frenzy", "fresh", "friar", "friday", "fridge", "fried",
        "friend", "fright", "fringe", "frock", "frog", "from", "front", "frost", "frosty", "frown", "frozen", "frugal",
        "fruit", "fruity", "fudge", "fuel", "fulfil", "full", "fully", "fun", "fund", "funny", "fur", "furry",
        "fury", "fuse", "fusion", "fuss", "fussy", "futile", "future", "fuzzy", "gadget", "gag", "gain", "gala",
        "galaxy", "gale", "gall", "galley", "gallon", "gallop", "gamble", "game", "gamma", "gandhi", "gap", "garage",
        "garden", "garlic", "gas", "gasp", "gate", "gather", "gaucho", "gauge", "gaul", "gaunt", "gave", "gaze",
        "gear", "geese", "gemini", "gender", "gene", "geneva", "genial", "genius", "genre", "gentle", "gently",
        "gentry",
        "genus", "george", "get", "ghetto", "ghost", "giant", "gift", "giggle", "gill", "gilt", "ginger", "girl",
        "give", "given", "glad", "glade", "glance", "gland", "glare", "glass", "glassy", "gleam", "glee", "glib",
        "glide", "global", "globe", "gloom", "gloomy", "gloria", "glory", "gloss", "glossy", "glove", "glow", "glue",
        "goal", "goat", "gold", "golden", "golf", "gone", "gong", "good", "goose", "gorge", "gory", "gosh",
        "gospel", "gossip", "got", "gothic", "govern", "gown", "grab", "grace", "grade", "grain", "grand", "grant",
        "grape", "graph", "grasp", "grass", "grassy", "grate", "grave", "gravel", "gravy", "gray", "grease", "greasy",
        "great", "greece", "greed", "greedy", "greek", "green", "greet", "grew", "grey", "grid", "grief", "grill",
        "grim", "grin", "grind", "grip", "grit", "gritty", "groan", "groin", "groom", "groove", "ground", "group",
        "grove", "grow", "grown", "growth", "grudge", "grunt", "guard", "guess", "guest", "guide", "guild", "guilt",
        "guilty", "guise", "guitar", "gulf", "gully", "gunman", "guru", "gut", "guy", "gypsy", "habit", "hack",
        "had", "hague", "hail", "hair", "hairy", "haiti", "hale", "half", "hall", "halt", "hamlet", "hammer",
        "hand", "handle", "handy", "hang", "hangar", "hanoi", "happen", "happy", "hard", "hardly", "hare", "harm",
        "harp", "harry", "harsh", "has", "hash", "hassle", "hasta", "haste", "hasten", "hasty", "hat", "hatch",
        "hate", "haul", "haunt", "havana", "have", "haven", "havoc", "hawaii", "hawk", "hawse", "hazard", "haze",
        "hazel", "hazy", "heal", "health", "heap", "hear", "heard", "heart", "hearth", "hearty", "heat", "heater",
        "heaven", "heavy", "hebrew", "heck", "hectic", "hedge", "heel", "hefty", "height", "heil", "heir", "held",
        "helium", "helix", "hello", "helm", "helmet", "help", "hemp", "hence", "henry", "her", "herald", "herb",
        "herd", "here", "hereby", "hermes", "hernia", "hero", "heroic", "hest", "hey", "heyday", "hick", "hidden",
        "hide", "high", "higher", "highly", "hill", "him", "hind", "hindu", "hint", "hippy", "hire", "his",
        "hiss", "hit", "hive", "hoard", "hoarse", "hobby", "hockey", "hold", "holder", "hollow", "holly", "holy",
        "home", "honest", "honey", "hood", "hope", "hopple", "horrid", "horror", "horse", "hose", "host", "hotbox",
        "hotel", "hound", "hour", "house", "hover", "how", "huck", "huge", "hull", "human", "humane", "humble",
        "humid", "hung", "hunger", "hungry", "hunt", "hurdle", "hurl", "hurry", "hurt", "hush", "hut", "hybrid",
        "hymn", "hyphen", "ice", "icing", "icon", "idaho", "idea", "ideal", "idiom", "idle", "idly", "idol",
        "ignite", "ignore", "ill", "image", "immune", "impact", "imply", "import", "impose", "inca", "inch", "income",
        "incur", "indeed", "index", "india", "indian", "indoor", "induce", "inept", "inert", "infant", "infect",
        "infer",
        "influx", "inform", "inhere", "inject", "injure", "injury", "ink", "inlaid", "inland", "inlet", "inmate", "inn",
        "innate", "inner", "input", "insane", "insect", "insert", "inset", "inside", "insist", "insult", "insure",
        "intact",
        "intake", "intend", "inter", "into", "invade", "invent", "invest", "invite", "invoke", "inward", "iowa", "iran",
        "iraq", "irish", "iron", "ironic", "irony", "isaac", "isabel", "islam", "island", "isle", "issue", "italy",
        "item", "itself", "ivan", "ivory", "ivy", "jacket", "jacob", "jaguar", "jail", "james", "japan", "jargon",
        "java", "jaw", "jazz", "jeep", "jelly", "jerky", "jersey", "jest", "jet", "jewel", "jim", "jive",
        "job", "jock", "jockey", "john", "join", "joke", "jolly", "jolt", "jordan", "joseph", "joy", "joyful",
        "joyous", "judas", "judge", "judy", "juice", "juicy", "july", "jumble", "jumbo", "jump", "june", "jungle",
        "junior", "junk", "junta", "jury", "just", "kami", "kansas", "karate", "karl", "karma", "kedge", "keel",
        "keen", "keep", "keeper", "kenya", "kept", "kernel", "kettle", "key", "khaki", "khaya", "khowar", "kick",
        "kidnap", "kidney", "kin", "kind", "kindly", "king", "kiss", "kite", "kitten", "knack", "knaggy", "knee",
        "knew", "knight", "knit", "knock", "knot", "know", "known", "koran", "korea", "kusan", "kuwait", "label",
        "lace", "lack", "lad", "ladder", "laden", "lady", "lagoon", "laity", "lake", "lamb", "lame", "lamp",
        "lance", "land", "lane", "laos", "lap", "lapse", "large", "larval", "laser", "last", "latch", "late",
        "lately", "latent", "later", "latest", "latter", "laugh", "launch", "lava", "lavish", "law", "lawful", "lawn",
        "laws", "lawyer", "lay", "layer", "layman", "lazy", "lead", "leader", "leaf", "leafy", "league", "leak",
        "leaky", "lean", "leap", "learn", "lease", "leash", "least", "leave", "led", "ledge", "left", "leg",
        "legacy", "legal", "legend", "legion", "lemon", "lend", "length", "lens", "lent", "leo", "leper", "lese",
        "lesion", "less", "lessen", "lesser", "lesson", "lest", "let", "lethal", "letter", "letup", "level", "lever",
        "levy", "lewis", "liable", "liar", "libel", "libya", "lice", "lick", "lid", "lie", "lied", "life",
        "lift", "light", "like", "likely", "lima", "limb", "lime", "limit", "limp", "line", "linear", "linen",
        "lineup", "linger", "link", "lion", "lip", "liquid", "lisbon", "list", "listen", "lit", "live", "lively",
        "liver", "livy", "liz", "lizard", "load", "loaf", "loan", "lobby", "lobe", "local", "locate", "lock",
        "locus", "lodge", "loft", "lofty", "log", "logic", "logo", "london", "lone", "lonely", "long", "longer",
        "look", "loop", "loose", "loosen", "loot", "lord", "lorry", "lose", "loss", "lost", "lot", "lotus",
        "loud", "loudly", "lounge", "lousy", "louvre", "love", "lovely", "lover", "low", "lower", "lowest", "loyal",
        "lucid", "luck", "lucky", "lucy", "lukes", "lull", "lump", "lumpy", "lunacy", "lunar", "lunch", "lung",
        "lure", "lurid", "lush", "lusory", "lute", "luther", "luxury", "lying", "lymph", "lyric", "macho", "macro",
        "macte", "madam", "madame", "made", "madrid", "magic", "magma", "magnet", "magnum", "maid", "maiden", "mail",
        "main", "mainly", "major", "make", "maker", "male", "malice", "mall", "malt", "malta", "mammal", "manage",
        "mane", "mania", "manic", "manila", "manner", "manor", "mantle", "manual", "manure", "many", "map", "maple",
        "marble", "march", "mare", "margin", "maria", "marina", "mark", "market", "marry", "mars", "marsh", "martin",
        "martyr", "mary", "mask", "mason", "mass", "mast", "match", "mate", "matrix", "matter", "mature", "maxim",
        "may", "maya", "maybe", "mayor", "maze", "mead", "meadow", "meal", "mean", "meant", "meat", "mecca",
        "medal", "media", "median", "medic", "medium", "meet", "mellow", "melody", "melon", "melt", "member", "memo",
        "memory", "menace", "mend", "mental", "mentor", "menu", "mercy", "mere", "merely", "merge", "merger", "merit",
        "merry", "mesh", "mess", "messy", "met", "metal", "meter", "method", "methyl", "metric", "metro", "mexico",
        "miami", "mickey", "mid", "midas", "midday", "middle", "midst", "midway", "might", "mighty", "milan", "mild",
        "mildew", "mile", "milk", "milky", "mill", "mimic", "mince", "mind", "mine", "mini", "mink", "minor",
        "mint", "minus", "minute", "mirror", "mirth", "misery", "miss", "mist", "misty", "mite", "mix", "mizzle",
        "moan", "moat", "mobile", "mock", "mode", "model", "modem", "modern", "modest", "modify", "module", "moist",
        "molar", "mole", "molten", "moment", "monaco", "monday", "money", "monies", "monk", "monkey", "month", "mood",
        "moody", "moon", "moor", "moral", "morale", "morbid", "more", "morgue", "mortal", "mortar", "mosaic", "moscow",
        "moses", "mosque", "moss", "most", "mostly", "moth", "mother", "motion", "motive", "motor", "mould", "mount",
        "mourn", "mouse", "mouth", "move", "movie", "mrs", "much", "muck", "mucky", "mucus", "mud", "muddle",
        "muddy", "mule", "mummy", "munich", "murky", "murmur", "muscle", "museum", "music", "mussel", "must", "mutant",
        "mute", "mutiny", "mutter", "mutton", "mutual", "muzzle", "myopic", "myriad", "myself", "mystic", "myth",
        "nadir",
        "nail", "name", "namely", "nape", "napkin", "naples", "narrow", "nasal", "nation", "native", "nature", "nausea",
        "naval", "nave", "navy", "near", "nearer", "nearly", "neat", "neatly", "neck", "need", "needle", "needy",
        "negate", "nemo", "neon", "nepal", "nephew", "nerve", "nest", "neural", "never", "newark", "newly", "next",
        "nice", "nicely", "niche", "nickel", "nidor", "niece", "night", "nile", "nimble", "nine", "ninety", "ninth",
        "nobel", "noble", "nobody", "node", "noise", "noisy", "non", "none", "noon", "nor", "norm", "normal",
        "north", "norway", "nose", "nostoc", "nosy", "not", "note", "notice", "notify", "notion", "nought", "noun",
        "novel", "novice", "now", "nozzle", "nubere", "null", "numb", "number", "nurse", "nylon", "oak", "oasis",
        "oath", "obese", "obey", "object", "oblige", "oboe", "obtain", "occult", "occupy", "occur", "ocean", "octave",
        "odd", "off", "offend", "offer", "office", "offset", "often", "ohio", "oil", "oily", "okay", "old",
        "older", "oldest", "olive", "omega", "omen", "omit", "once", "one", "onion", "only", "onset", "onto",
        "onus", "onward", "opaque", "open", "openly", "opera", "opium", "oppose", "optic", "option", "oracle", "orange",
        "orbit", "orchid", "orchil", "ordeal", "order", "organ", "orient", "origin", "ornate", "orphan", "oscar",
        "oslo",
        "other", "otter", "ought", "ounce", "our", "out", "outer", "output", "outset", "oval", "oven", "over",
        "overt", "owe", "owing", "owl", "own", "owner", "oxford", "oxide", "oxygen", "oyster", "ozone", "pace",
        "pack", "packet", "pact", "paddle", "paddy", "pagan", "page", "paid", "pain", "paint", "pair", "palace",
        "pale", "palm", "panama", "panel", "panic", "papa", "papal", "paper", "parade", "parcel", "pardon", "parent",
        "paris", "parish", "park", "parody", "parrot", "part", "partly", "party", "pascal", "pass", "past", "paste",
        "pastel", "pastor", "pastry", "pat", "patch", "patent", "path", "patio", "patrol", "patron", "paul", "pause",
        "pave", "pay", "peace", "peach", "peak", "pear", "pearl", "pedal", "peel", "peer", "peking", "pelvic",
        "pelvis", "pen", "penal", "pence", "pencil", "pennon", "penny", "people", "pepper", "per", "perch", "peril",
        "perish", "permit", "person", "peru", "pest", "peter", "petrol", "petty", "phage", "phase", "philip", "phone",
        "photo", "phrase", "piano", "pick", "picket", "picnic", "pie", "piece", "pier", "pierce", "piety", "pig",
        "pigeon", "piggy", "pigsty", "pike", "pile", "pill", "pillar", "pillow", "pilot", "pin", "pinch", "pine",
        "pink", "pint", "pious", "pipe", "pirate", "piston", "pit", "pitch", "pity", "pivot", "pixel", "pizza",
        "place", "placid", "plague", "plaguy", "plain", "plan", "plane", "planet", "plank", "plant", "plasma", "plate",
        "play", "playa", "player", "plea", "plead", "please", "pledge", "plenty", "plenum", "plight", "plot", "ploy",
        "plum", "plump", "plunge", "plural", "plus", "plush", "pocket", "pod", "poem", "poet", "poetic", "poetry",
        "point", "poison", "poland", "polar", "pole", "police", "policy", "polish", "polite", "poll", "pollen", "polo",
        "pond", "ponder", "pony", "pool", "poor", "poorly", "pop", "pope", "popery", "poppy", "pore", "pork",
        "port", "portal", "pose", "posh", "post", "postal", "potato", "potent", "pouch", "pound", "pour", "powder",
        "power", "prague", "praise", "prate", "pray", "prayer", "preach", "prefer", "prefix", "press", "pretty",
        "price",
        "pride", "priest", "primal", "prime", "prince", "print", "prior", "prism", "prison", "privy", "prize", "probe",
        "profit", "prompt", "prone", "proof", "propel", "proper", "prose", "proton", "proud", "prove", "proven",
        "proxy",
        "prune", "psalm", "pseudo", "psyche", "pub", "public", "puff", "pull", "pulp", "pulpit", "pulsar", "pulse",
        "pump", "punch", "pung", "punish", "punk", "pupil", "puppet", "puppy", "pure", "purely", "purge", "purify",
        "purple", "purse", "pursue", "push", "pushy", "put", "putt", "puzzle", "quaint", "quake", "quarry", "quartz",
        "quay", "quebec", "queen", "query", "quest", "queue", "quick", "quid", "quiet", "quilt", "quirk", "quit",
        "quite", "quiver", "quiz", "quota", "quote", "rabato", "rabbit", "race", "racism", "rack", "racket", "radar",
        "radio", "radish", "radius", "raffle", "raft", "rage", "raid", "rail", "rain", "rainy", "raise", "rally",
        "ramp", "random", "range", "rank", "ransom", "rapid", "rare", "rarely", "rarity", "rash", "rat", "rate",
        "rather", "ratify", "ratio", "rattle", "rave", "raven", "raw", "ray", "razor", "reach", "react", "read",
        "reader", "ready", "real", "really", "realm", "reap", "rear", "reason", "rebel", "recall", "recent", "recess",
        "recipe", "reckon", "record", "recoup", "rector", "red", "redeem", "reduce", "reed", "reef", "reefy", "refer",
        "reform", "refuge", "refuse", "regal", "regard", "regent", "regime", "region", "regret", "reign", "relate",
        "relax",
        "relay", "relic", "relief", "relish", "rely", "remain", "remark", "remedy", "remind", "remit", "remote",
        "remove",
        "renal", "render", "rent", "rental", "repair", "repeal", "repeat", "repent", "repine", "reply", "report",
        "rescue",
        "resent", "reside", "resign", "resin", "resist", "resort", "rest", "result", "resume", "retail", "retain",
        "retina",
        "retire", "return", "reveal", "revest", "review", "revise", "revive", "revolt", "reward", "rex", "rhexia",
        "rhine",
        "rhino", "rho", "rhyme", "rhythm", "ribbon", "rice", "rich", "rick", "rid", "ride", "rider", "ridge",
        "rife", "rifle", "rift", "right", "rigid", "ring", "rinse", "riot", "ripe", "ripen", "ripple", "rise",
        "risk", "risky", "rite", "ritual", "ritz", "rival", "river", "road", "roar", "roast", "rob", "robe",
        "robert", "robin", "robot", "robust", "rock", "rocket", "rocks", "rocky", "rod", "rode", "rodent", "rogue",
        "role", "roll", "roman", "rome", "roof", "room", "root", "rope", "rosa", "rose", "roseau", "rosy",
        "rotate", "rotor", "rotten", "rouge", "rough", "round", "route", "rover", "row", "royal", "rubble", "ruby",
        "rudder", "rude", "rugby", "ruin", "rule", "ruler", "rumble", "run", "rune", "rung", "runway", "rural",
        "rush", "russia", "rust", "rustic", "rusty", "ruta", "sabe", "saber", "sack", "sacred", "sad", "saddle",
        "sadism", "sadly", "safari", "safe", "safely", "safer", "safety", "saga", "sage", "sahara", "said", "sail",
        "sailor", "saint", "sake", "salad", "salary", "sale", "saline", "saliva", "salmon", "saloon", "salt", "salty",
        "salute", "sam", "same", "sample", "sand", "sandy", "sane", "sarong", "sash", "satin", "satire", "saturn",
        "sauce", "saudi", "sauna", "savage", "save", "saxon", "say", "scale", "scalp", "scan", "scant", "scar",
        "scarce", "scare", "scarf", "scary", "scene", "scenic", "scent", "school", "scope", "score", "scorn", "scot",
        "scotch", "scout", "scrap", "scream", "screen", "script", "scroll", "scrub", "scute", "sea", "seal", "seam",
        "seaman", "search", "season", "seat", "second", "secret", "sect", "sector", "secure", "see", "seed", "seeing",
        "seek", "seem", "seize", "seldom", "select", "self", "sell", "seller", "semi", "senate", "send", "senile",
        "senior", "sense", "sensor", "sent", "sentry", "seoul", "sequel", "serene", "serial", "series", "sermon",
        "serum",
        "serve", "server", "set", "settle", "seven", "severe", "sewage", "shabby", "shade", "shadow", "shady", "shaft",
        "shaggy", "shah", "shake", "shaky", "shall", "sham", "shame", "shanks", "shape", "share", "shark", "sharp",
        "shawl", "she", "shear", "sheen", "sheep", "sheer", "sheet", "shelf", "shell", "sherry", "shield", "shift",
        "shine", "shiny", "ship", "shire", "shirt", "shiver", "shock", "shoe", "shook", "shop", "shore", "short",
        "shot", "should", "shout", "show", "shower", "shrank", "shrewd", "shrill", "shrimp", "shrine", "shrink",
        "shrub",
        "shrug", "shuha", "shut", "shy", "shyly", "side", "sided", "siege", "sigh", "sight", "sigma", "sign",
        "signal", "silent", "silk", "silken", "silky", "sill", "silly", "silver", "simian", "simple", "simply", "since",
        "sinful", "sing", "singer", "single", "sink", "sir", "siren", "sirius", "sister", "sit", "site", "six",
        "sixth", "sixty", "size", "sketch", "skill", "skin", "skinny", "skip", "skirt", "skull", "sky", "slab",
        "slabby", "slack", "slain", "slam", "slang", "slap", "slate", "slater", "sleek", "sleep", "sleepy", "sleeve",
        "slice", "slick", "slid", "slide", "slight", "slim", "slimy", "sling", "slip", "slit", "slogan", "slope",
        "sloppy", "slot", "slow", "slowly", "slug", "slum", "slump", "small", "smart", "smash", "smear", "smell",
        "smelly", "smelt", "smile", "smite", "smoke", "smoky", "smooth", "smug", "snack", "snail", "snake", "snap",
        "sneak", "snow", "snowy", "snug", "soak", "soap", "sober", "soccer", "social", "sock", "socket", "soda",
        "sodden", "sodium", "sofa", "soft", "soften", "softly", "soggy", "soil", "solar", "sold", "sole", "solely",
        "solemn", "solid", "solo", "solve", "somali", "some", "son", "sonar", "sonata", "song", "sonic", "sony",
        "soon", "sooner", "soot", "soothe", "sordid", "sore", "sorrow", "sorry", "sort", "soul", "sound", "soup",
        "sour", "source", "space", "spade", "spain", "span", "spare", "spark", "sparse", "spasm", "spat", "spate",
        "speak", "spear", "speech", "speed", "speedy", "spell", "spend", "sphere", "spice", "spicy", "spider", "spiky",
        "spill", "spin", "spinal", "spine", "spinus", "spiral", "spirit", "spite", "splash", "split", "spoil", "spoke",
        "sponge", "spoon", "sport", "spot", "spouse", "spout", "spray", "spread", "spree", "spring", "sprint", "spur",
        "squad", "square", "squash", "squat", "squid", "stab", "stable", "stack", "staff", "stage", "stain", "stair",
        "stake", "stale", "stalin", "stall", "stamp", "stance", "stand", "staple", "star", "starch", "stare", "stark",
        "start", "starve", "state", "static", "statue", "status", "stay", "stead", "steady", "steak", "steal", "steam",
        "steel", "steep", "steer", "stem", "stench", "step", "steppe", "stereo", "stern", "stew", "stick", "sticky",
        "stiff", "stifle", "stigma", "still", "sting", "stint", "stir", "stitch", "stock", "stocky", "stone", "stony",
        "stool", "stop", "store", "storm", "stormy", "story", "stot", "stout", "stove", "strain", "strait", "strand",
        "strap", "strata", "straw", "stray", "streak", "stream", "street", "stress", "strict", "stride", "strife",
        "strike",
        "string", "strip", "strive", "stroll", "strong", "stud", "studio", "study", "stuff", "stuffy", "stunt",
        "sturdy",
        "style", "submit", "subset", "subtle", "subtly", "suburb", "such", "sudan", "sudden", "sue", "suez", "suffer",
        "sugar", "suit", "suite", "suitor", "sullen", "sultan", "sum", "summer", "summit", "summon", "sun", "sunday",
        "sunny", "sunset", "super", "superb", "supper", "supple", "supply", "sure", "surely", "surf", "surge", "survey",
        "suture", "swamp", "swan", "swap", "swarm", "sway", "swear", "sweat", "sweaty", "sweden", "sweep", "sweet",
        "swell", "swift", "swim", "swine", "swing", "swirl", "swiss", "switch", "sword", "swore", "sydney", "symbol",
        "synod", "syntax", "syria", "syrup", "system", "table", "tablet", "tace", "tacit", "tackle", "tact", "tactic",
        "tail", "tailor", "taiwan", "take", "tale", "talent", "talk", "tall", "tally", "tame", "tandem", "tangle",
        "tank", "tap", "tape", "target", "tariff", "tart", "tarzan", "task", "tasset", "taste", "tasty", "tattoo",
        "taurus", "taut", "tavern", "tax", "taxi", "tea", "teach", "teak", "team", "tear", "tease", "tech",
        "tecum", "teeth", "tehran", "tel", "tell", "temper", "temple", "tempo", "tempt", "ten", "tenant", "tend",
        "tender", "tendon", "tenet", "tennis", "tenor", "tense", "tensor", "tent", "tenth", "tenure", "tera", "teresa",
        "term", "test", "texas", "text", "than", "thank", "that", "the", "their", "them", "theme", "then",
        "thence", "theory", "there", "these", "thesis", "they", "thick", "thief", "thigh", "thin", "thing", "think",
        "third", "thirst", "thirty", "this", "thomas", "thorn", "those", "though", "thread", "threat", "three",
        "thrill",
        "thrive", "throat", "throne", "throng", "throw", "thrust", "thud", "thug", "thumb", "thump", "thus", "thyme",
        "tibet", "tick", "ticket", "tidal", "tide", "tidy", "tie", "tier", "tiger", "tight", "tile", "tiling",
        "till", "tilt", "timber", "time", "timid", "tin", "tiny", "tip", "tissue", "title", "toad", "toast",
        "today", "token", "tokyo", "told", "toll", "tom", "tomato", "tomb", "tonal", "tone", "tonic", "too",
        "took", "tool", "tooth", "top", "topaz", "tophet", "topic", "torch", "torque", "torso", "tort", "toss",
        "total", "totem", "touch", "tough", "tour", "toward", "towel", "tower", "town", "toxic", "toxin", "trace",
        "track", "tract", "trade", "tragic", "trail", "train", "trait", "tram", "trance", "trap", "trauma", "travel",
        "tray", "tread", "treat", "treaty", "treble", "tree", "trek", "tremor", "trench", "trend", "trendy", "trial",
        "tribal", "tribe", "trick", "tricky", "tried", "trifle", "trim", "trio", "trip", "triple", "troop", "trophy",
        "trot", "trough", "trout", "truce", "truck", "true", "truly", "trunk", "trust", "truth", "try", "tsar",
        "tube", "tulle", "tumble", "tuna", "tundra", "tune", "tung", "tunic", "tunis", "tunnel", "turban", "turf",
        "turk", "turkey", "turn", "turtle", "tutor", "tweed", "twelve", "twenty", "twice", "twin", "twist", "two",
        "tycoon", "tying", "type", "tyrant", "uganda", "ugly", "ulcer", "ultra", "umpire", "unable", "uncle", "under",
        "uneasy", "unfair", "unify", "union", "unique", "unit", "unite", "unity", "unkind", "unlike", "unrest",
        "unruly",
        "unship", "until", "unwary", "update", "upheld", "uphill", "uphold", "upon", "uproar", "upset", "upshot",
        "uptake",
        "upturn", "upward", "urban", "urge", "urgent", "urging", "usable", "usage", "use", "useful", "user", "usual",
        "utmost", "utter", "vacant", "vacuum", "vague", "vain", "valet", "valid", "valley", "value", "valve", "van",
        "vanish", "vanity", "vary", "vase", "vast", "vat", "vault", "vector", "vedic", "veil", "vein", "velvet",
        "vendor", "veneer", "venice", "venom", "vent", "venue", "venus", "verb", "verbal", "verge", "verify", "verity",
        "verse", "versus", "very", "vessel", "vest", "veto", "vex", "via", "viable", "vicar", "vice", "victim",
        "victor", "video", "vienna", "view", "vigil", "vigor", "viking", "vile", "villa", "vine", "vinyl", "viola",
        "violet", "violin", "viral", "virgo", "virtue", "virus", "visa", "vision", "visit", "visual", "vitae", "vital",
        "vivid", "vocal", "vodka", "vogue", "voice", "void", "volley", "volume", "vote", "vowel", "voyage", "vulgar",
        "wade", "wage", "waist", "wait", "waiter", "wake", "walk", "walker", "wall", "wallet", "walnut", "wander",
        "want", "war", "warden", "warm", "warmth", "warn", "warp", "warsaw", "wary", "was", "wash", "wasp",
        "waste", "watch", "water", "watery", "wave", "way", "weak", "weaken", "wealth", "wear", "weary", "wedge",
        "wee", "weed", "week", "weekly", "weep", "weight", "weird", "well", "were", "west", "wet", "whale",
        "wharf", "what", "wheat", "wheel", "wheeze", "wheezy", "when", "whence", "where", "which", "whiff", "whig",
        "while", "whim", "whip", "whisky", "white", "who", "whole", "wholly", "whom", "whose", "why", "wide",
        "widely", "widen", "wider", "widow", "width", "wife", "wild", "wildly", "wilful", "will", "willow", "win",
        "wind", "window", "windy", "wine", "winery", "wing", "wink", "winner", "winter", "wipe", "wire", "wisdom",
        "wise", "wish", "wit", "witch", "with", "within", "witty", "wizard", "woke", "wolf", "wolves", "woman",
        "womb", "won", "wonder", "wood", "wooden", "woods", "woody", "wool", "word", "work", "worker", "world",
        "worm", "worry", "worse", "worst", "worth", "worthy", "would", "wound", "wrap", "wrath", "wreath", "wreck",
        "wren", "wright", "wrist", "writ", "write", "writer", "wrong", "xerox", "yacht", "yager", "yale", "yard",
        "yarn", "yeah", "year", "yeast", "yellow", "yemen", "yet", "yield", "yogurt", "yokel", "yolk", "york",
        "you", "young", "your", "youth", "zaire", "zeal", "zebra", "zenith", "zero", "zigzag", "zinc", "zing",
        "zipper", "zombie", "zone", "zurich"
]
class XMSSPrivateKey:

    def __init__(self):
        self.wots_private_keys = None
        self.idx = None
        self.SK_PRF = None
        self.root_value = None
        self.SEED = None


class XMSSPublicKey:

    def __init__(self, OID=None, root_value=None, SEED=None, height=4, n=4, w=32):
        self.OID = OID
        self.root_value = root_value
        self.SEED = SEED

        self.height = height
        self.n = n
        self.w = w
        self.hash_functions = {
            0: hashlib.sha256,
            1: lambda: hashlib.shake_128(),  # Функция возвращает объект хеша
            2: lambda: hashlib.shake_256()  # Функция возвращает объект хеша
        }
        self.address_start = ""

    def generate_address(self, hash_function_code=2):
        # Определение параметров
        tree_height = self.height
        signature_scheme_code = 0  # XMSS

        # Представление параметров в виде байтов
        params = (hash_function_code << 4 | tree_height).to_bytes(1, 'big') + signature_scheme_code.to_bytes(1, 'big')

        # Конкатенация параметров с ключевыми данными
        key_data = params + str(self.OID).encode() + self.root_value + str(self.SEED).encode()

        # Выбор функции хеширования
        hash_func = self.hash_functions.get(hash_function_code, lambda: hashlib.shake_256())()
        hash_func.update(key_data)

        # Условие для длины вывода у shake функций
        if hash_function_code in {1, 2}:
            key_hash = hash_func.digest(32)
        else:
            key_hash = hash_func.digest()

        # Пересоздание объекта хеширования для контрольной суммы
        hash_func = self.hash_functions.get(hash_function_code, lambda: hashlib.shake_256())()
        hash_func.update(key_hash)
        checksum = hash_func.digest(32)[:4] if hash_function_code in {1, 2} else hash_func.digest()[:4]

        # Конкатенация хеша, контрольной суммы и параметров
        full_key = key_hash + params + checksum

        # Кодирование Base58
        address = base58.b58encode(full_key).decode('utf-8')

        return f"{self.address_start}{address}"

    def is_valid_address(self, address):
        try:
            # Декодирование адреса из Base58 и удаление префикса 'Out'
            decoded_address = base58.b58decode(address[len(self.address_start):])

            params = decoded_address[-6:-4]
            hash_function_code = params[0] >> 4
            tree_height = params[0] & 0x0F

            # Отделение контрольной суммы от основной части адреса
            # main_part = decoded_address[2:-4]
            main_part = decoded_address[0:-6]
            checksum = decoded_address[-4:]

            # Выбор функции хеширования
            hash_func = self.hash_functions.get(hash_function_code, lambda: hashlib.shake_256())()

            # Повторное вычисление контрольной суммы
            hash_func.update(main_part)
            calculated_checksum = hash_func.digest(32)[:4] if hash_function_code in {1, 2} else hash_func.digest()[:4]

            # Сравнение рассчитанной контрольной суммы с контрольной суммой в адресе
            return checksum == calculated_checksum
        except Exception as e:
            return False

    def to_json(self):
        return {
            'OID': self.OID,
            'root_value': self.root_value.hex(),
            'SEED': self.SEED,
            'height': self.height,
            'n': self.n,
            'w': self.w
        }

    def to_bytes(self):
        # Сериализация и сжатие объекта в байты
        return zlib.compress(pickle.dumps(self.to_json()))

    def to_str(self):
        return base58.b58encode(self.to_bytes())

    @classmethod
    def from_str(cls, text_pk):
        return XMSSPublicKey.from_json(XMSSPublicKey.from_bytes(base58.b58decode(text_pk)))

    @classmethod
    def from_bytes(cls, bytes_data):
        # Распаковка и десериализация объекта из сжатых байтов
        return pickle.loads(zlib.decompress(bytes_data))

    # def to_bytes(self):
    #     # Кодируем OID и SEED в байты
    #     oid_bytes = self.OID.encode('utf-8') if self.OID is not None else b''
    #     seed_bytes = self.SEED.encode('utf-8') if self.SEED is not None else b''
    #
    #     # Сериализуем данные с указанием длины каждой части
    #     return bytes([len(oid_bytes)]) + oid_bytes + bytes([len(self.root_value)]) + self.root_value + bytes(
    #         [len(seed_bytes)]) + seed_bytes
    #
    # @classmethod
    # def from_bytes(cls, bytes_data):
    #     # Десериализуем OID
    #     oid_length = bytes_data[0]
    #     oid = bytes_data[1:1 + oid_length].decode('utf-8')
    #
    #     # Десериализуем root_value
    #     root_value_start = 1 + oid_length
    #     root_value_length = bytes_data[root_value_start]
    #     root_value = bytes_data[root_value_start + 1:root_value_start + 1 + root_value_length]
    #
    #     # Десериализуем SEED
    #     seed_start = root_value_start + 1 + root_value_length
    #     seed_length = bytes_data[seed_start]
    #     SEED = bytes_data[seed_start + 1:seed_start + 1 + seed_length].decode('utf-8')
    #
    #     return cls(OID=oid, root_value=root_value, SEED=SEED)

    @classmethod
    def from_json(cls, json_data):
        OID = json_data.get('OID')
        root_value_hex = json_data.get('root_value')
        SEED = json_data.get('SEED')
        height = json_data.get('height')
        n = json_data.get('n')
        w = json_data.get('w')

        root_value = bytes.fromhex(root_value_hex) if root_value_hex else None
        # SEED = bytes.fromhex(SEED_hex) if SEED_hex else None

        return cls(OID=OID, root_value=root_value, SEED=SEED, height=height, n=n, w=w)


class XMSSKeypair:

    def __init__(self, SK, PK, height=4, n=4, w=32):
        self.SK = SK
        self.PK = PK
        self.height = height
        self.n = n
        self.w = w


class SigXMSS:
    def __init__(self, idx_sig, r, sig_ots, auth):
        self.idx_sig = idx_sig
        self.r = r
        self.sig_ots = sig_ots
        self.auth = auth

    def to_bytes(self):
        # Сериализация и сжатие объекта в байты
        return zlib.compress(pickle.dumps(self))

    @staticmethod
    def from_bytes(bytes_data):
        # Распаковка и десериализация объекта из сжатых байтов
        return pickle.loads(zlib.decompress(bytes_data))

    def to_str(self):
        return base58.b58encode(self.to_bytes())

    @classmethod
    def from_str(cls, sign_str):
        return SigXMSS.from_bytes(base58.b58decode(sign_str))

class SigWithAuthPath:
    def __init__(self, sig_ots, auth):
        self.sig_ots = sig_ots
        self.auth = auth


class ADRS:

    def __init__(self):
        self.layerAddress = bytes(4)
        self.treeAddress = bytes(8)
        self.type = bytes(4)

        self.first_word = bytes(4)
        self.second_word = bytes(4)
        self.third_word = bytes(4)

        self.keyAndMask = bytes(4)

    def setType(self, type_value):
        self.type = type_value.to_bytes(4, byteorder='big')
        self.first_word = bytearray(4)
        self.second_word = bytearray(4)
        self.third_word = bytearray(4)
        self.keyAndMask = bytearray(4)

    def getTreeHeight(self):
        return self.second_word

    def getTreeIndex(self):
        return self.third_word

    def setHashAddress(self, value):
        self.third_word = value.to_bytes(4, byteorder='big')

    def setKeyAndMask(self, value):
        self.keyAndMask = value.to_bytes(4, byteorder='big')

    def setChainAddress(self, value):
        self.second_word = value.to_bytes(4, byteorder='big')

    def setTreeHeight(self, value):
        self.second_word = value.to_bytes(4, byteorder='big')

    def setTreeIndex(self, value):
        self.third_word = value.to_bytes(4, byteorder='big')

    def setOTSAddress(self, value):
        self.first_word = value.to_bytes(4, byteorder='big')

    def setLTreeAddress(self, value):
        self.first_word = value.to_bytes(4, byteorder='big')

    def setLayerAddress(self, value):
        self.layerAddress = value.to_bytes(4, byteorder='big')

    def setTreeAddress(self, value):
        self.treeAddress = value.to_bytes(4, byteorder='big')


def WOTS_genSK(length, n):
    secret_key = [bytes()] * length

    for i in range(length):
        SEED = generate_random_value(length)

        secret_key[i] = pseudorandom_function(SEED, n)

    return secret_key


import random


def WOTS_genSK_from_seed(length, n, seed):
    # Инициализация генератора случайных чисел с использованием сида
    random.seed(seed)

    secret_key = []
    for _ in range(length):
        # Генерация элемента секретного ключа
        random_bytes = random.getrandbits(n * 8).to_bytes(n, 'big')
        secret_key.append(random_bytes)

    return secret_key


def WOTS_genPK(private_key: [bytes], length: int, w: int in {4, 16}, SEED, address):
    public_key = [bytes()] * length
    for i in range(length):
        address.setChainAddress(i)
        public_key[i] = chain(private_key[i], 0, w - 1, SEED, address, w)

    return public_key


def WOTS_sign(message: bytes, private_key: [bytes], w: int in {4, 16}, SEED, address):
    checksum = 0

    n = len(message) // 2
    len_1, len_2, len_all = compute_lengths(n, w)

    msg = base_w(message, w, len_1)

    for i in range(0, len_1):
        checksum += w - 1 - msg[i]

    checksum = checksum << int(8 - ((len_2 * log2(w)) % 8))

    len_2_bytes = compute_needed_bytes(checksum)

    msg.extend(base_w(to_byte(checksum, len_2_bytes), w, len_2))

    signature = [bytes()] * len_all

    for i in range(0, len_all):
        address.setChainAddress(i)
        signature[i] = chain(private_key[i], 0, msg[i], SEED, address, w)

    return signature


def WOTS_pkFromSig(message: bytes, signature: [bytes], w: int in {4, 16}, address, SEED):
    checksum = 0

    n = len(message) // 2
    len_1, len_2, len_all = compute_lengths(n, w)

    msg = base_w(message, w, len_1)

    for i in range(0, len_1):
        checksum += w - 1 - msg[i]

    checksum = checksum << int(8 - ((len_2 * log2(w)) % 8))

    len_2_bytes = compute_needed_bytes(checksum)

    msg.extend(base_w(to_byte(checksum, len_2_bytes), w, len_2))

    tmp_pk = [bytes()] * len_all

    for i in range(0, len_all):
        address.setChainAddress(i)
        tmp_pk[i] = chain(signature[i], msg[i], w - 1 - msg[i], SEED, address, w)

    return tmp_pk


def base_w(byte_string: bytes, w: int in {4, 16}, out_len):
    in_ = 0
    total_ = 0
    bits_ = 0
    base_w_ = []

    for i in range(0, out_len):
        if bits_ == 0:
            total_ = byte_string[in_]
            in_ += 1
            bits_ += 8

        bits_ -= log2(w)
        base_w_.append((total_ >> int(bits_)) & (w - 1))
    return base_w_


def generate_random_value(n, seed_value=None):
    # Инициализация генератора случайных чисел с заданным сидом
    seed(seed_value)

    alphabet = ascii_letters + digits
    value = ''.join(choice(alphabet) for _ in range(n))

    return value


def compute_needed_bytes(n):
    if n == 0:
        return 1
    return int(log(n, 256)) + 1


def compute_lengths(n: int, w: int in {4, 16}):
    len_1 = ceil(8 * n / log2(w))
    len_2 = floor(log2(len_1 * (w - 1)) / log2(w)) + 1
    len_all = len_1 + len_2
    return len_1, len_2, len_all


def to_byte(value, bytes_count):
    # Преобразование целого числа в bytes
    return value.to_bytes(bytes_count, byteorder='big')


def xor(one: bytearray, two: bytearray) -> bytearray:
    return bytearray(a ^ b for (a, b) in zip(one, two))


def int_to_bytes(val, count):
    byteVal = to_byte(val, count)
    acc = bytearray()
    for i in range(len(byteVal)):
        if byteVal[i] < 16:
            acc.extend(b'0')
        curr = hex(byteVal[i])[2:]
        acc.extend(curr.encode())
    return acc


def F(KEY, M):
    key_len = len(KEY)
    toBytes = to_byte(0, 4)
    help_ = sha256(toBytes + KEY + M).hexdigest()[:key_len]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def chain(X, i, s, SEED, address, w):
    if s == 0:
        return X
    if (i + s) > (w - 1):
        return None
    tmp = chain(X, i, s - 1, SEED, address, w)

    address.setHashAddress((i + s - 1))
    address.setKeyAndMask(0)
    KEY = PRF(SEED, address)
    address.setKeyAndMask(1)
    BM = PRF(SEED, address)
    tmp = F(KEY, xor(tmp, BM))
    return tmp


def PRF(KEY: str, M: ADRS) -> bytearray:
    toBytes = to_byte(3, 4)
    key_len = len(KEY)
    KEY2 = bytearray()
    KEY2.extend(map(ord, KEY))
    help_ = sha256(toBytes + KEY2 + M.keyAndMask).hexdigest()[:key_len * 2]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def H(KEY: bytearray, M: bytearray) -> bytearray:
    key_len = len(KEY)
    toBytes = to_byte(1, 4)
    help_ = sha256(toBytes + KEY + M).hexdigest()[:key_len]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def PRF_XMSS(KEY: str, M: bytearray, n: int) -> bytearray:
    toBytes = to_byte(3, 4)
    KEY2 = bytearray()
    KEY2.extend(map(ord, KEY))
    help_ = sha256(toBytes + KEY2 + M).hexdigest()[:n]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def H_msg(KEY: bytearray, M: bytearray, n: int) -> bytearray:
    toBytes = to_byte(2, 4)
    help_ = sha256(toBytes + KEY + M).hexdigest()[:n]
    out = bytearray()
    out.extend(map(ord, help_))
    return out


def RAND_HASH(left: bytearray, right: bytearray, SEED: str, adrs: ADRS):
    adrs.setKeyAndMask(0)
    KEY = PRF(SEED, adrs)
    adrs.setKeyAndMask(1)
    BM_0 = PRF(SEED, adrs)
    adrs.setKeyAndMask(2)
    BM_1 = PRF(SEED, adrs)

    return H(KEY, xor(left, BM_0) + xor(right, BM_1))


def pseudorandom_function(seed, n):
    # Создаем хеш из сида, предполагая, что seed является строкой.
    seed_bytes = seed.encode('utf-8')  # Преобразуем строку сида в байты
    hash_digest = hashlib.sha256(seed_bytes).digest()  # Создаем хеш SHA-256 от сида

    # Обрезаем или дополняем хеш до нужной длины n, возвращаем как bytearray
    return bytearray(hash_digest)[:n]


def ltree(pk: List[bytearray], address: ADRS, SEED: str, length: int) -> bytearray:
    address.setTreeHeight(0)

    while length > 1:
        for i in range(floor(length / 2)):
            address.setTreeIndex(i)
            pk[i] = RAND_HASH(pk[2 * i], pk[2 * i + 1], SEED, address)

        if length % 2 == 1:
            pk[floor(length / 2)] = pk[length - 1]

        length = ceil(length / 2)
        height = address.getTreeHeight()
        height = int.from_bytes(height, byteorder='big')
        address.setTreeHeight(height + 1)

    return pk[0]


def treeHash(SK: XMSSPrivateKey, s: int, t: int, address: ADRS, w: int in {4, 16}, length_all: int) -> bytearray:
    class StackElement:
        def __init__(self, node_value=None, height=None):
            self.node_value = node_value
            self.height = height

    Stack = []

    if s % (1 << t) != 0:
        raise ValueError("should be s % (1 << t) != 0")

    for i in range(0, int(pow(2, t))):
        SEED = SK.SEED
        address.setType(0)
        address.setOTSAddress(s + i)
        pk = WOTS_genPK(SK.wots_private_keys[s + i], length_all, w, SEED, address)
        address.setType(1)
        address.setLTreeAddress(s + i)
        node = ltree(pk, address, SEED, length_all)

        node_as_stack_element = StackElement(node, 0)

        address.setType(2)
        address.setTreeHeight(0)
        address.setTreeIndex(i + s)

        while len(Stack) != 0 and Stack[len(Stack) - 1].height == node_as_stack_element.height:
            address.setTreeIndex(int((int.from_bytes(address.getTreeHeight(), byteorder='big') - 1) / 2))

            previous_height = node_as_stack_element.height

            node = RAND_HASH(Stack.pop().node_value, node_as_stack_element.node_value, SEED, address)

            node_as_stack_element = StackElement(node, previous_height + 1)

            address.setTreeHeight(int.from_bytes(address.getTreeHeight(), byteorder='big') + 1)

        Stack.append(node_as_stack_element)

    return Stack.pop().node_value


def XMSS_keyGen(height: int, n: int, w: int in {4, 16}) -> XMSSKeypair:
    len_1, len_2, len_all = compute_lengths(n, w)

    wots_sk = []
    for i in range(0, 2 ** height):
        wots_sk.append(WOTS_genSK(len_all, n))

    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()
    idx = 0

    SK.SK_PRF = generate_random_value(n)
    SEED = generate_random_value(n)
    SK.SEED = SEED
    SK.wots_private_keys = wots_sk

    adrs = ADRS()

    root = treeHash(SK, 0, height, adrs, w, len_all)

    SK.idx = idx
    SK.root_value = root

    PK.OID = generate_random_value(n)
    PK.root_value = root
    PK.SEED = SEED

    KeyPair = XMSSKeypair(SK, PK)
    return KeyPair


def XMSS_keyGen_from_seed(seed: str, height: int, n: int, w: int) -> XMSSKeypair:
    len_1, len_2, len_all = compute_lengths(n, w)
    wots_sk = []

    # Изменяем генерацию WOTS ключей, используя уникальный сид для каждого ключа
    for i in range(0, 2 ** height):
        unique_seed = pseudorandom_function(seed + str(i), n)  # Генерация уникального сида для каждого ключа
        wots_sk.append(WOTS_genSK_from_seed(len_all, n, unique_seed))

    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()
    idx = 0

    SK.SK_PRF = generate_random_value(n, seed + "SK_PRF")  # Генерация SK_PRF на основе сида
    SEED = generate_random_value(n, seed + "SEED")  # Генерация SEED на основе сида
    SK.SEED = SEED
    SK.wots_private_keys = wots_sk

    adrs = ADRS()

    # Генерация корня дерева
    root = treeHash(SK, 0, height, adrs, w, len_all)
    SK.idx = idx
    SK.root_value = root

    PK.OID = generate_random_value(n, seed + "OID")  # Генерация OID на основе сида
    PK.root_value = root
    PK.SEED = SEED

    KeyPair = XMSSKeypair(SK, PK, height, n, w)
    return KeyPair


def buildAuth(SK: XMSSPrivateKey, index: int, address: ADRS, w: int in {4, 16}, length_all: int, h: int) -> List[
    bytearray]:
    auth = []

    for j in range(h):
        k = floor(index / (2 ** j)) ^ 1
        auth.append(treeHash(SK, k * (2 ** j), j, address, w, length_all))
    return auth


def treeSig(message: bytearray, SK: XMSSPrivateKey, address: ADRS, w: int in {4, 16}, length_all: int, idx_sig: int,
            h: int) -> SigWithAuthPath:
    auth = buildAuth(SK, idx_sig, address, w, length_all, h)
    address.setType(0)
    address.setOTSAddress(idx_sig)
    sig_ots = WOTS_sign(message, SK.wots_private_keys[idx_sig], w, SK.SEED, address)
    Sig = SigWithAuthPath(sig_ots, auth)
    return Sig


def XMSS_sign(message: bytearray, SK: XMSSPrivateKey, n, w: int, address: ADRS, h: int) -> SigXMSS:
    len_1, len_2, length_all = compute_lengths(n, w)
    idx_sig = SK.idx
    SK.idx += 1  # Инкрементируем индекс после использования

    # Генерация случайного значения на основе секретного ключа и индекса подписи
    r = PRF_XMSS(SK.SK_PRF, to_byte(idx_sig, 4), len_1)

    # Создание расширенного представления подписи с добавлением r и root_value
    arrayOfBytes = bytearray(r)
    arrayOfBytes.extend(SK.root_value)
    arrayOfBytes.extend(bytearray(int_to_bytes(idx_sig, n)))

    # Генерация вторичного хеша сообщения
    M2 = H_msg(arrayOfBytes, message, len_1)

    # Получение одноразовой подписи и аутентификационного пути
    sig = treeSig(M2, SK, address, w, length_all, idx_sig, h)

    # Создание и возвращение объекта SigXMSS с необходимыми данными для верификации
    return SigXMSS(idx_sig, r, sig.sig_ots, sig.auth)


def XMSS_rootFromSig(idx_sig: int, sig_ots, auth: List[bytearray], message: bytearray, h: int, w: int in {4, 16}, SEED,
                     address: ADRS):
    n = len(message) // 2
    len_1, len_2, length_all = compute_lengths(n, w)

    address.setType(0)
    address.setOTSAddress(idx_sig)
    pk_ots = WOTS_pkFromSig(message, sig_ots, w, address, SEED)
    address.setType(1)
    address.setLTreeAddress(idx_sig)
    node = [bytearray, bytearray]
    node[0] = ltree(pk_ots, address, SEED, length_all)
    address.setType(2)
    address.setTreeIndex(idx_sig)

    for k in range(0, h):
        address.setTreeHeight(k)
        if floor(idx_sig / (2 ** k)) % 2 == 0:
            address.setTreeIndex(int.from_bytes(address.getTreeIndex(), byteorder='big') // 2)
            node[1] = RAND_HASH(node[0], auth[k], SEED, address)
        else:
            address.setTreeIndex((int.from_bytes(address.getTreeIndex(), byteorder='big') - 1) // 2)
            node[1] = RAND_HASH(auth[k], node[0], SEED, address)

        node[0] = node[1]

    return node[0]


# def XMSS_verify(Sig: SigXMSS, M: bytearray, PK: XMSSPublicKey, n, w: int in {4, 16}, SEED, height: int):
def XMSS_verify(Sig: SigXMSS, M: bytearray, PK: XMSSPublicKey):
    address = ADRS()

    height = PK.height
    n = PK.n
    w = PK.w
    SEED = PK.SEED

    # n = len(M) // 2
    len_1, len_2, length_all = compute_lengths(n, w)

    arrayOfBytes = bytearray()
    arrayOfBytes.extend(Sig.r)
    arrayOfBytes.extend(PK.root_value)
    arrayOfBytes.extend(bytearray(int_to_bytes(Sig.idx_sig, n)))

    M2 = H_msg(arrayOfBytes, M, len_1)

    node = XMSS_rootFromSig(Sig.idx_sig, Sig.sig_ots, Sig.auth, M2, height, w, SEED, address)

    if node == PK.root_value:
        return True
    else:
        return False


def generate_seed(length):
    # Простая функция для генерации псевдослучайного сида
    return ''.join(choice(ascii_letters + digits) for _ in range(length))


def XMSS_demo(messages: List[bytearray]):
    height = int(log2(len(messages)))
    n = len(messages[0]) // 2
    w = 16

    keyPair = XMSS_keyGen(height, n, w)

    addressXMSS = ADRS()

    signatures = []

    for message in messages:
        signature = XMSS_sign(message, keyPair.SK, w, addressXMSS, height)
        signatures.append(signature)

    ifProved = True

    for signature, message in zip(signatures, messages):
        if not XMSS_verify(signature, message, keyPair.PK, n, w, keyPair.PK.SEED, height):
            ifProved = False
            break

    print("XMSS verification result:")
    print("Proved: " + str(ifProved))


def XMSS_demo_seed(messages: List[bytearray]):
    # height = int(log2(len(messages)))
    # msg_len = len(messages[0]) // 2
    # w = 16
    #
    # keyPair = XMSS_keyGen(height, msg_len, w)

    seed_client1 = "unique_seed_for_client1"  # Уникальный сид для клиента 1
    height = 4  # Высота дерева
    # n = 8  # Размер хэша в байтах
    n = len(messages[0]) // 2
    w = 16  # Параметр Winternitz

    # Генерация пары ключей на основе сида
    keyPair = XMSS_keyGen_from_seed(seed_client1, height, n, w)

    addressXMSS = ADRS()

    signatures = []

    for message in messages:
        signature = XMSS_sign(message, keyPair.SK, n, w, addressXMSS, height)
        signatures.append(signature)

    ifProved = True

    for signature, message in zip(signatures, messages):
        if not XMSS_verify(signature, message, keyPair.PK, n, w, keyPair.PK.SEED, height):
            ifProved = False
            break

    print("XMSS verification result:")
    print("Proved: " + str(ifProved))


import os


def save_keys_to_file(keypair: XMSSKeypair, file_path: str):
    data = {
        'height': keypair.height,
        'n': keypair.n,
        'w': keypair.w,
        'private_key': {
            # Исправлено: обработка списка списков байтов
            'wots_private_keys': [[key.hex() for key in wots_key] for wots_key in keypair.SK.wots_private_keys],
            'idx': keypair.SK.idx,
            'SK_PRF': keypair.SK.SK_PRF,
            'root_value': keypair.SK.root_value.hex(),
            'SEED': keypair.SK.SEED
        },
        'public_key': {
            'OID': keypair.PK.OID,
            'root_value': keypair.PK.root_value.hex(),
            'SEED': keypair.PK.SEED
        }

    }
    with open(file_path, 'w') as file:
        json.dump(data, file)


def load_keys_from_file(file_path: str) -> XMSSKeypair:
    with open(file_path, 'r') as file:
        data = json.load(file)

    height = data['height']
    n = data['n']
    w = data['w']

    SK = XMSSPrivateKey()
    PK = XMSSPublicKey()

    # Исправлено: корректная обработка структуры данных
    SK.wots_private_keys = [
        [bytes.fromhex(key_hex) for key_hex in wots_key]
        for wots_key in data['private_key']['wots_private_keys']
    ]
    SK.idx = data['private_key']['idx']
    SK.SK_PRF = data['private_key']['SK_PRF']
    SK.root_value = bytearray.fromhex(data['private_key']['root_value'])

    SK.SEED = data['private_key']['SEED']

    PK.OID = data['public_key']['OID']
    PK.root_value = bytes.fromhex(data['public_key']['root_value'])
    PK.SEED = data['public_key']['SEED']
    PK.height = height
    PK.n = n
    PK.w = w

    return XMSSKeypair(SK, PK, height, n, w)




# def generate_seed_from_secret_key(secret_key: XMSSPrivateKey) -> str:
#     # Сериализуем секретный ключ в строку
#     secret_key_data = {
#         'wots_private_keys': [[key.hex() for key in wots_key] for wots_key in secret_key.wots_private_keys],
#         'idx': secret_key.idx,
#         'SK_PRF': secret_key.SK_PRF,
#         'root_value': secret_key.root_value.hex(),
#         'SEED': secret_key.SEED
#     }
#     secret_key_json = json.dumps(secret_key_data)
#
#     # Хешируем JSON
#     hash_digest = hashlib.sha256(secret_key_json.encode('utf-8')).digest()
#
#     # Преобразуем хеш в 12 слов
#     word_indices = [hash_digest[i] % len(WORD_LIST) for i in range(12)]
#     seed_phrase = ' '.join(WORD_LIST[index] for index in word_indices)
#     return seed_phrase
#
#
# def generate_secret_key_from_seed(seed_phrase: str) -> XMSSPrivateKey:
#     # Разбиваем сид фразу на слова
#     words = seed_phrase.split()
#     if len(words) != 12:
#         raise ValueError("Seed phrase must contain exactly 12 words.")
#
#     # Преобразуем слова обратно в индексы
#     indices = [WORD_LIST.index(word) for word in words]
#
#     # Преобразуем индексы обратно в байты
#     seed_bytes = bytes(indices)
#
#     # Генерация хэша для восстановления ключа
#     hash_digest = hashlib.sha256(seed_bytes).digest()
#
#     # Восстановление секретного ключа из хэша
#     secret_key_json = base58.b58encode(hash_digest).decode('utf-8')
#     secret_key_data = json.loads(base58.b58decode(secret_key_json.encode('utf-8')).decode('utf-8'))
#
#     secret_key = XMSSPrivateKey()
#     secret_key.wots_private_keys = [
#         [bytes.fromhex(key_hex) for key_hex in wots_key]
#         for wots_key in secret_key_data['wots_private_keys']
#     ]
#     secret_key.idx = secret_key_data['idx']
#     secret_key.SK_PRF = secret_key_data['SK_PRF']
#     secret_key.root_value = bytearray.fromhex(secret_key_data['root_value'])
#     secret_key.SEED = secret_key_data['SEED']
#
#     return secret_key

from mnemonic import Mnemonic

def key_to_seed_phrase(key):
    # Проверяем, что длина ключа достаточная для получения 264 бит (необходимо для 24 слов)
    if len(key) < 33:
        raise ValueError("Key must be at least 33 bytes (264 bits) long to ensure it can be encoded into 24 words.")

    # mnemo = Mnemonic('english')

    # Преобразуем каждый байт ключа в его бинарное представление и собираем в одну строку
    bit_string = ''.join(f'{byte:08b}' for byte in key)

    # Генерируем фразу, беря каждые 11 бит из строки битов и преобразуя их в число, которое используется как индекс в списке слов
    seed_phrase = ' '.join(word_list[int(bit_string[i:i + 11], 2)] for i in range(0, 264, 11))

    return seed_phrase



def seed_phrase_to_key(seed_phrase):


    # Преобразуем каждое слово обратно в его индекс в списке слов
    indices = [word_list.index(word) for word in seed_phrase.split()]

    # Преобразуем каждый индекс обратно в бинарную строку, дополняя до 11 бит, и объединяем все в одну строку
    bit_string = ''.join(f'{index:011b}' for index in indices)

    # Преобразуем строку битов обратно в массив байт
    byte_array = bytearray(int(bit_string[i:i + 8], 2) for i in range(0, len(bit_string), 8))
    return bytes(byte_array)

class XMSS():
    def __init__(self):
        pass
    @classmethod
    def create(cls, ):
        """ """
        xmss = XMSS()


if __name__ == '__main__':
    # WOTS_demo(bytearray(b'0e4575aa2c51'))
    # print("#" * 30)
    #

    # Пример вызова функции с сидом
    # seed = generate_seed(20)  # Генерируем сид
    # seed = "rBirgrP91TgImgg937kR"
    #
    # print(seed)
    # height = 4  # Высота дерева, определяющая количество возможных подписей
    # n = 32  # Размер хэша в байтах
    # w = 16  # Параметр Winternitz
    #
    # keyPair = XMSS_keyGen_from_seed(seed, height, n, w)
    #
    # print("Создана пара ключей XMSS с использованием сида.", keyPair.SK.generate_address())

    # seed = "some_seed_value"
    # height = 4  # Высота дерева
    # n = 256  # Длина ключа
    # keypair = XMSSKeypair.generate_keys_from_seed(seed, height, n)
    # print("Приватный ключ и публичный ключ успешно сгенерированы из сида.", keypair)

    # XMSS_demo([bytearray(b'0e4575aa2c51')])
    # XMSS_demo_seed([bytearray(b'0e4575aa2c51'), bytearray(b'1e4575aa2c51')])

    # Генерация пары ключей и адреса для Клиента 1
    seed_client1 = "unique_seed_for_client3111223"  # Уникальный сид для клиента 1
    height = 6  # Высота дерева
    n = 10  # Размер хэша в байтах
    w = 16  # Параметр Winternitz

    print("Количество подписей", 2 ** height)
    # Генерация пары ключей на основе сида
    keyPair_client1 = XMSS_keyGen_from_seed(seed_client1, height, n, w)

    save_keys_to_file(keyPair_client1, "client1.key")

    keyPair_client1 = load_keys_from_file("client1.key")

    # Генерация адреса на основе публичного ключа
    address_client1 = keyPair_client1.PK.generate_address()

    print(f"Сид: {seed_client1}")
    print(f"Адрес Клиента 1: {address_client1}")
    print(f"Размер адреса Клиента 1: {len(address_client1)}")

    is_valid_address = keyPair_client1.PK.is_valid_address(address_client1)
    print(f"Адрес верен: {is_valid_address}")

    # Создание сообщения для подписи
    message_client1 = bytearray(b'This is a message from client1 to be signed.')

    # Подпись сообщения
    # addressXMSS_client1 = ADRS()  # Инициализация адреса для XMSS

    d = datetime.datetime.now()
    print("Делаем подпись")
    signature_client1 = XMSS_sign(message_client1, keyPair_client1.SK, n, w, ADRS(), height)

    print(
        f"Подпись: {signature_client1}, размер: {len(signature_client1.to_bytes())} байт  время: {datetime.datetime.now() - d}")
    print(len(base58.b58encode(signature_client1.to_bytes())))

    sign_str = signature_client1.to_str()
    pk_str = keyPair_client1.PK.to_str()
    print("pk_str", pk_str)
    print("sign_str", sign_str)

    # распаковываем подписи
    PK = XMSSPublicKey.from_str(pk_str)
    signature = SigXMSS.from_str(sign_str)
    print("OTS", signature.idx_sig)

    PK_client1_received = PK

    # Верификация подписи
    verification_result = XMSS_verify(signature, message_client1, PK)

    print(f"Результат верификации подписи: {'Подпись верна' if verification_result else 'Подпись неверна'}")
