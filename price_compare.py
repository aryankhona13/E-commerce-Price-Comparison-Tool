# Import 'requests' so Python can open web pages, like a browser does.
import requests

# Import 'quote_plus' so spaces in the search text become "+" in the web address.
from urllib.parse import quote_plus

# Import BeautifulSoup so we can read the HTML of a page and find things in it.
from bs4 import BeautifulSoup

# Import 're' (regular expressions) so we can find numbers and whole words in text.
import re

# ============================================================
# SHOP SETTINGS
# Each shop has 4 settings:
#   search_url: the shop's search page. {query} is replaced by what you type.
#   card: the box that holds one product on the search page.
#   title: the product name inside that box.
#   price: the current price inside that box.
# ============================================================

# A dictionary that holds the settings for each shop.
SHOPS = {
    # Start the FlyRobo settings.
    "FlyRobo": {
        # The FlyRobo search page address, with {query} where the product name goes.
        "search_url": "https://www.flyrobo.in/index.php?route=product/search&search={query}&description=true",
        # On FlyRobo, each product box has this class name.
        "card": ".product-thumb",
        # On FlyRobo, the product name is inside a tag with this class name.
        "title": ".name",
        # On FlyRobo, the current price is inside a tag with this class name.
        "price": ".price-new",
    },
    # Start the Robocraze settings.
    "Robocraze": {
        # The Robocraze search page address, with {query} where the product name goes.
        "search_url": "https://robocraze.com/search?q={query}&options%5Bprefix%5D=last&type=product",
        # On Robocraze, each product box has this class name.
        "card": ".card-information",
        # On Robocraze, the product name is inside a tag with this class name.
        "title": ".card-title",
        # On Robocraze, the sale price is inside a tag with this class name.
        "price": ".price-item--sale",
    },
    # Start the Ktron settings.
    "Ktron": {
        # The Ktron search page address, with {query} where the product name goes.
        "search_url": "https://www.ktron.in/?s={query}&post_type=product",
        # On Ktron, each product box is a list item with class "product".
        "card": "li.product",
        # On Ktron, the product name is inside an h2 tag in this box.
        "title": ".mf-product-details-hover h2",
        # On Ktron, the sale price is inside an ins tag in this box.
        "price": ".mf-product-details-hover ins",
    },
}

# Words that usually mean an accessory, not the main product.
# Products with these words get a big penalty, so they rank below the real product.
ACCESSORY_WORDS = ["shield", "case", "cover", "stand", "holder", "sticker", "bag", "adapter", "cable"]

# Pretend to be a normal web browser, so the shops do not reject the request.
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

# This function takes text like "Rs. 1,299.00" and returns the number 1299.0.
def get_number(text):
    # Search the text for the first number, allowing commas and a decimal point.
    match = re.search(r"\d[\d,]*(?:\.\d+)?", text)
    # If no number was found, return None (nothing).
    if not match:
        return None
    # Remove the commas (so 1,200 becomes 1200) and turn the text into a number.
    return float(match.group().replace(",", ""))


# This function counts how many search words are in a product name.
def count_matching_words(title, search_text):
    # Make the product name lowercase, so "Arduino" and "arduino" are the same.
    title = title.lower()
    # Split what the user typed into single words, all in lowercase.
    words = search_text.lower().split()

    # Start the count of search words found in the name at 0.
    found = 0
    # Check each word the user typed.
    for word in words:
        # If this whole word appears in the name (not as part of a longer word)...
        if re.search(r"\b" + re.escape(word) + r"\b", title):
            # ...add 1 to the count.
            found += 1

    # Start the count of accessory words at 0.
    accessories = 0
    # Check each accessory word in our list.
    for bad_word in ACCESSORY_WORDS:
        # Count it only if the user did not type that word and it appears in the name.
        if bad_word not in words and re.search(r"\b" + bad_word + r"\b", title):
            # Add 1 to the accessory count.
            accessories += 1

    # Give back the three numbers: words found, accessory words, and total words typed.
    return found, accessories, len(words)


