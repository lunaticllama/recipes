"""Parser tests, using snippets copied from the real "Phil's Recipes" doc.

Run from the repo root:  python -m unittest discover -s scripts/tests -t scripts
"""
import unittest

from tests.helpers import make_doc

import parser as rp


def parse(snippet):
    return rp.parse_document(make_doc(snippet))


def one(snippet):
    result = parse(snippet)
    assert len(result.recipes) == 1, [r["title"] for r in result.recipes]
    return result.recipes[0]


def items(section, group=0):
    return section["ingredient_groups"][group]["items"]


def kinds(result, title):
    return {p["kind"] for p in result.problems if p["recipe"] == title}


# --- real snippets --------------------------------------------------------

ADANA = """
## Adana Kebab

Ingredients:
For the Kebabs:
500 grams (about 1 pound 2 ounces) ground lamb
Kosher salt
2 tablespoons ice-cold water

For Serving:
1 red onion, thinly sliced
Pickled sport peppers or pepperoncini

Directions:
1.\tFor the Kebabs: Combine lamb with 7.5 grams (about 2 teaspoons) kosher salt.

2.\tMeanwhile, combine remaining teaspoon cumin.
Using wet hands, divide lamb mixture into 12 even balls.
3.\tLight one chimney full of charcoal.

4.\tDuring last few minutes of cooking, place bread directly on top of kebabs.
"""

PULLED_PORK = """
## Pulled Pork
Pork Ingredients:
1 whole bone-in or boneless pork butt (5 to 7 pounds)\v1 tablespoons safflower oil
1 medium onion, minced
Traditional “Sweet and Tangy” BBQ Sauce (see recipe)

Pulled Pork Dry Rub Ingredients:\v2 tablespoons brown sugar\v2 teaspoons chili powder
\vDirections:
1.\tRub the Pulled Pork Dry Rub: Mix all the dry rub ingredients.

7.\tSeason, Reduce, Serve: Add in the reserved half of the uncooked BBQ sauce.

Serve with reserved BBQ sauce.
"""

BBQ = """
## Traditional “Sweet and Tangy” BBQ Sauce
Ingredients:\v3 garlic cloves, minced\v1 cup ketchup\v
Directions:
* Just mix together.  Can add juices from pulled pork or some dry rub for further flavor.  Used for pulled pork, ribs, and chicken.
"""

BREADSTICKS = """
## Breadsticks
For the Dough:
1 cup warm water (105°F -110°F) (240ml)
1 teaspoon salt

For the Topping:
2 tablespoons unsalted butter melted

Directions:

1.\tIn the mixing bowl of a stand mixer, whisk together water, yeast, and sugar.

2.\tBake for 15 to 17 minutes or until golden brown.

Recipe: <Breadsticks - Preppy Kitchen|https://preppykitchen.com/breadsticks/>
"""

LAMB_SHANKS = """
## Braised Lamb Shanks (Pressure Cooker)
Ingredients:
2 lamb shanks
1 onion, diced
1 strip of peeled lemon rind

Gremolata ingredients:
½ bunch of parsley
2 cloves of garlic, minced
"""

FALAFEL = """
## Falafel
Ingredients:
1½ cups dry chickpeas\v½ cup chopped fresh parsley\vBoth optional: Pinch cayenne pepper and a pinch ground cardamom\vSafflower or grapeseed oil for pan frying\v
Directions:
1.\tRinse chickpeas. Then drain and lightly rinse and dry thoroughly (method from< |http://www.thekitchn.com/how-to-quicksoak><the Kitchn|http://www.thekitchn.com/how-to-quicksoak>).
In the meantime, add parsley, onion and garlic to a food processor.

6.\tAdjust heat as needed if they're browning too quickly.
These falafel are delicious on their own with hummus or a tahini sauce.
To freeze, pan-fry falafel, let cool, then freeze up to 1 month.

Source: <http://minimalistbaker.com/classic-vegan-falafel-gf/|http://minimalistbaker.com/classic-vegan-falafel-gf/>

Easy Tahini Sauce:
Ingredients:
¼ cup tahini
Salt

Directions:
1.\tMix all ingredients together.
"""

KIMCHI_PANCAKE = """
## Kimchi Pancake(s)
Ingredients:
½ cup all-purpose flour\v½ cup rice flour
4 scallions, chopped

Directions:
1.\tIn a large bowl, combine the flour and rice flour.
\v2.\tHeat a nonstick or cast iron pan over medium high heat.

Source: <http://thewoksoflife.com/2016/12/kimchi-pancake/|http://thewoksoflife.com/2016/12/kimchi-pancake/>

Dipping Sauce:
Ingredients:\v3 tablespoons soy sauce\v1 teaspoon sesame seeds

Directions:
Stir all of the ingredients together.

Source: <http://www.beyondkimchee.com/seafood-pancakes/|http://www.beyondkimchee.com/seafood-pancakes/>
"""

PORK_CUTLETS = """
## Pork Cutlets (or chicken)
Ingredients:
1 egg
Lemon, capers, arugula

Directions:
1.\tPut flour in rimmed plate.

3.\tServe with lemon juice and capers or the below beet puree.

Chicken Variation:
Do everything same but replace the pork cutlets with chicken breasts.

Beet Puree:
Ingredients:
1 small shallot, chopped\v1 small red beet, peeled, thinly sliced
Olive oil

Directions:
1.\tHeat olive oil in a small saucepan over medium-low.

Source: <http://www.bonappetit.com/recipe/pork-katsu-with-beet-puree|http://www.bonappetit.com/recipe/pork-katsu-with-beet-puree>
"""

