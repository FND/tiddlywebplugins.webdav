from tiddlyweb.model.bag import Bag
from tiddlyweb.model.recipe import Recipe
from tiddlywebplugins.utils import get_store
from tiddlyweb.config import config


def populate_store():
    store = get_store(config)

    for bag_name in ["alpha", "bravo"]:
        bag = Bag(bag_name)
        store.put(bag)
    for recipe_name in ["omega"]:
        recipe = Recipe(recipe_name)
        store.put(recipe)
