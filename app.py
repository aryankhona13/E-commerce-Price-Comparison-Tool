# Import 'streamlit', the library that builds the web page.
import streamlit as st

# Import the shop settings and the search function from price_compare.py.
from price_compare import SHOPS, find_best_product

# Set the title that appears on the browser tab.
st.set_page_config(page_title="Electronics Price Comparison")

# Show a big heading at the top of the page.
st.title("Electronics Price Comparison")

# Show a text box where the user types the product name.
search_text = st.text_input("Product name", placeholder="e.g. lithium ion battery 18650")

# Show a button. The code inside the "if" runs only when the button is clicked.
if st.button("Compare prices"):
    # Remove extra spaces from the typed text.
    search_text = search_text.strip()

    # If nothing was typed, show a warning and stop here.
    if not search_text:
        st.warning("Please type a product name.")
    else:
        # Start an empty list to hold one row per shop.
        rows = []

        # Show a loading message while the shops are being checked.
        with st.spinner("Checking shops... this may take 10 to 20 seconds"):
            # Go through each shop, one at a time.
            for shop_name, settings in SHOPS.items():
                # Find the closest matching product on this shop.
                best = find_best_product(settings, search_text)

                # If the shop gave a result, add it as a row.
                if best is not None:
                    title, price, exact = best
                    rows.append({
                        "Shop": shop_name,
                        "Price (Rs)": price,
                        "Product": title,
                        "Exact match": "Yes" if exact else "No (closest)",
                    })

        # If at least one shop gave a result...
        if rows:
            # Sort the rows from the lowest price to the highest.
            rows.sort(key=lambda row: row["Price (Rs)"])
            # Show the results as a table on the web page.
            st.table(rows)
            # Show the cheapest shop in a green box.
            st.success(f"Cheapest: {rows[0]['Shop']} at Rs {rows[0]['Price (Rs)']:.2f}")
        else:
            # If no shop gave a result, show an error message.
            st.error("No similar products found. Try a different name.")