STEAK = """
## Steak
Ingredients:
Steaks, I prefer New York Strip Steak
Salt and black pepper

Directions:
1.\tThoroughly dry steaks with paper towels.

5.\tLet the steaks rest covered for 10 minutes, and then serve.

Spicy Fennel Steak
Ingredients:
1-2 tablespoons of fennel seeds

Directions:
1.\tSmash fennel seed and mix with red pepper flakes.

Asian Marinade
Ingredients:
¼ cup soy sauce
1” ginger, peeled and sliced

Directions:
1.\tIn step one above, add them to a large, plastic zip-lock bag.
"""

ENCHILADAS = """
## Veggie Rojo Enchiladas
Ingredients:
2 cups homemade enchilada sauce\v2 tablespoons olive oil\v
Directions:
1.\tPreheat oven to 400 degrees Fahrenheit.\v2.\tIn a large skillet over medium heat, warm the olive oil.

Other Vegetable Fillings:
-one or two roasted sweet potatoes, black beans, and 1 onion (all sauteed)
-one or two zucchini or summer squash, black beans (all sauteed)

Homemade enchilada sauce
Ingredients:
3 tablespoons olive oil\v2 cups vegetable broth\v
Directions:\v1.\tMeasure the dry ingredients into a small bowl.\vIn a medium-sized pot over medium heat, warm the oil.\v2.\tOnce it's ready, pour in the flour and spice mixture.

Source: <http://cookieandkate.com/2016/vegetarian-enchiladas-recipe/|http://cookieandkate.com/2016/vegetarian-enchiladas-recipe/>
"""

QUESADILLAS = """
## Quesadillas, Several Types
Kimchi Quesadillas
Ingredients:\v2 Tbsp butter\v2 flour tortillas
Hot sauce, to taste\v
Directions:\v1.\tSauté the kimchi: Melt 1 1/2 Tbsp of butter.\v\v2.\tHeat the flour tortilla.\v
4.\tServe with sliced avocado and hot sauce, if desired.\v\vSource: <http://www.simplyrecipes.com/recipes/kimchi_avocado_quesadilla/|http://www.simplyrecipes.com/recipes/kimchi_avocado_quesadilla/>

Kale, Poblano, and Black Bean Quesadillas
Ingredients:
Leftover taco filling from the Kale, Poblano, and Black Bean Tacos, or make from scratch if desired

Directions:
1.\tSame as above, but substitute the kale, poblano, and black bean mixture for the kimchi.
"""

TOFU_STIR_FRY = """
## Tofu Stir Fry
Ingredients:
1 package extra-firm tofu
Oil for stir frying (coconut, safflower, or peanut are best)

Directions:
1.\tHeat oven to 400F.

4.\tThen add sauce to pan and stir continuously for several minutes.

Basic Stir Fry Sauce
Ingredients:
2 large cloves garlic, minced\v1 Tbsp ginger, minced
1 Tbsp Shaoxing wine, rice wine, sherry, sake, brandy, or white wine

Hot and Sour Sauce
Ingredients:
4 large garlic cloves, grated\v1 teaspoon honey
"""

GENERAL_TSO = """
## General Tso’s Stir Fry
Ingredients:

Sauce:
2 tsp sesame oil\v2 tsp cornstarch
1 Tbsp water

Tofu:\v12 ounces extra firm tofu\v2 Tbsp neutral oil (such as grape seed or canola)
\vStir Fry:\v1 Tbsp (15 ml) sesame oil\v4-7 dried red chilies\v
General Tso’s Special Directions:
1.\tPlace all tofu ingredients besides tofu and cornstarch in bowl.

3.\tReserve fried tofu as needed.

Source: <http://minimalistbaker.com/general-tsos-tofu/|http://minimalistbaker.com/general-tsos-tofu/>
"""

THAI_BOWLS = """
## Thai Noodle Bowls with Tofu and Veggies
Ingredients:
Tofu:
8 oz extra firm tofu\v3 tbs sesame oil, divided\v3 tbs cornstarch

Salad:\v5 oz very thin rice noodles\v2 carrots, thinly sliced
1 jalapeno, diced
\vDressing:\v2 cloves garlic, minced
1 tbs sesame oil
\vDirections:\v1.\tStart by wrapping tofu in a clean towel.
\v2.\tPrepare the tofu sauce in a medium mixing bowl.

Source: <http://minimalistbaker.com/thai-noodle-bowls-almond-butter-tofu/|http://minimalistbaker.com/thai-noodle-bowls-almond-butter-tofu/>
"""

ROAST_FISH = """
## Basic Roast Fish
Ingredients:
1 lemon
Olive oil

Directions:
1.\tPreheat oven to 400F or 350F.

3.\tPut in oven.

Watercress Sauce for Fish
Ingredients:
8 Tbs parsley, about ½ a bunch\vA bunch of watercress\vOlive oil
2 Tbs Hemp seeds (optional)\v\vDirections:
1.\tChop everything in a food processor.
"""