# This function finds the closest matching product on one shop.
def find_best_product(settings, search_text):
    # Put the search text into the shop's search address (spaces become "+").
    url = settings["search_url"].replace("{query}", quote_plus(search_text))

    # "try" means: attempt the steps below, and if something fails, do not crash.
    try:
        # Ask the shop for the page. Stop waiting after 15 seconds.
        response = requests.get(url, headers=HEADERS, timeout=15)
        # If the shop sent an error (for example 403 or 404), raise an error here.
        response.raise_for_status()
    # If anything went wrong with the request, run the code below.
    except requests.RequestException as error:
        # Show the reason on the screen.
        print(f"    Could not open page: {error}")
        # Give back nothing for this shop.
        return None

    # Read the page HTML so we can search inside it.
    soup = BeautifulSoup(response.text, "html.parser")
    # Find every product box on the page, using this shop's card setting.
    cards = soup.select(settings["card"])

    # Start with no best product yet.
    best = None
    # Start with no best score yet.
    best_score = None

    # Look at each product box, one at a time.
    for card in cards:
        # Find the product name tag inside this box.
        title_tag = card.select_one(settings["title"])
        # Find the price tag inside this box.
        price_tag = card.select_one(settings["price"])
        # If the name or the price is missing, skip this box.
        if title_tag is None or price_tag is None:
            continue

        # Clean up the product name: join its words with single spaces.
        title = " ".join(title_tag.get_text().split())
        # Turn the price text into a number.
        price = get_number(price_tag.get_text())
        # If there is no price number, skip this box.
        if price is None:
            continue

        # Count the matching words and accessory words in this product name.
        found, accessories, total = count_matching_words(title, search_text)
        # If none of the search words are in the name, skip this product.
        if found == 0:
            continue

        # Score the product: 1 point for each matching word, minus 10 points for each accessory word.
        score = found - (10 * accessories)

        # Keep this product if it is the first one, or if its score is higher than the best so far.
        if best_score is None or score > best_score:
            # Remember this score as the best score.
            best_score = score
            # Remember this product's name, price, and whether it is an exact match.
            best = (title, price, found == total and accessories == 0)

    # Show how many products were on the page, for checking.
    print(f"    {len(cards)} products on page")
    # Give back the best product found (or None if nothing matched).
    return best


# This function prints the results as a table.
def show_table(search_text, results):
    # Find the shop with the lowest price.
    cheapest_shop = min(results, key=lambda shop: results[shop][1])
    # Print the heading with what the user searched for.
    print(f"\nBest matches for: {search_text}")
    # Print a line of dashes to separate the heading.
    print("-" * 90)
    # Go through the shops, sorted from the lowest price to the highest.
    for shop, (title, price, exact) in sorted(results.items(), key=lambda item: item[1][1]):
        # Add a marker to the cheapest shop.
        cheapest_mark = "  <-- cheapest" if shop == cheapest_shop else ""
        # Add "(closest match)" if the product name is not an exact match.
        closeness = "" if exact else " (closest match)"
        # Print one row: shop name, price, product name (first 55 letters), and the notes.
        print(f"{shop:<12} Rs {price:>8.2f}  {title[:55]}{closeness}{cheapest_mark}")
    # Print a closing line of dashes.
    print("-" * 90)


# ============================================================
# MAIN PROGRAM
# ============================================================

# This is the main function. It runs the program from start to finish.
def main():
    # Show the program title.
    print("Live Electronics Price Comparison")
    # Tell the user how to stop the program.
    print("Type any product name, or 'quit' to exit.")

    # Repeat forever, until the user types quit.
    while True:
        # Ask the user for a product name, and remove extra spaces at the start and end.
        search_text = input("\nSearch product: ").strip()
        # If the user pressed Enter without typing anything, ask again.
        if not search_text:
            continue
        # If the user typed quit, stop the loop.
        if search_text.lower() == "quit":
            break

        # Start an empty dictionary to store the result from each shop.
        results = {}
        # Go through each shop, one at a time.
        for shop_name, settings in SHOPS.items():
            # Tell the user which shop is being checked.
            print(f"Checking {shop_name}...")
            # Find the closest matching product on this shop.
            best = find_best_product(settings, search_text)
            # If nothing was found on this shop, show a message.
            if best is None:
                print(f"  {shop_name}: nothing similar found")
            # Otherwise, save the result for this shop.
            else:
                results[shop_name] = best

        # If at least one shop gave a result, show the table.
        if results:
            show_table(search_text, results)
        # If no shop gave a result, tell the user.
        else:
            print("No similar products found. Try a different name.")


# This line means: run main() only when this file is started directly (not imported).
if __name__ == "__main__":
    main()