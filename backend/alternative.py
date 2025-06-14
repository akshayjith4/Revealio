import sys
import pandas as pd
from gensim.models import Word2Vec
import re

# ✅ Load trained Word2Vec model
model_path = "ingredient_alternatives.model"
try:
    model = Word2Vec.load(model_path)
except Exception as e:
    print(f"Error loading model: {e}")
    sys.exit()

# ✅ Load CSV dictionary for direct mapping
file_path = "ingredient_alternative.csv"
try:
    df = pd.read_csv(file_path)
    df = df.dropna(subset=["Ingredient", "Alternative"])  # Remove missing values
    df["Ingredient"] = df["Ingredient"].str.lower().str.strip()
    df["Alternative"] = df["Alternative"].str.lower().str.strip()
    alternative_dict = dict(zip(df["Ingredient"], df["Alternative"]))
except Exception as e:
    print(f"Warning: Failed to load CSV alternatives: {e}")
    alternative_dict = {}

# ✅ Function to get ingredient alternative
def get_alternative(ingredients):
    if isinstance(ingredients, str):  
        ingredients = [ingredients]  # Convert single string to list

    alternatives = {}

    for ingredient in ingredients:
        ingredient = ingredient.lower().strip()

        # 🟢 Check CSV dictionary first
        if ingredient in alternative_dict:
            alternatives[ingredient] = alternative_dict[ingredient]
        else:
            # 🔵 Check Word2Vec model
            try:
                if ingredient in model.wv.key_to_index:
                    similar_ingredients = model.wv.most_similar(ingredient, topn=3)
                    alternatives[ingredient] = ", ".join([item[0] for item in similar_ingredients])
                else:
                    alternatives[ingredient] = "No suitable alternative found."
            except KeyError:
                alternatives[ingredient] = "No suitable alternative found."

    return alternatives

# ✅ Function to update recommendation.html with alternatives **and print alternatives only**
def update_html_report():
    try:
        with open("recommendation.html", "r", encoding="utf-8") as file:
            html_content = file.read()

        new_html_content = html_content

        # Find all ingredients in the HTML that need alternatives
        matches = re.findall(r"(\w[\w\s]*) → No alternative found", html_content)
        updated_ingredients = {}

        for ingredient in matches:
            ingredient = ingredient.lower().strip()
            alternative_dict = get_alternative([ingredient])  
            alternative = alternative_dict.get(ingredient, "No suitable alternative found.")

            updated_ingredients[ingredient] = alternative

            # Replace in HTML
            new_html_content = new_html_content.replace(
                f"{ingredient.capitalize()} → No alternative found",
                f"{ingredient.capitalize()} → Alternative: {alternative}"
            )

        # Write back the modified HTML content
        with open("recommendation.html", "w", encoding="utf-8") as file:
            file.write(new_html_content)

        # ✅ **Print only the alternatives (clean output)**
        for ing, alt in updated_ingredients.items():
            print(alt)

    except Exception as e:
        print(f"Error updating recommendation.html: {e}")

# ✅ Run update function
if __name__ == "__main__":
    update_html_report()