BASIC_CURRY = """
## Basic Curry and Variations
Ingredients:
1 onion, chopped
1 cup cilantro leaves

Directions:
1.\tCombine garlic, ginger, chilies.
\v2.\tHeat oil in a large saucepan.\v\v3.\tImmediately add garlic paste.

Variations: substitute for chickpeas, pressed and baked tofu (see Tofu Stir Fry for technique), spinach, kale.

Coconut Milk Variation

Additional Ingredients:
1 tsp. sea salt, to taste\v1 tsp. ground cumin

14-ounce package of extra firm tofu, drained well
3 medium carrots, 1” thick sliced on a diagonal

Directions:
1.\tDon’t use any chilis with the garlic/ginger paste.

2.\tAt this point, you can transfer sauce to a blender. \v\v3.\tCut the tofu into 1” cubes.

Sources: <http://www.seriouseats.com/2016/04/best-channa-masala.html|http://www.seriouseats.com/2016/04/best-channa-masala.html>

<http://www.sproutedkitchen.com/vegetables-tofu-in-curry-sauce|http://www.sproutedkitchen.com/vegetables-tofu-in-curry-sauce>
"""

JERK_CHICKEN = """
## Jerk Chicken
Ingredients:
½ cup of soy sauce
1-2 scotch bonnets/habanero, seeded and chopped (2 will definitely be hotter)

3-4 lbs skin-on chicken thighs, with skin trimmed
Salt

Directions:
1.\tWash and thoroughly pat dry chicken thighs.  Salt both sides of thighs and and put in
fridge for several hours.

2.\tPut together all ingredients other than the chicken and puree.
"""

PUMPKIN_RAVIOLI = """
## Pumpkin Ravioli
Ingredients:
Fresh pasta dough

Directions:

Source:
<https://ohsheglows.com/2012/09/10/how-to-roast-a-sugar-pumpkin/|https://ohsheglows.com/2012/09/10/how-to-roast-a-sugar-pumpkin/>
<https://www.seriouseats.com/butternut-squash-ravioli-recipe|https://www.seriouseats.com/butternut-squash-ravioli-recipe>
"""

MOROCCAN = """
## Moroccan Grilled Chicken

Ingredients:
1½ to 1¾ pounds boneless skinless chicken breasts
¼ cup extra virgin olive oil

Directions:
1.\tPound out chicken breasts to even thickness, marinate 5-6 hours with the rest of the ingredients, and grill.
"""

# Moussaka as it was before Phil fixed it: its one step copied from Moroccan.
MOUSSAKA_OLD = """
## Moussaka
Ingredients:

Eggplant & Potato Layer:
2 large eggplants, sliced into 1/4-inch rounds
Olive oil, for brushing

Directions:
1.\tPound out chicken breasts to even thickness, marinate 5-6 hours with the rest of the ingredients, and grill.
"""

# Bigos as it was before Phil fixed it: no directions.
BIGOS_OLD = """
## Bigos
Ingredients:
~1 lb kielbasa, sliced
~1 lb stew beef, cubed
1 cup beef broth

Source: <Bigos (Polish Hunter's Stew) Recipe|https://www.seriouseats.com/from-a-polish-country-house-kitchens-hunters>
"""


class LabelledIngredientGroups(unittest.TestCase):
    def test_adana_groups(self):
        r = one(ADANA)
        groups = r["sections"][0]["ingredient_groups"]
        self.assertEqual([g.get("name") for g in groups], ["For the Kebabs", "For Serving"])
        self.assertEqual(groups[0]["items"][1], "Kosher salt")
        self.assertEqual(groups[1]["items"][-1], "Pickled sport peppers or pepperoncini")

    def test_adana_step_starting_with_group_name_is_still_a_step(self):
        r = one(ADANA)
        steps = r["sections"][0]["steps"]
        self.assertEqual(len(steps), 4)
        self.assertTrue(steps[0].startswith("For the Kebabs: Combine lamb"))

    def test_pulled_pork_groups_without_plain_ingredients_label(self):
        r = one(PULLED_PORK)
        groups = r["sections"][0]["ingredient_groups"]
        self.assertEqual([g.get("name") for g in groups],
                         ["Pork Ingredients", "Pulled Pork Dry Rub Ingredients"])
        self.assertEqual(len(groups[0]["items"]), 4)
        self.assertEqual(groups[1]["items"], ["2 tablespoons brown sugar", "2 teaspoons chili powder"])

    def test_breadsticks_groups_at_recipe_start(self):
        r = one(BREADSTICKS)
        groups = r["sections"][0]["ingredient_groups"]
        self.assertEqual([g.get("name") for g in groups], ["For the Dough", "For the Topping"])
        self.assertEqual(len(r["sections"]), 1)

    def test_gremolata_group(self):
        r = one(LAMB_SHANKS)
        groups = r["sections"][0]["ingredient_groups"]
        self.assertEqual(groups[1]["name"], "Gremolata ingredients")
        self.assertEqual(groups[1]["items"], ["½ bunch of parsley", "2 cloves of garlic, minced"])

    def test_general_tso_groups_and_prefixed_directions_label(self):
        r = one(GENERAL_TSO)
        self.assertEqual(len(r["sections"]), 1)
        s = r["sections"][0]
        self.assertEqual([g["name"] for g in s["ingredient_groups"]], ["Sauce", "Tofu", "Stir Fry"])
        self.assertEqual(s["ingredient_groups"][2]["items"][-1], "4-7 dried red chilies")
        self.assertEqual(len(s["steps"]), 2)

    def test_thai_bowls_groups_across_soft_breaks(self):
        r = one(THAI_BOWLS)
        s = r["sections"][0]
        self.assertEqual([g["name"] for g in s["ingredient_groups"]], ["Tofu", "Salad", "Dressing"])
        self.assertEqual(s["ingredient_groups"][1]["items"],
                         ["5 oz very thin rice noodles", "2 carrots, thinly sliced", "1 jalapeno, diced"])
        self.assertEqual(len(s["steps"]), 2)

    def test_unlabelled_block_after_blank_line_is_a_new_group(self):
        r = one(JERK_CHICKEN)
        groups = r["sections"][0]["ingredient_groups"]
        self.assertEqual(len(groups), 2)
        self.assertIsNone(groups[1].get("name"))
        self.assertEqual(groups[1]["items"][0], "3-4 lbs skin-on chicken thighs, with skin trimmed")

    def test_wrapped_step_line_joins_its_step(self):
        r = one(JERK_CHICKEN)
        steps = r["sections"][0]["steps"]
        self.assertEqual(len(steps), 2)
        self.assertIn("put in fridge for several hours.", steps[0])

    def test_colon_inside_line_is_not_a_group(self):
        r = one(FALAFEL)
        self.assertIn("Both optional: Pinch cayenne pepper and a pinch ground cardamom",
                      items(r["sections"][0]))
        self.assertEqual(len(r["sections"][0]["ingredient_groups"]), 1)


