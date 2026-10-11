import calendar
import database as db
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(
    page_title="Personal Finance Manager",
    page_icon="💰",
    layout="wide"
)


st.markdown("""
<style>
/* Keep the app content within the screen */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    padding-left: clamp(1rem, 3vw, 3rem);
    padding-right: clamp(1rem, 3vw, 3rem);
}

/* Make charts and embedded content fit their containers */
.stPlotlyChart,
[data-testid="stDataFrame"],
[data-testid="stTable"] {
    max-width: 100%;
}

/* Improve form and button sizing */
.stButton button,
.stFormSubmitButton button {
    min-height: 2.5rem;
}

/* Adjust padding on narrow screens */
@media (max-width: 640px) {
    .block-container {
        padding-top: 1rem;
        padding-left: 0.75rem;
        padding-right: 0.75rem;
    }

    h1 {
        font-size: 1.6rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

db.create_table()

st.title("💰 Personal Finance Manager")
st.caption("Track your income, expenses, and savings in one place.")

# Initialize transaction data


pages = [
    "Dashboard",
    "Add Transaction",
    "View Transactions",
    "Monthly Reports",
    "Expense Prediction",
    "CSV Import / Export"
]

# Keep track of the selected page
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Sidebar navigation
def update_page():
    st.session_state.current_page = st.session_state.sidebar_page


def go_to_page(target_page):
    st.session_state.current_page = target_page
    st.session_state.sidebar_page = target_page

st.sidebar.selectbox(
    "Navigation",
    pages,
    key="sidebar_page",
    index=pages.index(st.session_state.current_page),
    on_change=update_page
)

page = st.session_state.current_page

# Navigation buttons


# Compact navigation icons in one row
current_index = pages.index(page)

left_space, nav_space = st.columns([8, 2])

with nav_space:
    back_col, home_col, next_col = st.columns(3, gap="small")

    with back_col:
        st.button(
            "←",
            key="nav_prev",
            help="Previous page",
            disabled=(current_index == 0),
            on_click=go_to_page,
            args=(pages[max(0, current_index - 1)],),
            use_container_width=True
        )

    with home_col:
        st.button(
            "⌂",
            key="nav_home",
            help="Go to Dashboard",
            disabled=(page == "Dashboard"),
            on_click=go_to_page,
            args=("Dashboard",),
            use_container_width=True
        )

    with next_col:
        st.button(
            "→",
            key="nav_next",
            help="Next page",
            disabled=(current_index == len(pages) - 1),
            on_click=go_to_page,
            args=(pages[min(len(pages) - 1, current_index + 1)],),
            use_container_width=True
        )



if page == "Add Transaction":
    st.subheader("➕ Add a Transaction")

    with st.form("transaction_form"):
        transaction_type = st.selectbox(
            "Transaction Type",
            ["Expense", "Income"]
        )

        if transaction_type == "Income":
            categories = [
                "Salary", "Business", "Investment",
                "Freelance", "Gift", "Other"
            ]
        else:
            categories = [
                "Food", "Entertainment", "Travel",
                "Shopping", "Bills", "Health",
                "Education", "Sports", "Fitness / Gym",
                "Rent", "Transport", "Subscriptions",
                "Gifts", "Donations", "Pet Care", "Other"
            ]

        category_choice = st.selectbox(
            "Category",
            categories
        )

        custom_category = ""

        if category_choice == "Other":
            custom_category = st.text_input(
                "Enter Custom Category",
                placeholder="e.g., Repairs, Gardening, Festivals"
            )

        amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            value=100.0,
            step=100.0
        )

        transaction_date = st.date_input(
            "Transaction Date"
        )

        description = st.text_input(
            "Description",
            placeholder="Enter transaction details"
        )

        submitted = st.form_submit_button(
            "Save Transaction"
        )

    if submitted:
        category = (
            custom_category.strip()
            if category_choice == "Other"
            else category_choice
        )

        if not category:
            st.error("Please enter a category.")
        else:
            db.add_transaction(
                transaction_date.isoformat(),
                category,
                transaction_type,
                float(amount),
                description.strip()
            )
            st.success("Transaction saved successfully!")

elif page == "Dashboard":
    df = db.get_transactions()

    if df.empty:
        st.info("No transactions yet. Add your first transaction!")
    else:
        income = df.loc[df["type"] == "Income", "amount"].sum()
        expenses = df.loc[df["type"] == "Expense", "amount"].sum()
        balance = income - expenses

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"₹{income:,.2f}")
        col2.metric("Total Expenses", f"₹{expenses:,.2f}")
        col3.metric("Available Balance", f"₹{balance:,.2f}")

        st.subheader("Expense Breakdown")
        expense_df = df[df["type"] == "Expense"]

        if not expense_df.empty:
            category_totals = expense_df.groupby(
                "category", as_index=False
            )["amount"].sum()

            fig = px.pie(
                category_totals,
                names="category",
                values="amount",
                title="Expenses by Category",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses recorded yet.")

        st.subheader("Recent Transactions")
        st.dataframe(
            df.drop(columns=["id"]),
            use_container_width=True,
            hide_index=True
        )


elif page == "View Transactions":
    st.subheader("📋 Manage Transactions")

    df = db.get_transactions()

    if df.empty:
        st.info("No transactions saved yet.")
    else:
        st.dataframe(
            df.drop(columns=["id"]),
            use_container_width=True,
            hide_index=True
        )

        st.divider()
        st.subheader("✏️ Edit or Delete a Transaction")

        transaction_options = {
            f"ID {int(row['id'])} | {row['date']} | "
            f"{row['type']} | ₹{row['amount']:.2f} | "
            f"{row['category']}": int(row["id"])
            for _, row in df.iterrows()
        }

        selected_label = st.selectbox(
            "Select a transaction",
            list(transaction_options.keys())
        )

        selected_id = transaction_options[selected_label]
        transaction = df.loc[df["id"] == selected_id].iloc[0]

        with st.form("edit_transaction_form"):
            edit_type = st.selectbox(
                "Transaction Type",
                ["Expense", "Income"],
                index=["Expense", "Income"].index(
                    transaction["type"]
                )
            )

            edit_category = st.text_input(
                "Category",
                value=str(transaction["category"])
            )

            edit_amount = st.number_input(
                "Amount (₹)",
                min_value=0.01,
                value=float(transaction["amount"]),
                step=100.0
            )

            edit_date = st.date_input(
                "Transaction Date",
                value=pd.to_datetime(
                    transaction["date"]
                ).date()
            )

            edit_description = st.text_input(
                "Description",
                value=str(transaction["description"] or "")
            )

            update_clicked = st.form_submit_button(
                "Save Changes"
            )

        if update_clicked:
            if not edit_category.strip():
                st.error("Please enter a category.")
            else:
                db.update_transaction(
                    selected_id,
                    edit_date.isoformat(),
                    edit_category.strip(),
                    edit_type,
                    float(edit_amount),
                    edit_description.strip()
                )
                st.success("Transaction updated successfully!")
                st.rerun()

        if st.button(
            "🗑️ Delete Selected Transaction",
            type="secondary"
        ):
            db.delete_transaction(selected_id)
            st.success("Transaction deleted.")
            st.rerun()


elif page == "Monthly Reports":
    st.subheader("Monthly Financial Reports")

    df = db.get_transactions()

    if df.empty:
        st.info("No transactions available. Add transactions to generate a report.")
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        if df.empty:
            st.info("No valid transaction dates are available.")
        else:
            years = sorted(
                set(df["date"].dt.year.tolist() + [date.today().year]),
                reverse=True
            )

            col1, col2 = st.columns(2)

            with col1:
                selected_month = st.selectbox(
                    "Select Month",
                    range(1, 13),
                    format_func=lambda month: calendar.month_name[month]
                )

            with col2:
                selected_year = st.selectbox("Select Year", years)

            monthly_df = df[
                (df["date"].dt.month == selected_month)
                & (df["date"].dt.year == selected_year)
            ].copy()

            if monthly_df.empty:
                st.info("No transactions found for the selected month.")
            else:
                income = monthly_df.loc[
                    monthly_df["type"] == "Income", "amount"
                ].sum()

                expenses = monthly_df.loc[
                    monthly_df["type"] == "Expense", "amount"
                ].sum()

                savings = income - expenses

                col1, col2, col3 = st.columns(3)
                col1.metric("Monthly Income", f"₹{income:,.2f}")
                col2.metric("Monthly Expenses", f"₹{expenses:,.2f}")
                col3.metric("Net Savings", f"₹{savings:,.2f}")

                st.subheader("Expense Breakdown")

                expense_df = monthly_df[
                    monthly_df["type"] == "Expense"
                ]

                if not expense_df.empty:
                    category_totals = (
                        expense_df.groupby("category", as_index=False)["amount"]
                        .sum()
                    )

                    fig = px.pie(
                        category_totals,
                        names="category",
                        values="amount",
                        title="Expenses by Category",
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No expenses recorded for this month.")

                st.subheader("Transactions for Selected Month")

                display_df = monthly_df.copy()
                display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
                display_df = display_df.drop(columns=["id"], errors="ignore")

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

                report_csv = display_df.to_csv(index=False)

                st.download_button(
                    "Download Monthly Report (CSV)",
                    data=report_csv,
                    file_name=f"finance_report_{selected_year}_{selected_month:02d}.csv",
                    mime="text/csv"
                )


elif page == "Expense Prediction":
    st.header("📈 Monthly Expense Prediction")
    st.write(
        "Estimate future spending using your previous monthly expenses."
    )

    # Get all transactions
    df = db.get_transactions()

    # Keep expense transactions only
    expense_df = df[
        df["type"].astype(str).str.lower() == "expense"
    ].copy()

    if expense_df.empty:
        st.info(
            "No expense records found. Add some expense transactions "
            "before using this feature."
        )

    else:
        # Clean and prepare the data
        expense_df["date"] = pd.to_datetime(
            expense_df["date"], errors="coerce"
        )
        expense_df["amount"] = pd.to_numeric(
            expense_df["amount"], errors="coerce"
        )

        expense_df = expense_df.dropna(
            subset=["date", "amount"]
        )
        expense_df = expense_df[expense_df["amount"] > 0]

        if expense_df.empty:
            st.warning(
                "No valid expense records are available for prediction."
            )

        else:
            # Calculate total expenses for each calendar month
            expense_df["month"] = (
                expense_df["date"].dt.to_period("M")
            )

            monthly_expenses = (
                expense_df.groupby("month")["amount"]
                .sum()
                .sort_index()
            )

            # Display available monthly history
            history_df = pd.DataFrame({
                "Month": monthly_expenses.index.astype(str),
                "Expenses": monthly_expenses.values
            })

            st.subheader("Monthly Expense History")

            st.plotly_chart(
                px.bar(
                    history_df,
                    x="Month",
                    y="Expenses",
                    title="Recorded Expenses by Month",
                    labels={
                        "Month": "Month",
                        "Expenses": "Total Expenses (₹)"
                    }
                ),
                use_container_width=True
            )

            st.dataframe(
                history_df,
                hide_index=True,
                use_container_width=True
            )

            # Check whether there are at least three
            # consecutive calendar months of expense data
            last_three = monthly_expenses.tail(3)

            enough_history = len(last_three) == 3

            if enough_history:
                enough_history = all(
                    last_three.index[i]
                    == last_three.index[i - 1] + 1
                    for i in range(1, 3)
                )

            if enough_history:
                # Three-month moving average
                predicted_amount = last_three.mean()

                next_month = monthly_expenses.index[-1] + 1

                st.subheader("🔮 Expense Forecast")

                st.metric(
                    label=(
                        "Estimated Expenses for "
                        + next_month.strftime("%B %Y")
                    ),
                    value=f"₹{predicted_amount:,.2f}"
                )

                st.caption(
                    "Method: average of the latest three consecutive "
                    "months with recorded expenses. This is an estimate, "
                    "not a guarantee."
                )

                # Compare the forecast with the latest recorded month
                latest_expense = monthly_expenses.iloc[-1]

                change = predicted_amount - latest_expense

                if latest_expense > 0:
                    change_percent = (
                        change / latest_expense
                    ) * 100

                    st.write(
                        f"Compared with the latest recorded month, "
                        f"the estimate is "
                        f"{abs(change_percent):.1f}% "
                        f"{'higher' if change > 0 else 'lower' if change < 0 else 'unchanged'}."
                    )

            else:
                st.info(
                    "Not enough history for a reliable prediction yet. "
                    "Record expenses across at least three consecutive "
                    "calendar months. Your available history is shown above."
                )

elif page == "CSV Import / Export":
    st.subheader("CSV Import and Export")

    df = db.get_transactions()

    st.markdown("### Export Transactions")

    if df.empty:
        st.info("No transactions available to export yet.")
    else:
        export_df = df.drop(columns=["id"], errors="ignore")

        st.download_button(
            "Download All Transactions (CSV)",
            data=export_df.to_csv(index=False),
            file_name="personal_finance_transactions.csv",
            mime="text/csv"
        )

    st.divider()

    st.markdown("### Download CSV Template")

    template_df = pd.DataFrame(columns=[
        "date", "category", "type", "amount", "description"
    ])

    st.download_button(
        "Download Import Template",
        data=template_df.to_csv(index=False),
        file_name="transactions_template.csv",
        mime="text/csv"
    )

    st.caption(
        "Required columns: date, category, type, amount, description. "
        "Use YYYY-MM-DD for dates and Income or Expense for transaction type."
    )

    st.divider()

    st.markdown("### Import Transactions from CSV")

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        key="transaction_csv"
    )

    if uploaded_file is not None:
        try:
            import_df = pd.read_csv(uploaded_file)

            required_columns = [
                "date", "category", "type", "amount", "description"
            ]

            missing_columns = [
                column for column in required_columns
                if column not in import_df.columns
            ]

            if missing_columns:
                st.error(
                    "Missing required columns: "
                    + ", ".join(missing_columns)
                )

            elif import_df.empty:
                st.warning("The CSV file contains no transaction rows.")

            else:
                import_df = import_df[required_columns].copy()

                import_df["date"] = pd.to_datetime(
                    import_df["date"], errors="coerce"
                )

                import_df["category"] = (
                    import_df["category"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

                import_df["type"] = (
                    import_df["type"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .str.title()
                )

                import_df["amount"] = pd.to_numeric(
                    import_df["amount"], errors="coerce"
                )

                import_df["description"] = (
                    import_df["description"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

                

                valid_rows = (
                    import_df["date"].notna()
                    & import_df["category"].ne("")
                    & import_df["type"].isin(["Income", "Expense"])
                    & import_df["amount"].notna()
                    & (import_df["amount"] > 0)
                )

                invalid_count = int((~valid_rows).sum())
                valid_df = import_df.loc[valid_rows].copy()

                # Create a consistent key for each transaction
                def transaction_key(row):
                    transaction_date = pd.to_datetime(
                        row["date"], errors="coerce"
                    )

                    if pd.isna(transaction_date):
                        return None

                    return (
                        transaction_date.strftime("%Y-%m-%d"),
                        str(row["category"]).strip(),
                        str(row["type"]).strip().title(),
                        round(float(row["amount"]), 2),
                        str(row["description"]).strip()
                    )

                # Find transactions already in the database
                existing_df = db.get_transactions()
                existing_keys = set()

                for _, row in existing_df.iterrows():
                    key = transaction_key(row)
                    if key is not None:
                        existing_keys.add(key)

                # Filter out duplicates in the database and CSV
                seen_keys = set()
                new_indices = []
                duplicate_count = 0

                for index, row in valid_df.iterrows():
                    key = transaction_key(row)

                    if key in existing_keys or key in seen_keys:
                        duplicate_count += 1
                    else:
                        seen_keys.add(key)
                        new_indices.append(index)

                new_df = valid_df.loc[new_indices].copy()

                # Preview the new transactions
                st.write("Preview of new transactions:")

                preview_df = new_df.copy()
                preview_df["date"] = preview_df["date"].dt.strftime(
                    "%Y-%m-%d"
                )

                st.dataframe(
                    preview_df,
                    use_container_width=True,
                    hide_index=True
                )

                if invalid_count:
                    st.warning(
                        f"{invalid_count} invalid row(s) will be skipped."
                    )

                if duplicate_count:
                    st.warning(
                        f"{duplicate_count} duplicate transaction(s) "
                        "detected. They will be skipped."
                    )

                if st.button("Import New Transactions"):
                    if new_df.empty:
                        st.info("No new transactions to import.")
                    else:
                        for _, row in new_df.iterrows():
                            db.add_transaction(
                                row["date"].date().isoformat(),
                                row["category"],
                                row["type"],
                                float(row["amount"]),
                                row["description"]
                            )

                        st.success(
                            f"Successfully imported "
                            f"{len(new_df)} new transaction(s)."
                        )
                        st.rerun()

        except (
            ValueError,
            pd.errors.ParserError,
            UnicodeDecodeError
        ) as error:
            st.error(f"Could not read the CSV file: {error}")
