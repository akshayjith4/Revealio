import sqlite3
import pandas as pd
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ✅ Load CSV file
csv_file = "ingredient.csv"
try:
    df = pd.read_csv(csv_file, encoding="ISO-8859-1")
    df["ingredient_name"] = df["ingredient_name"].str.lower().str.strip()  # Normalize ingredient names
except Exception as e:
    print(f"❌ Error loading CSV file: {e}")
    exit()

# ✅ Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# ✅ Function to Check Allergen Risk
def check_allergen_risk(username, extracted_text):
    db_file = "users.db"
    
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()

            # ✅ Fetch user details
            cursor.execute("SELECT allergies, health_conditions, diet FROM users WHERE username = ?", (username,))
            user_data = cursor.fetchone()

            if not user_data:
                return {"error": f"❌ {username}, we couldn't find your profile in our database."}

            # ✅ Extract user details
            user_allergies = set(filter(None, map(str.strip, user_data[0].lower().split(",")))) if user_data[0] and user_data[0] != "None" else set()
            user_conditions = set(filter(None, map(str.strip, user_data[1].lower().split(",")))) if user_data[1] and user_data[1] != "None" else set()
            user_diet = set(filter(None, map(str.strip, user_data[2].lower().split(",")))) if user_data[2] and user_data[2] != "None" else set()

            # ✅ Process extracted text (ingredients)
            raw_text = extracted_text.strip().lower()
            words = set(re.findall(r'\b[a-zA-Z0-9-]+\b', raw_text))  # Unique words only

            # ✅ Match ingredients with dataset
            dataset_ingredients = set(df["ingredient_name"].dropna().unique())
            valid_ingredients = words.intersection(dataset_ingredients)

            if not valid_ingredients:
                return {"result": f"❌ {username}, we couldn't find any valid ingredients in the dataset."}

            # ✅ Categorizing Ingredients
            analysis_results = []
            unsafe_ingredients = []

            for ingredient in valid_ingredients:
                row = df.loc[df["ingredient_name"] == ingredient]

                if row.empty:
                    continue  # Skip to next ingredient

                row = row.iloc[0]  # Get the first matching row

                # ✅ Extract relevant details
                ingredient_allergens = set(filter(None, map(str.strip, str(row["allergen_info"]).lower().split(",")))) if pd.notna(row["allergen_info"]) else set()
                ingredient_health_risks = set(filter(None, map(str.strip, str(row["health_conditions"]).lower().split(",")))) if pd.notna(row["health_conditions"]) else set()
                ingredient_diet_restrictions = set(filter(None, map(str.strip, str(row["Not_Suitable_for_Diets"]).lower().split(",")))) if pd.notna(row["Not_Suitable_for_Diets"]) else set()
                description = row["description"] if pd.notna(row["description"]) else "No detailed description available."

                # ✅ Check risk factors
                risky_ingredients = user_allergies.intersection(ingredient_allergens)
                health_warnings = user_conditions.intersection(ingredient_health_risks)
                diet_warnings = user_diet.intersection(ingredient_diet_restrictions)

                # ✅ Sentiment Analysis
                sentiment_score = analyzer.polarity_scores(description)["compound"]

                # ✅ Personalized Safety Classification
                safety_status = "Safe ✅"
                reasons = []

                if risky_ingredients or health_warnings or diet_warnings:
                    safety_status = "Not Safe ❌"
                    unsafe_ingredients.append(ingredient)
                    if risky_ingredients:
                        reasons.append(f"⚠️ **Allergens:** {', '.join(risky_ingredients)}")
                    if health_warnings:
                        reasons.append(f"⚠️ **Health Risks:** {', '.join(health_warnings)}")
                    if diet_warnings:
                        reasons.append(f"⚠️ **Not Suitable for Diet:** {', '.join(diet_warnings)}")
                elif sentiment_score > 0.5:
                    reasons.append(f"✅ **This ingredient is highly beneficial!** {description[:100]}...")  # Show the first 100 characters of the description as context
                elif sentiment_score > 0:
                    reasons.append(f"🙂 **This ingredient has some positive effects.** {description[:100]}...")  # Show the first 100 characters of the description as context
                else:
                    reasons.append(f"🤷 **Neutral impact.** {description[:100]}...")  # Show the first 100 characters of the description as context


                analysis_results.append({
                    "ingredient": ingredient.capitalize(),
                    "status": safety_status,
                    "description": description,
                    "reasons": reasons
                })

    except Exception as e:
        return {"error": f"❌ An unexpected error occurred: {e}"}

    # ✅ Construct result dictionary
    result_data = {
        "username": username,
        "analysis_results": analysis_results,
        "unsafe_ingredients": unsafe_ingredients,
        "message": "✅ This food is safe for you. Enjoy!" if not unsafe_ingredients else "❌ Some ingredients might not be safe for you."
    }

    return result_data