class SubRecipes(unittest.TestCase):
    def test_falafel_tahini_sauce(self):
        r = one(FALAFEL)
        self.assertEqual([s.get("name") for s in r["sections"]], [None, "Easy Tahini Sauce"])
        self.assertEqual(items(r["sections"][1]), ["¼ cup tahini", "Salt"])
        self.assertEqual(r["sections"][1]["steps"], ["Mix all ingredients together."])
        self.assertEqual(r["sources"][0]["url"], "http://minimalistbaker.com/classic-vegan-falafel-gf/")

    def test_falafel_link_inside_step(self):
        step = one(FALAFEL)["sections"][0]["steps"][0]
        self.assertIn("(method from [the Kitchn](http://www.thekitchn.com/how-to-quicksoak)).", step)

    def test_falafel_text_after_last_step_stays_with_it(self):
        steps = one(FALAFEL)["sections"][0]["steps"]
        self.assertEqual(len(steps), 2)
        self.assertIn("These falafel are delicious", steps[1])
        self.assertIn("To freeze", steps[1])

    def test_kimchi_pancake_dipping_sauce(self):
        r = one(KIMCHI_PANCAKE)
        self.assertEqual([s.get("name") for s in r["sections"]], [None, "Dipping Sauce"])
        self.assertEqual(items(r["sections"][1]), ["3 tablespoons soy sauce", "1 teaspoon sesame seeds"])
        self.assertEqual(r["sections"][1]["steps"], ["Stir all of the ingredients together."])
        self.assertEqual(len(r["sources"]), 2)

    def test_pork_cutlets_variation_note_and_beet_puree(self):
        r = one(PORK_CUTLETS)
        self.assertEqual([s.get("name") for s in r["sections"]], [None, "Beet Puree"])
        self.assertEqual(r["sections"][0]["notes"],
                         [{"name": "Chicken Variation",
                           "text": "Do everything same but replace the pork cutlets with chicken breasts."}])
        self.assertEqual(len(r["sections"][1]["steps"]), 1)

    def test_steak_short_lines_start_sub_recipes(self):
        r = one(STEAK)
        self.assertEqual([s.get("name") for s in r["sections"]], [None, "Spicy Fennel Steak", "Asian Marinade"])
        self.assertEqual(len(r["sections"][0]["steps"]), 2)
        self.assertEqual(items(r["sections"][2]), ["¼ cup soy sauce", "1” ginger, peeled and sliced"])

    def test_enchiladas_note_and_sauce(self):
        r = one(ENCHILADAS)
        self.assertEqual([s.get("name") for s in r["sections"]], [None, "Homemade enchilada sauce"])
        self.assertEqual(len(r["sections"][0]["steps"]), 2)
        note = r["sections"][0]["notes"][0]
        self.assertEqual(note["name"], "Other Vegetable Fillings")
        self.assertEqual(len(note["text"].split("\n")), 2)
        sauce_steps = r["sections"][1]["steps"]
        self.assertEqual(len(sauce_steps), 2)
        self.assertIn("\nIn a medium-sized pot", sauce_steps[0])

    def test_quesadillas_first_section_is_named(self):
        r = one(QUESADILLAS)
        self.assertEqual([s.get("name") for s in r["sections"]],
                         ["Kimchi Quesadillas", "Kale, Poblano, and Black Bean Quesadillas"])
        self.assertEqual(len(r["sections"][0]["steps"]), 3)
        self.assertEqual(len(r["sources"]), 1)

    def test_tofu_stir_fry_ingredient_only_sauces(self):
        r = one(TOFU_STIR_FRY)
        self.assertEqual([s.get("name") for s in r["sections"]],
                         [None, "Basic Stir Fry Sauce", "Hot and Sour Sauce"])
        self.assertEqual(len(items(r["sections"][1])), 3)
        self.assertEqual(items(r["sections"][2]), ["4 large garlic cloves, grated", "1 teaspoon honey"])
        self.assertEqual(r["sections"][1]["steps"], [])

    def test_watercress_sauce(self):
        r = one(ROAST_FISH)
        self.assertEqual([s.get("name") for s in r["sections"]], [None, "Watercress Sauce for Fish"])
        self.assertEqual(len(items(r["sections"][1])), 4)


class MultipleDirections(unittest.TestCase):
    def test_roast_fish_two_direction_blocks(self):
        r = one(ROAST_FISH)
        self.assertEqual([len(s["steps"]) for s in r["sections"]], [2, 1])

    def test_basic_curry(self):
        r = one(BASIC_CURRY)
        self.assertEqual([s.get("name") for s in r["sections"]], [None, "Coconut Milk Variation"])
        self.assertEqual([len(s["steps"]) for s in r["sections"]], [3, 3])
        self.assertEqual(r["sections"][0]["notes"][0]["name"], "Variations")
        groups = r["sections"][1]["ingredient_groups"]
        self.assertEqual(groups[0]["name"], "Additional Ingredients")
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(r["sources"]), 2)


