import streamlit as st 
import pandas as pd
import plotly.express as px
import json
import os


st.set_page_config(page_title="Simple Finance App",page_icon = "📈",layout="wide")

category_file = "categories.json"

if "categories" not in st.session_state:
     st.session_state.categories = {
          "Uncategorized": []
     }
if os.path.exists(category_file):
    try:
        with open(category_file, "r") as f:
            st.session_state.categories = json.load(f)
    except json.JSONDecodeError:
        st.error("Error loading categories file. Using default categories.")

def save_categories():
    try:
        with open(category_file, "w") as f:
            json.dump(st.session_state.categories, f)
    except Exception as e:
        st.error(f"Error saving categories: {e}")
    return None
def load_transactions(file):
    try:
        df = pd.read_csv(file)
        # Convert Date to datetime if it exists
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        # Ensure Balance is numeric
        if 'Balance' in df.columns:
            df['Balance'] = pd.to_numeric(df['Balance'], errors='coerce')
        st.write(df)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None
def add_keyword_to_category(category, keyword):
     keyword = keyword.strip()
     if keyword and keyword not in st.session_state.categories[category]:
          st.session_state.categories[category].append(keyword)
          save_categories()
          st.success(f"Keyword '{keyword}' added to category '{category}'.")
          return True
     
     return False

def main():
    st.title("Simple Finance App")
    st.write("This is a simple finance app to visualize your transactions.")
    
    uploaded_file = st.file_uploader("Upload your transactions file", type=["csv"])

    balance_df = None
    imbalance_df = None

    if uploaded_file is not None:
        df = load_transactions(uploaded_file)

        if df is not None:
            st.session_state.balance_df = df[df['Balance'] > 0].copy()
            st.session_state.balance_df['Category'] = 'Uncategorized'  # Initialize Category column
            imbalance_df = df[df['Balance'] < 0].copy()

            tab1, tab2 = st.tabs(["Balance > 0", "Balance < 0"])
            
            with tab1:
                # Add category section
                new_category = st.text_input("New Category")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.success(f"Category '{new_category}' added.")
                        st.rerun()

                # Expenses section
                st.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.balance_df[["Date","Description","Category","Balance"]],
                    column_config={
                        "Date": st.column_config.TextColumn(
                            "Date",
                            help="Transaction date in YYYY-MM-DD format"
                        ),
                        "Description": st.column_config.TextColumn(
                            "Description",
                            help="Transaction description"
                        ),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            help="Select a category for this transaction", 
                            options=list(st.session_state.categories.keys())
                        ),
                        "Balance": st.column_config.NumberColumn(
                            "Balance",
                            help="Transaction amount",
                            format="%.2f"
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )

                save_button = st.button("Save Changes", type="primary")  # Fix type parameter
                if save_button:
                    for idx, row in edited_df.iterrows():
                        if row["Category"] == st.session_state.balance_df.at[idx, "Category"]:  # Fix variable name
                            continue
                        
                        details = row["Description"]  # Fix column name
                        new_category = row["Category"]  # Add this line
                        st.session_state.balance_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)

                    # Keep existing summary code
                    st.subheader("Expenses Summary") 
                    category_totals = st.session_state.balance_df.groupby("Category")["Balance"].sum().reset_index()
                    category_totals = category_totals.sort_values("Balance", ascending=False)

                    st.dataframe(
                         category_totals,
                         column_config={
                                "Category": st.column_config.TextColumn("Category"),
                                "Balance": st.column_config.NumberColumn("Balance")
                         },
                         use_container_width =True,
                         hide_index=True

                    )
                    fig = px.pie(
                         category_totals,
                         values="Balance",
                         names="Category",
                         title="Expenses by Category",
                         
                    )
                    st.plotly_chart(fig,use_container_width=True)
                    
            with tab2:
                st.subheader("Payments summary")
                total_payments = imbalance_df["Balance"].sum()
                st.metric("Total Payments", f"${total_payments:,.2f}")
                st.write(imbalance_df)
 
            
main()