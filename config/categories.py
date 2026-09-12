# Default search terms. GitHub Actions can override with CATEGORY_QUERIES_JSON.
from config.settings import CATEGORIES as _OVERRIDE

_DEFAULT = [
"atta","rice","dal","pulses","flour","maida","besan","sooji","rava","poha","oats","quinoa","millets","dalia","vermicelli","noodles","pasta","cooking oil","ghee","salt","sugar","jaggery","honey",
"spices","masala","turmeric","chilli powder","coriander powder","garam masala","pepper","jeera","mustard seeds","dry fruits","nuts","seeds",
"biscuits","cookies","namkeen","chips","popcorn","chocolates","candy","instant noodles","sauces","ketchup","mayonnaise","peanut butter","jam","breakfast cereal","protein bars",
"tea","coffee","health drinks","soft drinks","juices","water","energy drinks","milk","curd","yogurt","paneer","cheese","butter","bread","eggs","fresh fruits","fresh vegetables",
"soap","body wash","shampoo","conditioner","hair oil","face wash","toothpaste","toothbrush","mouthwash","deodorant","perfume","skincare","moisturizer","sunscreen","hand wash","sanitizer","shaving",
"detergent","fabric conditioner","dishwash","floor cleaner","toilet cleaner","surface cleaner","kitchen cleaner","tissues","toilet paper","garbage bags","air freshener","baby care","diapers","baby food","pet food","pet care","stationery","batteries","phone accessories","electronics","kitchen","home essentials","cleaning essentials","personal care","grocery"
]
CATEGORIES = _OVERRIDE or _DEFAULT