class StepsWithoutLabels(unittest.TestCase):
    def test_numbered_lines_without_directions_label(self):
        r = one("""
        ## Chili Oil
        Ingredients:
        1 cup chili flakes or more
        1 clove garlic, minced

        1.\tFry garlic, shallot, and chili flakes in oil for 5 minutes.

        2.\tPour into mason jar and mix in other ingredients.
        """)
        self.assertEqual(items(r["sections"][0]), ["1 cup chili flakes or more", "1 clove garlic, minced"])
        self.assertEqual(len(r["sections"][0]["steps"]), 2)

    def test_ingredients_only_recipe_is_kept_and_flagged(self):
        result = parse("""
        ## Basic Stir Fry Sauce
        Ingredients:
        2 large cloves garlic, minced\v1 Tbsp ginger, minced
        1 Tbsp Sambal Oelek, Siracha, or other hot sauce
        """)
        self.assertEqual(len(items(result.recipes[0]["sections"][0])), 3)
        self.assertIn("no-steps", kinds(result, "Basic Stir Fry Sauce"))

    def test_unnumbered_directions_become_one_step(self):
        r = one(BBQ)
        self.assertEqual(len(r["sections"][0]["steps"]), 1)


class ProblemReport(unittest.TestCase):
    def test_pumpkin_ravioli_flagged(self):
        result = parse(PUMPKIN_RAVIOLI)
        self.assertTrue({"empty-directions", "no-steps", "short"} <= kinds(result, "Pumpkin Ravioli"))
        self.assertEqual(len(result.recipes[0]["sources"]), 2)

    def test_bigos_without_directions_flagged(self):
        result = parse(BIGOS_OLD)
        self.assertIn("no-steps", kinds(result, "Bigos"))

    def test_moussaka_copied_step_flagged(self):
        result = parse(MOROCCAN + MOUSSAKA_OLD)
        self.assertIn("copied-step", kinds(result, "Moussaka"))

    def test_lamb_shanks_flagged(self):
        result = parse(LAMB_SHANKS)
        self.assertIn("no-steps", kinds(result, "Braised Lamb Shanks (Pressure Cooker)"))

    def test_empty_ingredients_flagged(self):
        result = parse("""
        ## Tzatziki Sauce
        Ingredients:

        Combine 1 cup of greek yogurt with 1 cucumber (peeled and pitted), diced small, salt, pepper, and lemon
        juice to taste.  If you don’t have lemon juice, it will be fine.

        Directions:
        """)
        r = result.recipes[0]
        self.assertTrue({"empty-ingredients", "empty-directions"} <= kinds(result, "Tzatziki Sauce"))
        self.assertIn("guess", kinds(result, "Tzatziki Sauce"))
        self.assertEqual(len(r["sections"][0]["notes"]), 1)
        self.assertIn("juice to taste", r["sections"][0]["notes"][0]["text"])

    def test_good_recipes_are_not_flagged(self):
        result = parse(ADANA + FALAFEL + STEAK + TOFU_STIR_FRY + BASIC_CURRY)
        self.assertEqual([p for p in result.problems if p["kind"] not in ("guess", "cross-link")], [])

    def test_merged_ingredients_line_flagged(self):
        result = parse("""
        ## Cheddar Biscuits (Like Red Lobster)
        Ingredients:
        1/2 teaspoon baking soda1 teaspoon garlic powder
        360 g water about 1 1/2 cups + 1 Tbsp
        500 grams (about 1 pound 2 ounces) ground lamb
        1 dried birds eye chili, crushed (or sub 1/4 tsp red pepper flake)
        1 fresh chili, diced, or sub 1/4 tsp red pepper flake
        3 cups grated cheddar cheese, divided 2 cups and 1 cup
        Safflower/coconut/peanut oil, typically 2-4 tbs

        Directions:
        * Preheat oven to 425°F (218°C).
        """)
        guesses = [p["detail"] for p in result.problems if p["kind"] == "guess"]
        self.assertEqual(len(guesses), 1)
        self.assertIn("baking soda1", guesses[0])

    def test_report_text_names_recipe_and_line(self):
        result = parse(PUMPKIN_RAVIOLI)
        text = rp.format_report(result)
        self.assertIn("Pumpkin Ravioli", text)
        self.assertIn("1 recipe", text)


PUMPKIN_RAVIOLI_NEW = """
## Pumpkin Ravioli
Ingredients:
Fresh egg pasta dough
4 garlic cloves, roasted and mashed into a puree

Directions:
1.\tCombine roasted squash, garlic, cheese and herbs.

2.\tRoll out fresh pasta dough into sheets.

3,\tSpoon approximately a tablespoon of the squash mixture along a sheet of pasta.
Source:
Note: This is the best recipe for roasting sugar pumpkins I have found: <https://ohsheglows.com/roast-a-sugar-pumpkin/|https://ohsheglows.com/roast-a-sugar-pumpkin/>


<https://bigflavorstinykitchen.com/roasted-sweet-potato-ravioli/|https://bigflavorstinykitchen.com/roasted-sweet-potato-ravioli/>
<https://www.seriouseats.com/butternut-squash-ravioli-recipe|https://www.seriouseats.com/butternut-squash-ravioli-recipe>
"""


class DocTypos(unittest.TestCase):
    def test_step_number_typed_with_comma_is_a_step_and_flagged(self):
        result = parse(PUMPKIN_RAVIOLI_NEW)
        steps = result.recipes[0]["sections"][0]["steps"]
        self.assertEqual(len(steps), 3)
        self.assertTrue(steps[2].startswith("Spoon approximately"))
        guesses = [p["detail"] for p in result.problems if p["kind"] == "guess"]
        self.assertTrue(any("3," in g for g in guesses), guesses)

    def test_step_number_missing_its_period_is_a_step_and_flagged(self):
        result = parse("""
        ## Aunt Kathy's Hot Crab Dip
        Ingredients:\v1/2 to 1 lb. crab, picked over\v8 oz. cream cheese\v
        Directions:\v1\tSoften cream cheese and then mix all ingredients together.
        \v2.\tBake 350° 30 minutes and serve with bread or crackers.
        """)
        steps = result.recipes[0]["sections"][0]["steps"]
        self.assertEqual(steps, ["Soften cream cheese and then mix all ingredients together.",
                                 "Bake 350° 30 minutes and serve with bread or crackers."])
        guesses = [p["detail"] for p in result.problems if p["kind"] == "guess"]
        self.assertTrue(any("“1”" in g for g in guesses), guesses)
        self.assertEqual([p for p in result.problems if p["kind"] == "dropped"], [])

    def test_unnumbered_direction_starting_with_lowercase_after_number_is_left_alone(self):
        r = one("""
        ## Brown Rice (Pressure Cooker)
        Ingredients:
        1 cup of brown rice
        Directions:
        2 cups of water go in first, then the rice.
        """)
        self.assertEqual(r["sections"][0]["steps"], ["2 cups of water go in first, then the rice."])

    def test_mistyped_step_number_line_is_not_reported_as_dropped(self):
        result = parse(PUMPKIN_RAVIOLI_NEW)
        self.assertEqual([p for p in result.problems if p["kind"] == "dropped"], [])

    def test_comma_number_in_ingredients_is_not_a_step(self):
        r = one("""
        ## Lentil and Bean Chili
        Ingredients:
        2, 15-ounce cans diced tomatoes
        Directions:
        1.\tHeat a large pot.
        """)
        self.assertEqual(items(r["sections"][0]), ["2, 15-ounce cans diced tomatoes"])

    def test_links_after_a_note_in_sources_stay_sources(self):
        r = one(PUMPKIN_RAVIOLI_NEW)
        self.assertEqual([s["url"] for s in r["sources"]],
                         ["https://bigflavorstinykitchen.com/roasted-sweet-potato-ravioli/",
                          "https://www.seriouseats.com/butternut-squash-ravioli-recipe"])
        self.assertEqual(len(r["notes"]), 1)
        self.assertIn("ohsheglows.com", r["notes"][0]["text"])
        self.assertNotIn("seriouseats", r["notes"][0]["text"])

    def test_pumpkin_ravioli_links_to_fresh_egg_pasta_dough(self):
        result = parse(PUMPKIN_RAVIOLI_NEW + "## Fresh Egg Pasta Dough\nIngredients:\n2 whole large eggs\n")
        first = result.recipes[0]["sections"][0]["ingredient_groups"][0]["items"][0]
        self.assertEqual(first, "[Fresh egg pasta dough](recipe:fresh-egg-pasta-dough)")


class Cleanup(unittest.TestCase):
    def test_soft_breaks_split_lines(self):
        r = one("""
        ## Aunt Kathy's Hot Crab Dip
        Ingredients:\v1/2 to 1 lb. crab, picked over\v8 oz. cream cheese\vSalt\v
        Directions:\v1.\tSoften cream cheese.
        \v2.\tBake 350° 30 minutes and serve with bread or crackers.
        """)
        self.assertEqual(items(r["sections"][0]), ["1/2 to 1 lb. crab, picked over", "8 oz. cream cheese", "Salt"])
        self.assertEqual(r["sections"][0]["steps"],
                         ["Soften cream cheese.", "Bake 350° 30 minutes and serve with bread or crackers."])

    def test_zero_width_and_punctuation_only_lines_ignored(self):
        r = one("""
        ## Rasta Pasta
        Ingredients:
        1 lb chicken​ breast
        Directions:
        1.\tSeason chicken.
        .
        ‌
        2.\tRemove chicken.
        """)
        self.assertEqual(items(r["sections"][0]), ["1 lb chicken breast"])
        self.assertEqual(r["sections"][0]["steps"], ["Season chicken.", "Remove chicken."])

    def test_empty_heading_ignored(self):
        result = parse("""
        ## Brown Rice (Pressure Cooker)
        Ingredients:
        1 cup of brown rice
        Directions:
        1.\tPut brown rice and water in pressure cooker.
        ##
        ## Jerk Chicken
        Ingredients:
        Salt
        """)
        self.assertEqual([r["title"] for r in result.recipes], ["Brown Rice (Pressure Cooker)", "Jerk Chicken"])

    def test_title_heading_level_is_detected(self):
        result = parse("""
        # Brown Rice
        Ingredients:
        1 cup of brown rice
        # Steak
        Ingredients:
        Salt
        """)
        self.assertEqual([r["title"] for r in result.recipes], ["Brown Rice", "Steak"])

    def test_double_spaces_collapse(self):
        r = one(JERK_CHICKEN)
        self.assertNotIn("  ", r["sections"][0]["steps"][0])


class StepNumbers(unittest.TestCase):
    def test_variants(self):
        r = one("""
        ## Baguettes
        Ingredients:
        500 g all purpose flour
        1.75 - 2 lbs chicken cutlets
        Directions:
        1.\tMix all ingredients in a bowl.
        2. Preheat the oven to 500F.
        3\t.Stretch each dough rectangle slightly.
        4. \tPlace on a lightly floured couche.
        """)
        self.assertEqual(items(r["sections"][0]), ["500 g all purpose flour", "1.75 - 2 lbs chicken cutlets"])
        self.assertEqual(r["sections"][0]["steps"],
                         ["Mix all ingredients in a bowl.", "Preheat the oven to 500F.",
                          "Stretch each dough rectangle slightly.", "Place on a lightly floured couche."])

    def test_docs_list_items_are_steps(self):
        r = one("""
        ## Cheddar Biscuits (Like Red Lobster)
        Ingredients:
        1 cup (125g) shredded cheddar cheese
        Directions:

        * Preheat oven to 425°F (218°C).

        * Place the flour in a large bowl.
        """)
        self.assertEqual(r["sections"][0]["steps"], ["Preheat oven to 425°F (218°C).", "Place the flour in a large bowl."])

    def test_repeated_step_number_flagged(self):
        result = parse("""
        ## Pasta Broccoli Bolognese
        Ingredients:
        1 large head of broccoli
        Directions:
        1.\tBring a large pot of water to a rolling boil.
        2.\tHeat 2 Tbsp. oil in a large skillet.
        3.\tSalt water, and cook pasta.
        3.\tWhile pasta is cooking, add garlic.
        """)
        self.assertEqual(len(result.recipes[0]["sections"][0]["steps"]), 4)
        self.assertIn("guess", kinds(result, "Pasta Broccoli Bolognese"))


class Sources(unittest.TestCase):
    def test_linked_text(self):
        r = one(BREADSTICKS)
        self.assertEqual(r["sources"], [{"text": "Breadsticks - Preppy Kitchen", "url": "https://preppykitchen.com/breadsticks/"}])

    def test_bare_url_in_plain_text(self):
        r = one("""
        ## Kale Mushroom Salad Over Farro
        Ingredients:
        1 cup farro
        Directions:
        1.\tServe kale and mushroom salad over the farro.
        Source: http://thepioneerwoman.com/cooking/killer-kale-salad/
        """)
        self.assertEqual(r["sources"], [{"text": "http://thepioneerwoman.com/cooking/killer-kale-salad/",
                                         "url": "http://thepioneerwoman.com/cooking/killer-kale-salad/"}])

    def test_plain_text(self):
        r = one("""
        ## Lentil Soup (Phil’s Italian Lentil Soup)
        Ingredients:
        Olive oil
        Directions:
        1.\tSaute the carrots.
        Source: Phil’s own recipe
        """)
        self.assertEqual(r["sources"], [{"text": "Phil’s own recipe"}])

    def test_mixed_text_and_link(self):
        r = one("""
        ## Korean Spicy Beef Soup
        Ingredients:
        2 lbs brisket
        Directions:
        1.\tCut brisket into 1 inch cubes.
        Sources: Lucky Peach Spicy Beef Soup and <http://www.beyondkimchee.com/instant-pot-korean-beef-stew/|http://www.beyondkimchee.com/instant-pot-korean-beef-stew/>
        """)
        self.assertEqual(r["sources"], [
            {"text": "Lucky Peach Spicy Beef Soup"},
            {"text": "http://www.beyondkimchee.com/instant-pot-korean-beef-stew/",
             "url": "http://www.beyondkimchee.com/instant-pot-korean-beef-stew/"}])

    def test_text_on_line_after_source(self):
        r = one("""
        ## Pancakes
        Ingredients:
        2 large eggs
        Directions:
        1.\tWhisk eggs into milk.
        \vSource: <https://www.kingarthurbaking.com/recipes/simply-perfect-pancakes-recipe|https://www.kingarthurbaking.com/recipes/simply-perfect-pancakes-recipe>
        J Kenji Alt-Lopez on Instagram for yeasted version.
        """)
        self.assertEqual(len(r["sources"]), 2)
        self.assertEqual(r["sources"][1], {"text": "J Kenji Alt-Lopez on Instagram for yeasted version."})
        self.assertEqual(len(r["sections"][0]["steps"]), 1)

    def test_whitespace_link_before_real_link_is_dropped(self):
        r = one("""
        ## Cheddar Biscuits (Like Red Lobster)
        Ingredients:
        1 cup cheddar
        Directions:
        * Preheat oven.
        Source:< |https://sallysbakingaddiction.com/homemade-cheddar-biscuits/><https://sallysbakingaddiction.com/homemade-cheddar-biscuits|https://sallysbakingaddiction.com/homemade-cheddar-biscuits>
        """)
        self.assertEqual(r["sources"], [{"text": "https://sallysbakingaddiction.com/homemade-cheddar-biscuits",
                                         "url": "https://sallysbakingaddiction.com/homemade-cheddar-biscuits"}])

    def test_redirect_wrappers_are_unwrapped(self):
        result = parse("""
        ## Greek Lemon Chicken and Potatoes
        Ingredients:
        8 cloves garlic
        Directions:
        1. Add garlic to a blender.
        Source:< |https://url.us.m.mimecastprotect.com/s/HbkZ?domain=google.com><https://www.sipandfeast.com/greek-lemon-chicken/|https://url.us.m.mimecastprotect.com/s/HbkZ?domain=google.com>
        ## Hasselback Potato Gratin
        Ingredients:
        2 cups heavy cream
        Directions:
        * Heat oven to 400°F.
        Source:< |https://www.google.com/search?q=https://www.seriouseats.com/hasselback-potato-gratin-recipe><J. Kenji López-Alt via Serious Eats|https://www.google.com/search?q=https://www.seriouseats.com/hasselback-potato-gratin-recipe>
        """)
        a, b = result.recipes
        self.assertEqual(a["sources"], [{"text": "https://www.sipandfeast.com/greek-lemon-chicken/",
                                         "url": "https://www.sipandfeast.com/greek-lemon-chicken/"}])
        self.assertEqual(b["sources"], [{"text": "J. Kenji López-Alt via Serious Eats",
                                         "url": "https://www.seriouseats.com/hasselback-potato-gratin-recipe"}])

    def test_based_off_of_this(self):
        r = one("""
        ## Pad See Ew (Vegan or not)
        Ingredients:
        Cilantro
        Directions:
        1.\tServe with cilantro and siracha.
        Based off of this: <https://sahdcooks.blogspot.com/2014/09/pad-see-ew.html|https://sahdcooks.blogspot.com/2014/09/pad-see-ew.html>
        """)
        self.assertEqual(r["sources"][0]["url"], "https://sahdcooks.blogspot.com/2014/09/pad-see-ew.html")


class CrossLinks(unittest.TestCase):
    def test_pulled_pork_and_bbq_sauce_link_each_other(self):
        result = parse(PULLED_PORK + BBQ)
        pork, bbq = result.recipes
        self.assertIn("[Traditional “Sweet and Tangy” BBQ Sauce](recipe:traditional-sweet-and-tangy-bbq-sauce)",
                      pork["sections"][0]["ingredient_groups"][0]["items"][3])
        self.assertIn("[pulled pork](recipe:pulled-pork)", bbq["sections"][0]["steps"][0])

    def test_chili_oil_but_not_beef_stock(self):
        result = parse("""
        ## Beef Stock
        Ingredients:
        15 lbs of beef bone
        ## Chili Oil
        Ingredients:
        1 cup chili flakes or more
        ## Korean Spicy Beef Soup
        Ingredients:
        1 Tsp, Better than Bouillon beef stock seasoning
        Chili oil for serving, if desired
        Directions:
        1.\tIf using beef stock, omit the Better than Bouillon beef stock.
        """)
        soup = result.recipes[2]
        text = " ".join(items(soup["sections"][0]) + soup["sections"][0]["steps"])
        self.assertIn("[Chili oil](recipe:chili-oil) for serving", text)
        self.assertNotIn("recipe:beef-stock", text)

    def test_pancakes_never_linked(self):
        result = parse("""
        ## Cabbage Slaw (For Fritters, Pancakes and Tacos)
        Ingredients:
        1 Lime, juiced
        Directions:
        1.\tServe slaw on top of fritters, pancakes, or tacos.
        ## Pancakes
        Ingredients:
        2 large eggs
        """)
        self.assertNotIn("recipe:pancakes", str(result.recipes[0]))

    def test_missing_target_is_reported(self):
        result = parse(PULLED_PORK)
        self.assertIn("cross-link", kinds(result, "Pulled Pork"))


class NothingDropped(unittest.TestCase):
    SNIPPETS = [ADANA, PULLED_PORK, BBQ, BREADSTICKS, LAMB_SHANKS, FALAFEL, KIMCHI_PANCAKE,
                PORK_CUTLETS, STEAK, ENCHILADAS, QUESADILLAS, TOFU_STIR_FRY, GENERAL_TSO,
                THAI_BOWLS, ROAST_FISH, BASIC_CURRY, JERK_CHICKEN, PUMPKIN_RAVIOLI]

    def test_every_line_lands_somewhere(self):
        for snippet in self.SNIPPETS:
            result = parse(snippet)
            dropped = [p for p in result.problems if p["kind"] == "dropped"]
            self.assertEqual(dropped, [], snippet.split("\n")[1])

    def test_dropped_check_works(self):
        doc = make_doc(ADANA)
        lines = rp.doc_to_lines(doc)
        recipes = rp.parse_lines(lines)
        recipes[0]["sections"][0]["ingredient_groups"][0]["items"].pop()
        problems = rp.find_dropped(lines, recipes)
        self.assertEqual(len(problems), 1)
        self.assertIn("ice-cold water", problems[0]["detail"])


class Slugs(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(rp.slugify("Aunt Kathy's Hot Crab Dip"), "aunt-kathys-hot-crab-dip")
        self.assertEqual(rp.slugify("Thai “Puffy” Eggs"), "thai-puffy-eggs")
        self.assertEqual(rp.slugify("Lentil Soup (Phil’s Italian Lentil Soup)"), "lentil-soup-phils-italian-lentil-soup")
        self.assertEqual(rp.slugify("Pasta with Chickpeas [Pasta con Ceci]"), "pasta-with-chickpeas-pasta-con-ceci")
        self.assertEqual(rp.slugify("Gougères & Socca/Farinata"), "gougeres-socca-farinata")

    def test_recipe_has_slug_and_tags(self):
        r = one("""
        ## Steak
        Ingredients:
        Salt
        Tags: beef, quick
        """)
        self.assertEqual(r["slug"], "steak")
        self.assertEqual(r["tags"], ["beef", "quick"])
        self.assertEqual(items(r["sections"][0]), ["Salt"])


if __name__ == "__main__":
    unittest.main()
